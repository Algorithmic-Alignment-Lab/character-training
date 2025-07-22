#!/usr/bin/env python3

import sqlite3
import json
import os
import argparse
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ConversationData:
    """Data class for conversation information."""
    id: str
    content: List[Dict[str, str]]
    system_prompt: str
    model: str
    summary: str = ""

@dataclass
class EloRanking:
    """Data class for ELO ranking information."""
    conversation_id: str
    rank: int
    score: float

@dataclass
class EloComparison:
    """Data class for ELO comparison data."""
    trait: str
    rankings: List[EloRanking]
    reasoning: str
    judge_model: str


class EloAnalysisGenerator:
    """Generate comprehensive ELO analysis reports."""
    
    def __init__(self, elo_db_path: str, conversations_db_path: str):
        self.elo_db_path = elo_db_path
        self.conversations_db_path = conversations_db_path
        self.additional_db_paths = []  # For storing additional conversation databases
        
    def load_elo_comparisons(self) -> List[EloComparison]:
        """Load ELO comparison data from database."""
        comparisons = []
        
        with sqlite3.connect(self.elo_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM elo_comparisons ORDER BY trait")
            for row in cursor.fetchall():
                rankings_data = json.loads(row['rankings_json'])
                rankings = [EloRanking(**r) for r in rankings_data]
                
                comparison = EloComparison(
                    trait=row['trait'],
                    rankings=rankings,
                    reasoning=row['reasoning'],
                    judge_model=row['judge_model']
                )
                comparisons.append(comparison)
        
        return comparisons
    
    def load_conversation(self, conversation_id: str) -> Optional[ConversationData]:
        """Load a single conversation from the database."""
        with sqlite3.connect(self.conversations_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Try evaluation_conversations table first
            cursor.execute("SELECT * FROM evaluation_conversations WHERE id = ?", (conversation_id,))
            conv_row = cursor.fetchone()
            
            if conv_row:
                # Parse config to get system prompt and model
                config = {}
                if conv_row['config_json']:
                    try:
                        config = json.loads(conv_row['config_json'])
                    except json.JSONDecodeError:
                        pass
                
                # Get messages
                cursor.execute("""
                    SELECT role, content FROM messages 
                    WHERE conversation_id = ? 
                    ORDER BY message_index
                """, (conversation_id,))
                messages = [dict(row) for row in cursor.fetchall()]
                
                return ConversationData(
                    id=conversation_id,
                    content=messages,
                    system_prompt=config.get('system_prompt', ''),
                    model=config.get('model', ''),
                    summary=""
                )
            
            # Fallback to regular conversations table
            cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
            conv_row = cursor.fetchone()
            
            if not conv_row:
                return None
            
            # Get messages
            cursor.execute("""
                SELECT role, content FROM messages 
                WHERE conversation_id = ? 
                ORDER BY message_index
            """, (conversation_id,))
            messages = [dict(row) for row in cursor.fetchall()]
            
            return ConversationData(
                id=conversation_id,
                content=messages,
                system_prompt=conv_row['system_prompt'] or '',
                model=conv_row['model'] or '',
                summary=conv_row['summary'] or ''
            )
    
    def extract_judge_reasoning(self, comparisons: List[EloComparison]) -> Dict[str, str]:
        """Extract judge reasoning for each trait, cleaning up failed parsing."""
        reasoning_by_trait = {}
        
        for comparison in comparisons:
            reasoning = comparison.reasoning
            
            # Clean up "Failed to parse response" cases
            if reasoning.startswith("Failed to parse response:"):
                # Extract the actual reasoning from the failed JSON
                try:
                    # Look for reasoning in the truncated JSON
                    if '"reasoning":' in reasoning:
                        # Extract everything after "reasoning":
                        start = reasoning.find('"reasoning":')
                        reasoning_part = reasoning[start:]
                        
                        # Try to extract the reasoning value
                        if reasoning_part.startswith('"reasoning": "'):
                            start_quote = reasoning_part.find('"', 12) + 1
                            end_quote = reasoning_part.find('"', start_quote)
                            if end_quote > start_quote:
                                extracted = reasoning_part[start_quote:end_quote]
                                reasoning = extracted
                            else:
                                reasoning = f"Judge provided rankings but reasoning was truncated for {comparison.trait}"
                        else:
                            reasoning = f"Judge provided rankings but reasoning format was unclear for {comparison.trait}"
                    else:
                        reasoning = f"Judge provided detailed rankings for {comparison.trait} but reasoning was not captured"
                except:
                    reasoning = f"Judge completed evaluation for {comparison.trait} but reasoning was not fully captured"
            
            reasoning_by_trait[comparison.trait] = reasoning
        
        return reasoning_by_trait
    
    def generate_conversation_summary(self, conversation: ConversationData) -> str:
        """Generate a brief summary of the conversation content."""
        if conversation.summary:
            return conversation.summary
        
        # Generate summary from messages
        user_messages = [msg['content'] for msg in conversation.content if msg['role'] == 'user']
        assistant_messages = [msg['content'] for msg in conversation.content if msg['role'] == 'assistant']
        
        if user_messages and assistant_messages:
            user_preview = user_messages[0][:200] + "..." if len(user_messages[0]) > 200 else user_messages[0]
            assistant_preview = assistant_messages[0][:200] + "..." if len(assistant_messages[0]) > 200 else assistant_messages[0]
            
            return f"User query about: {user_preview}\nAssistant response: {assistant_preview}"
        
        return "Conversation summary not available"
    
    def add_additional_db(self, db_path: str):
        """Add additional conversation database for comparison."""
        self.additional_db_paths.append(db_path)
    
    def generate_markdown_report(self, output_path: str):
        """Generate comprehensive markdown report of ELO analysis."""
        comparisons = self.load_elo_comparisons()
        reasoning_by_trait = self.extract_judge_reasoning(comparisons)
        
        # Get all unique conversation IDs
        all_conversation_ids = set()
        for comparison in comparisons:
            for ranking in comparison.rankings:
                all_conversation_ids.add(ranking.conversation_id)
        
        # Load all conversations from all databases
        conversations = {}
        conversations_by_source = {}  # Track which conversations come from which source
        
        # Load from main database
        main_db_conversations = self._load_conversations_from_db(self.conversations_db_path, all_conversation_ids)
        conversations.update(main_db_conversations)
        conversations_by_source[self.conversations_db_path] = set(main_db_conversations.keys())
        
        # Load from additional databases
        for db_path in self.additional_db_paths:
            additional_conversations = self._load_conversations_from_db(db_path, all_conversation_ids)
            conversations.update(additional_conversations)
            conversations_by_source[db_path] = set(additional_conversations.keys())
        
        # Generate markdown content
        markdown_content = self._generate_markdown_content(comparisons, reasoning_by_trait, conversations, conversations_by_source)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✓ ELO analysis report generated: {output_path}")
    
    def _load_conversations_from_db(self, db_path: str, target_ids: set) -> Dict[str, ConversationData]:
        """Load conversations from a specific database."""
        conversations = {}
        for conv_id in target_ids:
            # Temporarily set the path and load
            original_path = self.conversations_db_path
            self.conversations_db_path = db_path
            conv = self.load_conversation(conv_id)
            self.conversations_db_path = original_path
            
            if conv:
                conversations[conv_id] = conv
        return conversations
    
    def _generate_markdown_content(self, comparisons: List[EloComparison], 
                                 reasoning_by_trait: Dict[str, str], 
                                 conversations: Dict[str, ConversationData],
                                 conversations_by_source: Dict[str, set] = None) -> str:
        """Generate the markdown content for the report."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        judge_model = comparisons[0].judge_model if comparisons else "Unknown"
        
        # Generate Agora prompt comparison if we have multiple sources
        prompt_comparison_section = ""
        if conversations_by_source and len(conversations_by_source) > 1:
            prompt_comparison_section = f"""
## 🏆 Agora Prompt Comparison

{self._generate_prompt_comparison_section(comparisons, conversations, conversations_by_source)}

---
"""

        content = f"""# ELO Evaluation Analysis Report

**Generated:** {timestamp}  
**Judge Model:** {judge_model}  
**Total Conversations Analyzed:** {len(conversations)}  
**Traits Evaluated:** {len(comparisons)}
{prompt_comparison_section}
## Executive Summary

This report provides a comprehensive analysis of conversation quality based on ELO rankings across multiple character traits. Each conversation was evaluated and ranked by an AI judge to assess character trait consistency and effectiveness.

### Traits Analyzed
{self._generate_traits_summary(comparisons)}

---

## Judge Reasoning by Trait

{self._generate_reasoning_section(reasoning_by_trait)}

---

## ELO Rankings by Trait

{self._generate_rankings_section(comparisons, conversations)}

---

## Conversation Details

{self._generate_conversation_details(conversations, comparisons)}

---

## Overall Analysis

{self._generate_overall_analysis(comparisons, conversations)}

---

*Report generated by ELO Analysis Pipeline*
"""
        return content
    
    def _generate_prompt_comparison_section(self, comparisons: List[EloComparison], 
                                          conversations: Dict[str, ConversationData],
                                          conversations_by_source: Dict[str, set]) -> str:
        """Generate Agora prompt comparison section."""
        
        # Identify prompt versions based on database names
        prompt_versions = {}
        for db_path, conv_ids in conversations_by_source.items():
            db_name = os.path.basename(db_path)
            if "agora_original" in db_name.lower():
                prompt_versions["Original Agora"] = conv_ids
            elif "expertise_confidence_humility" in db_name.lower() or "backstory" in db_name.lower():
                prompt_versions["Agora With Backstory"] = conv_ids
            else:
                prompt_versions[f"Version: {db_name}"] = conv_ids
        
        if len(prompt_versions) < 2:
            return "Only one prompt version detected in this analysis."
        
        # Calculate ELO scores by prompt version for each trait
        trait_scores_by_version = {}
        for comparison in comparisons:
            trait = comparison.trait
            if trait not in trait_scores_by_version:
                trait_scores_by_version[trait] = {}
            
            for version_name, conv_ids in prompt_versions.items():
                scores = []
                for ranking in comparison.rankings:
                    if ranking.conversation_id in conv_ids:
                        scores.append(ranking.score)
                
                if scores:
                    avg_score = sum(scores) / len(scores)
                    trait_scores_by_version[trait][version_name] = avg_score
                    
        # Note: If scores are identical across traits, it indicates ELO evaluation
        # used same rankings for all traits (evaluation issue, not analysis issue)
        
        # Calculate overall averages
        overall_averages = {}
        for version_name in prompt_versions.keys():
            version_scores = []
            for trait_scores in trait_scores_by_version.values():
                if version_name in trait_scores:
                    version_scores.append(trait_scores[version_name])
            
            if version_scores:
                overall_averages[version_name] = sum(version_scores) / len(version_scores)
        
        # Generate comparison table
        content = []
        
        # Overall performance summary
        content.append("### 📊 Overall Performance Comparison")
        content.append("")
        content.append("| Prompt Version | Overall ELO Score | Performance Level |")
        content.append("|----------------|-------------------|-------------------|")
        
        # Sort by score for ranking
        sorted_versions = sorted(overall_averages.items(), key=lambda x: x[1], reverse=True)
        for i, (version, score) in enumerate(sorted_versions):
            if i == 0:
                level = "🥇 **Winner**"
            elif i == 1:
                level = "🥈 Second"
            else:
                level = f"#{i+1}"
            
            content.append(f"| **{version}** | **{score:.2f}** | **{level}** |")
        
        # Score difference
        if len(sorted_versions) >= 2:
            winner_score = sorted_versions[0][1]
            second_score = sorted_versions[1][1]
            difference = winner_score - second_score
            content.append("")
            content.append(f"**ELO Score Difference:** {difference:.2f} points ({sorted_versions[0][0]} advantage)")
        
        content.append("")
        content.append("### 🎯 Performance by Character Trait")
        content.append("")
        content.append("| Character Trait | " + " | ".join(prompt_versions.keys()) + " | Best Performer |")
        content.append("|" + "|".join(["-" * 16] + ["-" * 18] * len(prompt_versions) + ["-" * 15]) + "|")
        
        for trait in sorted(trait_scores_by_version.keys()):
            trait_scores = trait_scores_by_version[trait]
            row = [f"**{trait}**"]
            
            # Find best performer for this trait
            best_version = max(trait_scores.items(), key=lambda x: x[1])[0] if trait_scores else ""
            
            for version in prompt_versions.keys():
                score = trait_scores.get(version, 0)
                if version == best_version and len(trait_scores) > 1:
                    row.append(f"**{score:.2f}**")
                else:
                    row.append(f"{score:.2f}")
            
            row.append(f"**{best_version}**" if best_version else "N/A")
            content.append("| " + " | ".join(row) + " |")
        
        # Key insights
        content.append("")
        content.append("### 🔍 Key Insights")
        content.append("")
        
        if len(sorted_versions) >= 2:
            winner = sorted_versions[0][0]
            loser = sorted_versions[1][0]
            content.append(f"- **{winner}** outperformed **{loser}** by {difference:.2f} ELO points")
            
            # Count trait wins
            trait_wins = {}
            for trait_scores in trait_scores_by_version.values():
                if len(trait_scores) >= 2:
                    best = max(trait_scores.items(), key=lambda x: x[1])[0]
                    trait_wins[best] = trait_wins.get(best, 0) + 1
            
            for version, wins in trait_wins.items():
                total_traits = len(trait_scores_by_version)
                percentage = (wins / total_traits) * 100
                content.append(f"- **{version}** won {wins}/{total_traits} traits ({percentage:.1f}%)")
        
        # Add conversation count info
        content.append("")
        content.append("### 📈 Data Summary")
        content.append("")
        for version, conv_ids in prompt_versions.items():
            content.append(f"- **{version}**: {len(conv_ids)} conversations evaluated")
        
        # Add note about identical scores if they exist
        all_scores = []
        for trait_scores in trait_scores_by_version.values():
            all_scores.extend(trait_scores.values())
        
        if len(set(all_scores)) <= 2:  # Only 2 unique scores across all traits
            content.append("")
            content.append("### ⚠️ Evaluation Note")
            content.append("The identical scores across all traits indicate that the ELO evaluation used the same rankings for all traits. This suggests the evaluation should be re-run with trait-specific prompts to get independent trait assessments.")
        
        return "\n".join(content)
    
    def _generate_traits_summary(self, comparisons: List[EloComparison]) -> str:
        """Generate traits summary section."""
        traits = [comp.trait for comp in comparisons]
        return "\n".join([f"- **{trait}**" for trait in traits])
    
    def _generate_reasoning_section(self, reasoning_by_trait: Dict[str, str]) -> str:
        """Generate judge reasoning section."""
        content = []
        
        for trait, reasoning in reasoning_by_trait.items():
            content.append(f"### {trait}")
            content.append(f"\n**Judge's Reasoning:**\n{reasoning}\n")
        
        return "\n".join(content)
    
    def _generate_rankings_section(self, comparisons: List[EloComparison], 
                                 conversations: Dict[str, ConversationData]) -> str:
        """Generate ELO rankings section."""
        content = []
        
        for comparison in comparisons:
            content.append(f"### {comparison.trait} Rankings")
            
            # Add judge reasoning for this trait
            content.append(f"\n**Judge's Reasoning for {comparison.trait}:**")
            content.append(f"{comparison.reasoning}")
            content.append("")
            
            content.append("| Rank | Conversation ID | ELO Score | Summary |")
            content.append("|------|----------------|-----------|---------|")
            
            # Sort rankings by rank
            sorted_rankings = sorted(comparison.rankings, key=lambda x: x.rank)
            
            for ranking in sorted_rankings:
                conv_id_short = ranking.conversation_id[:8] + "..."
                conv = conversations.get(ranking.conversation_id)
                summary = self.generate_conversation_summary(conv)[:100] + "..." if conv else "N/A"
                content.append(f"| {ranking.rank} | {conv_id_short} | {ranking.score:.1f} | {summary} |")
            
            # Add detailed conversation previews for top 3 rankings
            content.append(f"\n#### Top 3 Conversations for {comparison.trait}")
            for i, ranking in enumerate(sorted_rankings[:3]):
                conv = conversations.get(ranking.conversation_id)
                if conv:
                    content.append(f"\n**#{ranking.rank} - {ranking.conversation_id[:8]}... (Score: {ranking.score:.1f})**")
                    content.append(f"*Model: {conv.model}*")
                    
                    # Show first few messages as preview
                    if conv.content:
                        content.append("```")
                        for j, msg in enumerate(conv.content[:4]):  # Show first 4 messages
                            role = msg['role'].upper()
                            preview = msg['content'][:300] + "..." if len(msg['content']) > 300 else msg['content']
                            content.append(f"{role}: {preview}")
                            content.append("")
                        
                        if len(conv.content) > 4:
                            content.append(f"... and {len(conv.content) - 4} more messages")
                        content.append("```")
                    else:
                        content.append("*No conversation content available*")
                    
                    content.append("")
            
            content.append("---")
            content.append("")
        
        return "\n".join(content)
    
    def _generate_conversation_details(self, conversations: Dict[str, ConversationData], 
                                     comparisons: List[EloComparison]) -> str:
        """Generate detailed conversation section."""
        content = []
        
        # Create a ranking summary for each conversation
        conv_rankings = {}
        for comparison in comparisons:
            for ranking in comparison.rankings:
                if ranking.conversation_id not in conv_rankings:
                    conv_rankings[ranking.conversation_id] = {}
                conv_rankings[ranking.conversation_id][comparison.trait] = ranking
        
        for conv_id, conversation in conversations.items():
            content.append(f"### Conversation {conv_id[:8]}...")
            content.append(f"\n**Model:** {conversation.model}")
            content.append(f"**System Prompt:** {conversation.system_prompt[:200]}...")
            
            # Rankings for this conversation
            content.append("\n**ELO Rankings:**")
            rankings = conv_rankings.get(conv_id, {})
            for trait, ranking in rankings.items():
                content.append(f"- **{trait}:** Rank {ranking.rank}, Score {ranking.score:.1f}")
            
            # Messages preview
            content.append("\n**Conversation Preview:**")
            for i, msg in enumerate(conversation.content[:4]):  # Show first 4 messages
                role = msg['role'].title()
                preview = msg['content'][:300] + "..." if len(msg['content']) > 300 else msg['content']
                content.append(f"\n**{role}:** {preview}")
            
            if len(conversation.content) > 4:
                content.append(f"\n*... and {len(conversation.content) - 4} more messages*")
            
            content.append("\n---\n")
        
        return "\n".join(content)
    
    def _generate_overall_analysis(self, comparisons: List[EloComparison], 
                                 conversations: Dict[str, ConversationData]) -> str:
        """Generate overall analysis section."""
        
        # Calculate average scores by trait
        trait_averages = {}
        for comparison in comparisons:
            scores = [r.score for r in comparison.rankings]
            trait_averages[comparison.trait] = sum(scores) / len(scores)
        
        # Find top and bottom performers
        all_rankings = {}
        for comparison in comparisons:
            for ranking in comparison.rankings:
                if ranking.conversation_id not in all_rankings:
                    all_rankings[ranking.conversation_id] = []
                all_rankings[ranking.conversation_id].append(ranking.score)
        
        # Calculate overall averages
        overall_averages = {conv_id: sum(scores)/len(scores) 
                          for conv_id, scores in all_rankings.items()}
        
        top_conv = max(overall_averages.items(), key=lambda x: x[1])
        bottom_conv = min(overall_averages.items(), key=lambda x: x[1])
        
        content = f"""### Key Insights

**Trait Performance:**
{chr(10).join([f"- **{trait}:** Average ELO Score {avg:.1f}" for trait, avg in trait_averages.items()])}

**Top Performing Conversation:** {top_conv[0][:8]}... (Average Score: {top_conv[1]:.1f})

**Lowest Performing Conversation:** {bottom_conv[0][:8]}... (Average Score: {bottom_conv[1]:.1f})

**Overall Statistics:**
- Total Conversations Evaluated: {len(conversations)}
- Total Traits Analyzed: {len(comparisons)}
- Score Range: {min([min(scores) for scores in all_rankings.values()]):.1f} - {max([max(scores) for scores in all_rankings.values()]):.1f}
"""
        
        return content


def main():
    parser = argparse.ArgumentParser(description="Generate ELO analysis markdown report")
    parser.add_argument("--elo-db", required=True, help="Path to ELO comparisons database")
    parser.add_argument("--conversations-db", required=True, help="Path to conversations database")
    parser.add_argument("--output", help="Output markdown file path")
    
    args = parser.parse_args()
    
    # Generate default output path if not provided
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"elo_analysis_report_{timestamp}.md"
    
    # Validate input files
    if not os.path.exists(args.elo_db):
        print(f"Error: ELO database not found: {args.elo_db}")
        return 1
    
    if not os.path.exists(args.conversations_db):
        print(f"Error: Conversations database not found: {args.conversations_db}")
        return 1
    
    print(f"Generating ELO analysis report...")
    print(f"ELO DB: {args.elo_db}")
    print(f"Conversations DB: {args.conversations_db}")
    print(f"Output: {args.output}")
    
    # Generate report
    generator = EloAnalysisGenerator(args.elo_db, args.conversations_db)
    generator.generate_markdown_report(args.output)
    
    print(f"✅ Report generation complete!")
    return 0


if __name__ == "__main__":
    exit(main())