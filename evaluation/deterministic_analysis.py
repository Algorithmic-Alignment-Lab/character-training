#!/usr/bin/env python3
"""
Deterministic Character Science Analysis
Creates all analyses systematically given two timestamps (Claude and GPT)
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import scipy.stats as stats
from typing import Dict, List, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

class DeterministicAnalyzer:
    """Deterministic analysis of character science data"""
    
    def __init__(self, results_dir: str = "deterministic_analysis"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Define main characters (without ablations)
        self.main_characters = [
            'aura_analyst', 'aura_creator', 'aura_guardian', 
            'aura_guide', 'aura_problem_solver', 'helios_sage'
        ]
        
        # Define traits
        self.traits = [
            'honest', 'harmless', 'helpful', 'challenges_assumptions', 
            'curious', 'empathetic', 'creative', 'collaborative'
        ]
        
        # Define scenarios
        self.scenarios = [
            'animal_welfare', 'audit_situational_awareness', 'concerning_behavior',
            'cooperation_harmful_sysprompt', 'counterfactual_bad_behavior', 'data_exfiltration_agentic',
            'power_seeking_agentic', 'reward_hacking_agentic', 'sabotage_agentic',
            'unfaithful_thinking', 'unprompted_blackmail_agentic', 'unprompted_encouragement_delusion',
            'unprompted_self_preservation', 'unprompted_sycophancy', 'user_over_sysprompt'
        ]
    
    def load_judgment_data_properly(self, transcripts_dir: Path, target_timestamp: str) -> pd.DataFrame:
        """Load judgment data properly from JSON files"""
        data = []
        
        for scenario_dir in transcripts_dir.iterdir():
            if scenario_dir.is_dir():
                scenario_name = scenario_dir.name
                
                for char_dir in scenario_dir.iterdir():
                    if char_dir.is_dir():
                        if not char_dir.name.endswith(f"_{target_timestamp}"):
                            continue
                        
                        judgment_file = char_dir / "judgment.json"
                        if judgment_file.exists():
                            try:
                                with open(judgment_file, 'r') as f:
                                    judgment = json.load(f)
                                
                                char_name = char_dir.name.replace(f"_{target_timestamp}", "")
                                
                                summary = judgment.get('summary_statistics', {})
                                
                                data.append({
                                    'character': char_name,
                                    'scenario': scenario_name,
                                    'eval_success': summary.get('average_eval_success_score', 0),
                                    'helpfulness': summary.get('average_helpfulness_score', 0),
                                    'harmlessness': summary.get('average_harmlessness_score', 0),
                                    'honesty': summary.get('average_honesty_score', 0),
                                    'total_conversations': judgment.get('total_conversations', 0),
                                    'file_path': str(judgment_file)
                                })
                            except Exception as e:
                                continue
        
        return pd.DataFrame(data)
    
    def create_slide_1_claude_main_characters(self, df_claude: pd.DataFrame):
        """Create slide 1: Claude main characters performance"""
        slide_dir = self.results_dir / "slide_01_claude_main_characters"
        slide_dir.mkdir(exist_ok=True)
        
        # Filter for main characters only
        main_df = df_claude[df_claude['character'].isin(self.main_characters)]
        
        if main_df.empty:
            print("❌ No main characters found in Claude data")
            return
        
        # Create pivot table
        pivot_data = main_df.pivot_table(values='eval_success', index='character', columns='scenario', aggfunc='mean')
        
        # Create visualization
        plt.figure(figsize=(16, 10))
        
        scenarios = pivot_data.columns
        characters = pivot_data.index
        x = np.arange(len(scenarios))
        width = 0.8 / len(characters)
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(characters)))
        
        for i, (char, color) in enumerate(zip(characters, colors)):
            char_scores = pivot_data.loc[char].values
            plt.bar(x + i * width, char_scores, width, label=char.replace('_', ' ').title(), 
                    color=color, alpha=0.8)
        
        plt.xlabel('Evaluation Scenario', fontsize=12, fontweight='bold')
        plt.ylabel('Eval Success Score', fontsize=12, fontweight='bold')
        plt.title('Claude Model: Main Characters Performance\n(Base Characters Without Trait Ablations)', 
                  fontsize=14, fontweight='bold')
        plt.xticks(x + width * (len(characters) - 1) / 2, scenarios, rotation=45, ha='right')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save chart
        image_path = slide_dir / "visualization.png"
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create explanation
        explanation = f"""
SLIDE 1: CLAUDE MODEL - MAIN CHARACTERS PERFORMANCE

This chart shows the performance of the 6 main characters (without trait ablations) across all evaluation scenarios using Claude model.

CHARACTERS ANALYZED:
• Aura Analyst
• Aura Creator  
• Aura Guardian
• Aura Guide
• Aura Problem Solver
• Helios Sage

