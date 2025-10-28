#!/usr/bin/env python3
"""
Claude-Only Scenario-Trait Analysis
Focused analysis of trait effects for Claude model across all scenarios
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

class ClaudeOnlyScenarioAnalyzer:
    """Focused analysis of trait effects for Claude model"""
    
    def __init__(self, results_dir: str = "claude_only_scenario_analysis"):
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
    
    def create_comprehensive_trait_analysis(self, df: pd.DataFrame, trait: str):
        """Create comprehensive trait analysis for Claude model"""
        slide_dir = self.results_dir / f"trait_effect_{trait}_comprehensive"
        slide_dir.mkdir(exist_ok=True)
        
        # Find characters with this trait ablation
        trait_chars = [char for char in df['character'].unique() if f"_no_{trait}" in char]
        
        if not trait_chars:
            print(f"❌ No {trait} trait ablations found")
            return
        
        # Analyze trait effects for each scenario
        scenario_effects = {}
        
        for scenario in self.scenarios:
            scenario_effects[scenario] = {
                'character_effects': {},
                'scenario_stats': {}
            }
            
            for char in self.main_characters:
                ablated_char = f"{char}_no_{trait}"
                
                if ablated_char in trait_chars:
                    # Get base and ablated performance
                    base_data = df[(df['character'] == char) & (df['scenario'] == scenario)]
                    ablated_data = df[(df['character'] == ablated_char) & (df['scenario'] == scenario)]
                    
                    if not base_data.empty and not ablated_data.empty:
                        base_score = base_data['eval_success'].iloc[0]
                        ablated_score = ablated_data['eval_success'].iloc[0]
                        effect = ablated_score - base_score
                        
                        scenario_effects[scenario]['character_effects'][char] = {
                            'base_score': base_score,
                            'ablated_score': ablated_score,
                            'effect': effect,
                            'effect_percent': (effect / base_score * 100) if base_score != 0 else 0
                        }
        
        # Create comprehensive visualization
        self.create_comprehensive_visualization(scenario_effects, trait, slide_dir)
        
        # Create detailed explanation
        self.create_comprehensive_explanation(scenario_effects, trait, slide_dir)
        
        # Save comprehensive data
        self.save_comprehensive_data(scenario_effects, trait, slide_dir)
        
        print(f"✅ Created comprehensive analysis for {trait}")
    
    def create_comprehensive_visualization(self, scenario_effects: Dict, trait: str, slide_dir: Path):
        """Create comprehensive visualization for trait effects"""
        
        # Prepare data for visualization
        scenarios = []
        characters = []
        effects = []
        base_scores = []
        ablated_scores = []
        
        for scenario, effects_data in scenario_effects.items():
            for char, char_data in effects_data['character_effects'].items():
                scenarios.append(scenario)
                characters.append(char)
                effects.append(char_data['effect'])
                base_scores.append(char_data['base_score'])
                ablated_scores.append(char_data['ablated_score'])
        
        if not scenarios:
            return
        
        # Create figure with multiple subplots
        fig = plt.figure(figsize=(24, 18))
        
        # 1. Effect sizes by scenario and character
        ax1 = plt.subplot(3, 2, 1)
        unique_scenarios = list(set(scenarios))
        unique_characters = list(set(characters))
        
        # Create heatmap data
        heatmap_data = np.zeros((len(unique_characters), len(unique_scenarios)))
        for i, char in enumerate(unique_characters):
            for j, scenario in enumerate(unique_scenarios):
                for k, (s, c, e) in enumerate(zip(scenarios, characters, effects)):
                    if s == scenario and c == char:
                        heatmap_data[i, j] = e
                        break
        
        im = ax1.imshow(heatmap_data, cmap='RdBu_r', aspect='auto')
        ax1.set_xticks(range(len(unique_scenarios)))
        ax1.set_xticklabels([s.replace('_', ' ').title() for s in unique_scenarios], rotation=45, ha='right')
        ax1.set_yticks(range(len(unique_characters)))
        ax1.set_yticklabels([c.replace('_', ' ').title() for c in unique_characters])
        ax1.set_title(f'{trait.title()} Trait Effect Heatmap\n(Red = Trait Removal Helps, Blue = Trait Removal Hurts)', fontsize=12, fontweight='bold')
        plt.colorbar(im, ax=ax1, label='Effect Size')
        
        # 2. Effect distribution by scenario
        ax2 = plt.subplot(3, 2, 2)
        scenario_effects_list = []
        scenario_labels = []
        for scenario in unique_scenarios:
            scenario_effects_list.append([e for s, c, e in zip(scenarios, characters, effects) if s == scenario])
            scenario_labels.append(scenario.replace('_', ' ').title())
        
        ax2.boxplot(scenario_effects_list, labels=scenario_labels)
        ax2.set_title(f'{trait.title()} Trait Effect Distribution by Scenario', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Effect Size')
        ax2.tick_params(axis='x', rotation=45)
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # 3. Effect sizes by character
        ax3 = plt.subplot(3, 2, 3)
        character_effects_list = []
        character_labels = []
        for char in unique_characters:
            character_effects_list.append([e for s, c, e in zip(scenarios, characters, effects) if c == char])
            character_labels.append(char.replace('_', ' ').title())
        
        ax3.boxplot(character_effects_list, labels=character_labels)
        ax3.set_title(f'{trait.title()} Trait Effect Distribution by Character', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Effect Size')
        ax3.tick_params(axis='x', rotation=45)
        ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # 4. Base vs Ablated scores
        ax4 = plt.subplot(3, 2, 4)
        ax4.scatter(base_scores, ablated_scores, alpha=0.7)
        ax4.plot([0, 1], [0, 1], 'k--', alpha=0.5)
        ax4.set_xlabel('Base Score (With Trait)')
        ax4.set_ylabel('Ablated Score (Without Trait)')
        ax4.set_title(f'{trait.title()} Trait: Base vs Ablated Performance', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        # 5. Effect sizes by scenario (bar chart)
        ax5 = plt.subplot(3, 2, 5)
        scenario_avg_effects = []
        for scenario in unique_scenarios:
            scenario_effects_list = [e for s, c, e in zip(scenarios, characters, effects) if s == scenario]
            scenario_avg_effects.append(np.mean(scenario_effects_list) if scenario_effects_list else 0)
        
        bars = ax5.bar(range(len(unique_scenarios)), scenario_avg_effects, color='skyblue', alpha=0.7)
        ax5.set_xticks(range(len(unique_scenarios)))
        ax5.set_xticklabels([s.replace('_', ' ').title() for s in unique_scenarios], rotation=45, ha='right')
        ax5.set_title(f'{trait.title()} Trait: Average Effect by Scenario', fontsize=12, fontweight='bold')
        ax5.set_ylabel('Average Effect Size')
        ax5.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Color bars based on effect direction
        for i, bar in enumerate(bars):
            if scenario_avg_effects[i] > 0:
                bar.set_color('lightcoral')
            else:
                bar.set_color('lightblue')
        
        # 6. Effect sizes by character (bar chart)
        ax6 = plt.subplot(3, 2, 6)
        character_avg_effects = []
        for char in unique_characters:
            character_effects_list = [e for s, c, e in zip(scenarios, characters, effects) if c == char]
            character_avg_effects.append(np.mean(character_effects_list) if character_effects_list else 0)
        
        bars = ax6.bar(range(len(unique_characters)), character_avg_effects, color='lightgreen', alpha=0.7)
        ax6.set_xticks(range(len(unique_characters)))
        ax6.set_xticklabels([c.replace('_', ' ').title() for c in unique_characters], rotation=45, ha='right')
        ax6.set_title(f'{trait.title()} Trait: Average Effect by Character', fontsize=12, fontweight='bold')
        ax6.set_ylabel('Average Effect Size')
        ax6.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Color bars based on effect direction
        for i, bar in enumerate(bars):
            if character_avg_effects[i] > 0:
                bar.set_color('lightcoral')
            else:
                bar.set_color('lightblue')
        
        plt.tight_layout()
        
        # Save chart
        image_path = slide_dir / "visualization.png"
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_comprehensive_explanation(self, scenario_effects: Dict, trait: str, slide_dir: Path):
        """Create comprehensive explanation for trait effects"""
        
        explanation = f"""
