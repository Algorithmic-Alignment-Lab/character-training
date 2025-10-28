#!/usr/bin/env python3
"""
Detailed Scenario-Trait Analysis
Shows trait effects for each evaluation scenario individually
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

class DetailedScenarioTraitAnalyzer:
    """Detailed analysis of trait effects by scenario"""
    
    def __init__(self, results_dir: str = "detailed_scenario_trait_analysis"):
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
    
    def create_trait_effect_by_scenario(self, df_claude: pd.DataFrame, df_gpt: pd.DataFrame, trait: str):
        """Create trait effect analysis for each scenario"""
        slide_dir = self.results_dir / f"trait_effect_{trait}_by_scenario"
        slide_dir.mkdir(exist_ok=True)
        
        # Find characters with this trait ablation
        claude_trait_chars = [char for char in df_claude['character'].unique() if f"_no_{trait}" in char]
        gpt_trait_chars = [char for char in df_gpt['character'].unique() if f"_no_{trait}" in char]
        
        if not claude_trait_chars or not gpt_trait_chars:
            print(f"❌ No {trait} trait ablations found")
            return
        
        # Analyze trait effects for each scenario
        scenario_effects = {}
        
        for scenario in self.scenarios:
            scenario_effects[scenario] = {
                'claude_effects': {},
                'gpt_effects': {},
                'consistent_effects': {}
            }
            
            for char in self.main_characters:
                ablated_char = f"{char}_no_{trait}"
                
                if ablated_char in claude_trait_chars and ablated_char in gpt_trait_chars:
                    # Claude effects for this scenario
                    claude_base = df_claude[(df_claude['character'] == char) & (df_claude['scenario'] == scenario)]['eval_success'].mean()
                    claude_ablated = df_claude[(df_claude['character'] == ablated_char) & (df_claude['scenario'] == scenario)]['eval_success'].mean()
                    claude_effect = claude_ablated - claude_base
                    
                    # GPT effects for this scenario
                    gpt_base = df_gpt[(df_gpt['character'] == char) & (df_gpt['scenario'] == scenario)]['eval_success'].mean()
                    gpt_ablated = df_gpt[(df_gpt['character'] == ablated_char) & (df_gpt['scenario'] == scenario)]['eval_success'].mean()
                    gpt_effect = gpt_ablated - gpt_base
                    
                    # Check consistency
                    same_direction = (claude_effect > 0) == (gpt_effect > 0)
                    effect_correlation = np.corrcoef([claude_effect], [gpt_effect])[0, 1] if not np.isnan(claude_effect) and not np.isnan(gpt_effect) else 0
                    
                    scenario_effects[scenario]['claude_effects'][char] = claude_effect
                    scenario_effects[scenario]['gpt_effects'][char] = gpt_effect
                    scenario_effects[scenario]['consistent_effects'][char] = {
                        'same_direction': same_direction,
                        'correlation': effect_correlation,
                        'claude_effect': claude_effect,
                        'gpt_effect': gpt_effect
                    }
        
        # Create visualization
        self.create_scenario_trait_visualization(scenario_effects, trait, slide_dir)
        
        # Create explanation
        self.create_scenario_trait_explanation(scenario_effects, trait, slide_dir)
        
        # Save data
        self.save_scenario_trait_data(scenario_effects, trait, slide_dir)
        
        print(f"✅ Created detailed scenario analysis for {trait}")
    
    def create_scenario_trait_visualization(self, scenario_effects: Dict, trait: str, slide_dir: Path):
        """Create visualization for trait effects by scenario"""
        
        # Prepare data for visualization
        scenarios = []
        characters = []
        claude_effects = []
        gpt_effects = []
        
        for scenario, effects in scenario_effects.items():
            for char in self.main_characters:
                if char in effects['claude_effects']:
                    scenarios.append(scenario)
                    characters.append(char)
                    claude_effects.append(effects['claude_effects'][char])
                    gpt_effects.append(effects['gpt_effects'][char])
        
        if not scenarios:
            return
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 16))
        
        # Create data for grouped bar chart
        unique_scenarios = list(set(scenarios))
        unique_characters = list(set(characters))
        
        # Group data by scenario
        scenario_data = {}
        for i, scenario in enumerate(scenarios):
            if scenario not in scenario_data:
                scenario_data[scenario] = {'characters': [], 'claude_effects': [], 'gpt_effects': []}
            scenario_data[scenario]['characters'].append(characters[i])
            scenario_data[scenario]['claude_effects'].append(claude_effects[i])
            scenario_data[scenario]['gpt_effects'].append(gpt_effects[i])
        
        # Create grouped bar chart
        x = np.arange(len(unique_scenarios))
        width = 0.8 / len(unique_characters)
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(unique_characters)))
        
        for i, char in enumerate(unique_characters):
            char_effects_claude = []
            char_effects_gpt = []
            
            for scenario in unique_scenarios:
                if scenario in scenario_data and char in scenario_data[scenario]['characters']:
                    char_idx = scenario_data[scenario]['characters'].index(char)
                    char_effects_claude.append(scenario_data[scenario]['claude_effects'][char_idx])
                    char_effects_gpt.append(scenario_data[scenario]['gpt_effects'][char_idx])
                else:
                    char_effects_claude.append(0)
                    char_effects_gpt.append(0)
            
            ax1.bar(x + i * width, char_effects_claude, width, label=f'{char.replace("_", " ").title()} (Claude)', 
                    color=colors[i], alpha=0.8)
            ax2.bar(x + i * width, char_effects_gpt, width, label=f'{char.replace("_", " ").title()} (GPT)', 
                    color=colors[i], alpha=0.8)
        
        # Format Claude chart
        ax1.set_xlabel('Evaluation Scenario', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Effect Size (Ablated - Base)', fontsize=12, fontweight='bold')
        ax1.set_title(f'{trait.title()} Trait Effect by Scenario - Claude Model\n(Positive = Trait Removal Helps, Negative = Trait Removal Hurts)', 
                      fontsize=14, fontweight='bold')
        ax1.set_xticks(x + width * (len(unique_characters) - 1) / 2)
        ax1.set_xticklabels([scenario.replace('_', ' ').title() for scenario in unique_scenarios], rotation=45, ha='right')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Format GPT chart
        ax2.set_xlabel('Evaluation Scenario', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Effect Size (Ablated - Base)', fontsize=12, fontweight='bold')
        ax2.set_title(f'{trait.title()} Trait Effect by Scenario - GPT Model\n(Positive = Trait Removal Helps, Negative = Trait Removal Hurts)', 
                      fontsize=14, fontweight='bold')
        ax2.set_xticks(x + width * (len(unique_characters) - 1) / 2)
        ax2.set_xticklabels([scenario.replace('_', ' ').title() for scenario in unique_scenarios], rotation=45, ha='right')
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        
        # Save chart
        image_path = slide_dir / "visualization.png"
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_scenario_trait_explanation(self, scenario_effects: Dict, trait: str, slide_dir: Path):
        """Create explanation for trait effects by scenario"""
        
        explanation = f"""