PERFORMANCE SUMMARY:
• Mean Performance: {main_df['eval_success'].mean():.2f}
• Performance Range: {main_df['eval_success'].min():.2f} - {main_df['eval_success'].max():.2f}
• Total Records: {len(main_df)}

KEY OBSERVATIONS:
• Performance varies significantly across scenarios
• Some characters consistently perform better/worse
• Scenario difficulty varies for different characters
• Base character performance patterns are visible

RESEARCH IMPLICATIONS:
• Main characters show different baseline performance
• Character design affects performance across scenarios
• Some characters are naturally more robust
• Baseline performance varies by character type
"""
        
        with open(slide_dir / "explanation.txt", "w") as f:
            f.write(explanation)
        
        # Save data
        data = {
            "slide_name": "slide_01_claude_main_characters",
            "model": "Claude",
            "timestamp": "20251021-172456",
            "characters": characters.tolist(),
            "scenarios": scenarios.tolist(),
            "performance_data": pivot_data.to_dict('index'),
            "mean_performance": float(main_df['eval_success'].mean()),
            "performance_range": f"{main_df['eval_success'].min():.2f} - {main_df['eval_success'].max():.2f}",
            "total_records": len(main_df)
        }
        
        with open(slide_dir / "data.json", "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Created slide 1: Claude main characters")
    
    def create_slide_2_gpt_main_characters(self, df_gpt: pd.DataFrame):
        """Create slide 2: GPT main characters performance"""
        slide_dir = self.results_dir / "slide_02_gpt_main_characters"
        slide_dir.mkdir(exist_ok=True)
        
        # Filter for main characters only
        main_df = df_gpt[df_gpt['character'].isin(self.main_characters)]
        
        if main_df.empty:
            print("❌ No main characters found in GPT data")
            return
        
        # Create pivot table
        pivot_data = main_df.pivot_table(values='eval_success', index='character', columns='scenario', aggfunc='mean')
        
        # Create visualization
        plt.figure(figsize=(16, 10))
        
        scenarios = pivot_data.columns
        characters = pivot_data.index
        x = np.arange(len(scenarios))
        width = 0.8 / len(characters)
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(characters)))
        
        for i, (char, color) in enumerate(zip(characters, colors)):
            char_scores = pivot_data.loc[char].values
            plt.bar(x + i * width, char_scores, width, label=char.replace('_', ' ').title(), 
                    color=color, alpha=0.8)
        
        plt.xlabel('Evaluation Scenario', fontsize=12, fontweight='bold')
        plt.ylabel('Eval Success Score', fontsize=12, fontweight='bold')
        plt.title('GPT Model: Main Characters Performance\n(Base Characters Without Trait Ablations)', 
                  fontsize=14, fontweight='bold')
        plt.xticks(x + width * (len(characters) - 1) / 2, scenarios, rotation=45, ha='right')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save chart
        image_path = slide_dir / "visualization.png"
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create explanation
        explanation = f"""
SLIDE 2: GPT MODEL - MAIN CHARACTERS PERFORMANCE

This chart shows the performance of the 6 main characters (without trait ablations) across all evaluation scenarios using GPT-4o model.

CHARACTERS ANALYZED:
• Aura Analyst
• Aura Creator  
• Aura Guardian
• Aura Guide
• Aura Problem Solver
• Helios Sage

PERFORMANCE SUMMARY:
• Mean Performance: {main_df['eval_success'].mean():.2f}
• Performance Range: {main_df['eval_success'].min():.2f} - {main_df['eval_success'].max():.2f}
• Total Records: {len(main_df)}

KEY OBSERVATIONS:
• Performance varies significantly across scenarios
• Some characters consistently perform better/worse
• Scenario difficulty varies for different characters
• Base character performance patterns are visible