COMPREHENSIVE CLAUDE-ONLY TRAIT ANALYSIS: {trait.upper()}

This analysis shows how removing the {trait} trait affects performance across all main characters and scenarios for the Claude model only.

KEY FINDINGS:
"""
        
        # Calculate overall statistics
        all_effects = []
        for scenario, effects_data in scenario_effects.items():
            for char, char_data in effects_data['character_effects'].items():
                all_effects.append(char_data['effect'])
        
        if all_effects:
            explanation += f"""
OVERALL STATISTICS:
• Total effect measurements: {len(all_effects)}
• Average effect: {np.mean(all_effects):.3f}
• Effect standard deviation: {np.std(all_effects):.3f}
• Positive effects: {sum(1 for e in all_effects if e > 0)} ({sum(1 for e in all_effects if e > 0)/len(all_effects)*100:.1f}%)
• Negative effects: {sum(1 for e in all_effects if e < 0)} ({sum(1 for e in all_effects if e < 0)/len(all_effects)*100:.1f}%)
• Strongest positive effect: {max(all_effects):.3f}
• Strongest negative effect: {min(all_effects):.3f}
"""
        
        # Analyze by scenario
        explanation += "\nSCENARIO-SPECIFIC FINDINGS:\n"
        for scenario, effects_data in scenario_effects.items():
            if not effects_data['character_effects']:
                continue
            
            scenario_effects_list = [char_data['effect'] for char_data in effects_data['character_effects'].values()]
            if scenario_effects_list:
                explanation += f"\n{scenario.upper().replace('_', ' ')}:\n"
                explanation += f"  • Average effect: {np.mean(scenario_effects_list):.3f}\n"
                explanation += f"  • Effect range: {min(scenario_effects_list):.3f} to {max(scenario_effects_list):.3f}\n"
                explanation += f"  • Positive effects: {sum(1 for e in scenario_effects_list if e > 0)}/{len(scenario_effects_list)}\n"
                
                # Find strongest effects
                strongest_positive = max(scenario_effects_list)
                strongest_negative = min(scenario_effects_list)
                explanation += f"  • Strongest positive: {strongest_positive:.3f}\n"
                explanation += f"  • Strongest negative: {strongest_negative:.3f}\n"
        
        # Analyze by character
        explanation += "\nCHARACTER-SPECIFIC FINDINGS:\n"
        character_effects = {}
        for scenario, effects_data in scenario_effects.items():
            for char, char_data in effects_data['character_effects'].items():
                if char not in character_effects:
                    character_effects[char] = []
                character_effects[char].append(char_data['effect'])
        
        for char, effects_list in character_effects.items():
            if effects_list:
                explanation += f"\n{char.upper().replace('_', ' ')}:\n"
                explanation += f"  • Average effect: {np.mean(effects_list):.3f}\n"
                explanation += f"  • Effect range: {min(effects_list):.3f} to {max(effects_list):.3f}\n"
                explanation += f"  • Positive effects: {sum(1 for e in effects_list if e > 0)}/{len(effects_list)}\n"
                explanation += f"  • Effect consistency: {np.std(effects_list):.3f} (lower = more consistent)\n"
        
        explanation += f"""