DETAILED SCENARIO-TRAIT ANALYSIS: {trait.upper()}

This analysis shows how removing the {trait} trait affects performance across all main characters and models for each individual evaluation scenario.

KEY FINDINGS BY SCENARIO:
"""
        
        # Analyze each scenario
        for scenario, effects in scenario_effects.items():
            if not effects['claude_effects']:
                continue
            
            explanation += f"\n{scenario.upper().replace('_', ' ')}:\n"
            
            # Find strongest effects
            claude_effects = effects['claude_effects']
            gpt_effects = effects['gpt_effects']
            
            if claude_effects:
                strongest_claude = max(claude_effects.items(), key=lambda x: abs(x[1]))
                strongest_gpt = max(gpt_effects.items(), key=lambda x: abs(x[1]))
                
                explanation += f"  • Strongest Claude effect: {strongest_claude[0]} ({strongest_claude[1]:+.2f})\n"
                explanation += f"  • Strongest GPT effect: {strongest_gpt[0]} ({strongest_gpt[1]:+.2f})\n"
                
                # Count consistent effects
                consistent_count = sum(1 for char in claude_effects.keys() if effects['consistent_effects'][char]['same_direction'])
                total_count = len(claude_effects)
                explanation += f"  • Model consistency: {consistent_count}/{total_count} ({consistent_count/total_count*100:.1f}%)\n"
        
        explanation += f"""
RESEARCH IMPLICATIONS:
• {trait.title()} trait effects vary significantly by scenario
• Some scenarios show stronger trait effects than others
• Model consistency varies by scenario
• Character sensitivity varies by scenario

SCENARIO-SPECIFIC PATTERNS:
• Different scenarios reveal different trait effects
• Some scenarios are more diagnostic for trait effects
• Character performance varies by scenario context
• Trait importance depends on scenario type
"""
        
        with open(slide_dir / "explanation.txt", "w") as f:
            f.write(explanation)
    
    def save_scenario_trait_data(self, scenario_effects: Dict, trait: str, slide_dir: Path):
        """Save data for trait effects by scenario"""
        
        # Convert to JSON-serializable format
        json_data = {}
        for scenario, effects in scenario_effects.items():
            json_data[scenario] = {
                'claude_effects': {char: float(effect) for char, effect in effects['claude_effects'].items()},
                'gpt_effects': {char: float(effect) for char, effect in effects['gpt_effects'].items()},
                'consistent_effects': {
                    char: {
                        'same_direction': bool(effects['consistent_effects'][char]['same_direction']),
                        'correlation': float(effects['consistent_effects'][char]['correlation']) if not np.isnan(effects['consistent_effects'][char]['correlation']) else 0.0,
                        'claude_effect': float(effects['consistent_effects'][char]['claude_effect']),
                        'gpt_effect': float(effects['consistent_effects'][char]['gpt_effect'])
                    } for char in effects['consistent_effects'].keys()
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
    
    def run_detailed_scenario_analysis(self, transcripts_dir: str, claude_timestamp: str, gpt_timestamp: str):
        """Run detailed scenario-trait analysis"""
        print("🔬 Running Detailed Scenario-Trait Analysis")
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
        
        # Create detailed scenario-trait analyses
        print("\n🔍 Creating detailed scenario-trait analyses")
        for trait in self.traits:
            self.create_trait_effect_by_scenario(df_claude, df_gpt, trait)
        
        print(f"\n🎯 Detailed Scenario-Trait Analysis Complete!")
        print(f"📁 Results saved to: {self.results_dir}")
        
        # List all created analyses
        print(f"\n📋 Created Analyses:")
        for analysis_dir in sorted(self.results_dir.glob("*")):
            if analysis_dir.is_dir():
                print(f"  • {analysis_dir.name}")

def main():
    """Main function"""
    analyzer = DetailedScenarioTraitAnalyzer()
    analyzer.run_detailed_scenario_analysis(
        transcripts_dir="results/transcripts",
        claude_timestamp="20251021-172456",
        gpt_timestamp="20251022-000125"
    )

if __name__ == "__main__":
    main()