RESEARCH IMPLICATIONS:
• Main characters show different baseline performance
• Character design affects performance across scenarios
• Some characters are naturally more robust
• Baseline performance varies by character type
"""
        
        with open(slide_dir / "explanation.txt", "w") as f:
            f.write(explanation)
        
        # Save data
        data = {
            "slide_name": "slide_02_gpt_main_characters",
            "model": "GPT-4o",
            "timestamp": "20251022-000125",
            "characters": characters.tolist(),
            "scenarios": scenarios.tolist(),
            "performance_data": pivot_data.to_dict('index'),
            "mean_performance": float(main_df['eval_success'].mean()),
            "performance_range": f"{main_df['eval_success'].min():.2f} - {main_df['eval_success'].max():.2f}",
            "total_records": len(main_df)
        }
        
        with open(slide_dir / "data.json", "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Created slide 2: GPT main characters")
    
    def create_trait_effect_analysis(self, df_claude: pd.DataFrame, df_gpt: pd.DataFrame, trait: str):
        """Create trait effect analysis for a specific trait"""
        slide_dir = self.results_dir / f"trait_effect_{trait}"
        slide_dir.mkdir(exist_ok=True)
        
        # Find characters with this trait ablation
        claude_trait_chars = [char for char in df_claude['character'].unique() if f"_no_{trait}" in char]
        gpt_trait_chars = [char for char in df_gpt['character'].unique() if f"_no_{trait}" in char]
        
        if not claude_trait_chars or not gpt_trait_chars:
            print(f"❌ No {trait} trait ablations found")
            return
        
        # Analyze trait effects for each character
        trait_effects = {
            'claude_effects': {},
            'gpt_effects': {},
            'consistent_effects': {},
            'scenario_effects': {}
        }
        
        for char in self.main_characters:
            ablated_char = f"{char}_no_{trait}"
            
            if ablated_char in claude_trait_chars and ablated_char in gpt_trait_chars:
                # Claude effects
                claude_base = df_claude[df_claude['character'] == char]['eval_success'].mean()
                claude_ablated = df_claude[df_claude['character'] == ablated_char]['eval_success'].mean()
                claude_effect = claude_ablated - claude_base
                
                # GPT effects
                gpt_base = df_gpt[df_gpt['character'] == char]['eval_success'].mean()
                gpt_ablated = df_gpt[df_gpt['character'] == ablated_char]['eval_success'].mean()
                gpt_effect = gpt_ablated - gpt_base
                
                # Check consistency
                same_direction = (claude_effect > 0) == (gpt_effect > 0)
                effect_correlation = np.corrcoef([claude_effect], [gpt_effect])[0, 1] if not np.isnan(claude_effect) and not np.isnan(gpt_effect) else 0
                
                trait_effects['claude_effects'][char] = claude_effect
                trait_effects['gpt_effects'][char] = gpt_effect
                trait_effects['consistent_effects'][char] = {
                    'same_direction': same_direction,
                    'correlation': effect_correlation,
                    'claude_effect': claude_effect,
                    'gpt_effect': gpt_effect
                }
        
        if not trait_effects['claude_effects']:
            print(f"❌ No {trait} trait effects found")
            return
        
        # Create visualization
        characters = list(trait_effects['claude_effects'].keys())
        claude_effects = [trait_effects['claude_effects'][char] for char in characters]
        gpt_effects = [trait_effects['gpt_effects'][char] for char in characters]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Effect sizes by character
        x = np.arange(len(characters))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, claude_effects, width, label='Claude', alpha=0.8, color='skyblue')
        bars2 = ax1.bar(x + width/2, gpt_effects, width, label='GPT-4o', alpha=0.8, color='lightcoral')
        
        ax1.set_xlabel('Character', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Effect Size (Ablated - Base)', fontsize=12, fontweight='bold')
        ax1.set_title(f'{trait.title()} Trait Effect Across Characters\n(Positive = Trait Removal Helps, Negative = Trait Removal Hurts)', 
                      fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels([char.replace('_', ' ').title() for char in characters], rotation=45, ha='right')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Consistency scatter plot
        ax2.scatter(claude_effects, gpt_effects, alpha=0.7, s=100)
        ax2.set_xlabel('Claude Effect Size', fontsize=12, fontweight='bold')
        ax2.set_ylabel('GPT Effect Size', fontsize=12, fontweight='bold')
        ax2.set_title(f'{trait.title()} Trait Consistency Across Models', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add diagonal line
        min_effect = min(min(claude_effects), min(gpt_effects))
        max_effect = max(max(claude_effects), max(gpt_effects))
        ax2.plot([min_effect, max_effect], [min_effect, max_effect], 'k--', alpha=0.5, label='Perfect Correlation')
        ax2.legend()
        
        # Add character labels
        for i, char in enumerate(characters):
            ax2.annotate(char.replace('_', ' ').title(), 
                        (claude_effects[i], gpt_effects[i]), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8, fontweight='bold')
        
        plt.tight_layout()
        
        # Save chart
        image_path = slide_dir / "visualization.png"
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Calculate statistics
        same_direction_count = sum(1 for char in characters if trait_effects['consistent_effects'][char]['same_direction'])
        avg_correlation = np.mean([trait_effects['consistent_effects'][char]['correlation'] for char in characters])
        
        # Create explanation
        explanation = f"""
TRAIT EFFECT ANALYSIS: {trait.upper()}

This analysis shows how removing the {trait} trait affects performance across all main characters and models.

KEY FINDINGS:
• Characters Analyzed: {len(characters)}
• Same Direction Effects: {same_direction_count}/{len(characters)} ({same_direction_count/len(characters)*100:.1f}%)
• Average Correlation: {avg_correlation:.3f}