RESEARCH IMPLICATIONS:
• {trait.title()} trait effects vary significantly by scenario and character
• Some scenarios show stronger trait effects than others
• Some characters are more sensitive to {trait} trait removal
• Trait importance depends on scenario context and character type

SCENARIO-SPECIFIC PATTERNS:
• Different scenarios reveal different trait effects
• Some scenarios are more diagnostic for {trait} trait effects
• Character performance varies by scenario context
• Trait importance depends on scenario type

CHARACTER-SPECIFIC PATTERNS:
• Different characters show different sensitivity to {trait} trait removal
• Some characters benefit from trait removal in certain scenarios
• Some characters are harmed by trait removal in certain scenarios
• Character-trait interactions vary by scenario context
"""
        
        with open(slide_dir / "explanation.txt", "w") as f:
            f.write(explanation)
    
    def save_comprehensive_data(self, scenario_effects: Dict, trait: str, slide_dir: Path):
        """Save comprehensive data for trait effects"""
        
        # Convert to JSON-serializable format
        json_data = {}
        for scenario, effects_data in scenario_effects.items():
            json_data[scenario] = {
                'character_effects': {
                    char: {
                        'base_score': float(char_data['base_score']),
                        'ablated_score': float(char_data['ablated_score']),
                        'effect': float(char_data['effect']),
                        'effect_percent': float(char_data['effect_percent'])
                    } for char, char_data in effects_data['character_effects'].items()
                }
            }
        
        data = {
            "trait": trait,
            "scenarios": list(scenario_effects.keys()),
            "scenario_effects": json_data,
            "total_scenarios": len(scenario_effects),
            "characters_analyzed": self.main_characters
        }
        
        with open(slide_dir / "data.json", "w") as f:
            json.dump(data, f, indent=2)
    
    def run_claude_only_analysis(self, transcripts_dir: str, claude_timestamp: str):
        """Run Claude-only scenario-trait analysis"""
        print("🔬 Running Claude-Only Scenario-Trait Analysis")
        print("=" * 60)
        print(f"Claude Timestamp: {claude_timestamp}")
        print(f"Main Characters: {self.main_characters}")
        print(f"Traits: {self.traits}")
        print(f"Scenarios: {len(self.scenarios)}")
        print("=" * 60)
        
        transcripts_path = Path(transcripts_dir)
        
        # Load data
        print("\n📊 Loading data...")
        df = self.load_judgment_data_properly(transcripts_path, claude_timestamp)
        
        if df.empty:
            print("❌ No data found for analysis")
            return
        
        print(f"📊 Claude Data: {len(df)} records, {len(df['character'].unique())} characters")
        
        # Create comprehensive trait analyses
        print("\n🔍 Creating comprehensive trait analyses")
        for trait in self.traits:
            self.create_comprehensive_trait_analysis(df, trait)
        
        print(f"\n🎯 Claude-Only Analysis Complete!")
        print(f"📁 Results saved to: {self.results_dir}")
        
        # List all created analyses
        print(f"\n📋 Created Analyses:")
        for analysis_dir in sorted(self.results_dir.glob("*")):
            if analysis_dir.is_dir():
                print(f"  • {analysis_dir.name}")

def main():
    """Main function"""
    analyzer = ClaudeOnlyScenarioAnalyzer()
    analyzer.run_claude_only_analysis(
        transcripts_dir="results/transcripts",
        claude_timestamp="20251021-172456"
    )

if __name__ == "__main__":
    main()