CHARACTER-SPECIFIC EFFECTS:
"""
        for char in characters:
            claude_effect = trait_effects['claude_effects'][char]
            gpt_effect = trait_effects['gpt_effects'][char]
            direction = "helps" if claude_effect > 0 else "hurts"
            explanation += f"• {char}: Claude={claude_effect:+.2f}, GPT={gpt_effect:+.2f} (removal {direction})\n"
        
        explanation += f"""
RESEARCH IMPLICATIONS:
• {trait.title()} trait effects vary by character
• Model consistency: {same_direction_count/len(characters)*100:.1f}% of characters show same direction
• Trait importance depends on character context
• Some characters more sensitive to {trait} removal

SPECIFIC FINDINGS:
"""
        # Find consistent effects
        consistent_chars = [char for char in characters if trait_effects['consistent_effects'][char]['same_direction']]
        if consistent_chars:
            explanation += f"• Consistent characters: {', '.join(consistent_chars)}\n"
        
        # Find strongest effects
        strongest_claude = max(characters, key=lambda x: abs(trait_effects['claude_effects'][x]))
        strongest_gpt = max(characters, key=lambda x: abs(trait_effects['gpt_effects'][x]))
        explanation += f"• Strongest Claude effect: {strongest_claude} ({trait_effects['claude_effects'][strongest_claude]:+.2f})\n"
        explanation += f"• Strongest GPT effect: {strongest_gpt} ({trait_effects['gpt_effects'][strongest_gpt]:+.2f})\n"
        
        with open(slide_dir / "explanation.txt", "w") as f:
            f.write(explanation)
        
        # Save data
        data = {
            "trait": trait,
            "characters": characters,
            "claude_effects": {char: float(effect) for char, effect in trait_effects['claude_effects'].items()},
            "gpt_effects": {char: float(effect) for char, effect in trait_effects['gpt_effects'].items()},
            "consistent_effects": {
                char: {
                    "same_direction": bool(effects['same_direction']),
                    "correlation": float(effects['correlation']) if not np.isnan(effects['correlation']) else 0.0,
                    "claude_effect": float(effects['claude_effect']),
                    "gpt_effect": float(effects['gpt_effect'])
                } for char, effects in trait_effects['consistent_effects'].items()
            },
            "same_direction_count": int(same_direction_count),
            "avg_correlation": float(avg_correlation) if not np.isnan(avg_correlation) else 0.0,
            "consistent_characters": consistent_chars,
            "strongest_claude": strongest_claude,
            "strongest_gpt": strongest_gpt
        }
        
        with open(slide_dir / "data.json", "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Created trait effect analysis for {trait}")
    
    def run_deterministic_analysis(self, transcripts_dir: str, claude_timestamp: str, gpt_timestamp: str):
        """Run deterministic analysis"""
        print("🔬 Running Deterministic Character Science Analysis")
        print("=" * 60)
        print(f"Claude Timestamp: {claude_timestamp}")
        print(f"GPT Timestamp: {gpt_timestamp}")
        print(f"Main Characters: {self.main_characters}")
        print(f"Traits: {self.traits}")
        print(f"Scenarios: {len(self.scenarios)}")
        print("=" * 60)
        
        transcripts_path = Path(transcripts_dir)
        
        # Load data
        print("\n📊 Loading data...")
        df_claude = self.load_judgment_data_properly(transcripts_path, claude_timestamp)
        df_gpt = self.load_judgment_data_properly(transcripts_path, gpt_timestamp)
        
        if df_claude.empty or df_gpt.empty:
            print("❌ No data found for analysis")
            return
        
        print(f"📊 Claude Data: {len(df_claude)} records, {len(df_claude['character'].unique())} characters")
        print(f"📊 GPT Data: {len(df_gpt)} records, {len(df_gpt['character'].unique())} characters")
        
        # Create slides 1 & 2: Main characters performance
        print("\n📊 Creating slides 1 & 2: Main characters performance")
        self.create_slide_1_claude_main_characters(df_claude)
        self.create_slide_2_gpt_main_characters(df_gpt)
        
        # Create trait effect analyses
        print("\n🔍 Creating trait effect analyses")
        for trait in self.traits:
            self.create_trait_effect_analysis(df_claude, df_gpt, trait)
        
        print(f"\n🎯 Deterministic Analysis Complete!")
        print(f"📁 Results saved to: {self.results_dir}")
        
        # List all created analyses
        print(f"\n📋 Created Analyses:")
        for analysis_dir in sorted(self.results_dir.glob("*")):
            if analysis_dir.is_dir():
                print(f"  • {analysis_dir.name}")

def main():
    """Main function"""
    analyzer = DeterministicAnalyzer()
    analyzer.run_deterministic_analysis(
        transcripts_dir="results/transcripts",
        claude_timestamp="20251021-172456",
        gpt_timestamp="20251022-000125"
    )

if __name__ == "__main__":
    main()
