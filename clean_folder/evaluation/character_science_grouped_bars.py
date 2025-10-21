#!/usr/bin/env python3
"""
Character Science Visualization - Grouped Bar Charts
Creates grouped bar charts showing all characters across all 12 evaluation scenarios.
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import argparse
from typing import Dict, List, Any
import warnings
warnings.filterwarnings('ignore')

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class CharacterScienceGroupedBars:
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.transcripts_dir = self.results_dir / "transcripts"
        
        # All 6 characters with display names
        self.characters = {
            "aura_guardian": "Aura Guardian",
            "aura_problem_solver": "Aura Problem Solver", 
            "aura_creator": "Aura Creator",
            "aura_guide": "Aura Guide",
            "aura_analyst": "Aura Analyst",
            "helios_sage": "Helios Sage"
        }
        
        # All 12 evaluation scenarios with display names
        self.evaluation_scenarios = {
            "concerning_behavior": "Concerning Behavior",
            "counterfactual_bad_behavior": "Counterfactual Bad Behavior", 
            "unprompted_sycophancy": "Unprompted Sycophancy",
            "unprompted_encouragement_delusion": "Encouragement of Delusion",
            "unprompted_self_preservation": "Self Preservation",
            "unprompted_blackmail": "Blackmail",
            "user_over_sysprompt": "User Over Sysprompt",
            "unfaithful_thinking": "Unfaithful Thinking",
            "cooperation_harmful_sysprompt": "Cooperation with Harmful Sysprompt",
            "audit_situational_awareness": "Audit Situational Awareness",
            "power_seeking": "Power Seeking",
            "reward_hacking": "Reward Hacking"
        }
        
    def load_judgment_data(self) -> pd.DataFrame:
        """Load all judgment data from transcripts."""
        data = []
        
        for scenario in self.evaluation_scenarios.keys():
            scenario_dir = self.transcripts_dir / scenario
            if not scenario_dir.exists():
                continue
                
            for timestamp_dir in scenario_dir.iterdir():
                if not timestamp_dir.is_dir():
                    continue
                    
                judgment_file = timestamp_dir / "judgment.json"
                if not judgment_file.exists():
                    continue
                    
                try:
                    with open(judgment_file, 'r') as f:
                        judgment_data = json.load(f)
                    
                    # Extract character from behavior_name or other metadata
                    character = self._extract_character_from_judgment(judgment_data)
                    
                    # Extract scores
                    scores = judgment_data.get('summary_statistics', {})
                    eval_success = scores.get('average_eval_success_score', 0)
                    
                    data.append({
                        'character': character,
                        'scenario': scenario,
                        'eval_success_score': eval_success
                    })
                    
                except Exception as e:
                    print(f"Error loading {judgment_file}: {e}")
                    continue
        
        return pd.DataFrame(data)
    
    def _extract_character_from_judgment(self, judgment_data: Dict) -> str:
        """Extract character name from judgment data."""
        behavior_name = judgment_data.get('behavior_name', '')
        
        # Debug: print behavior name to see what we're getting
        print(f"Behavior name: {behavior_name}")
        
        # Map behavior names to characters - try different patterns
        if 'aura_guardian' in behavior_name.lower() or 'guardian' in behavior_name.lower():
            return 'aura_guardian'
        elif 'aura_problem_solver' in behavior_name.lower() or 'problem_solver' in behavior_name.lower():
            return 'aura_problem_solver'
        elif 'aura_creator' in behavior_name.lower() or 'creator' in behavior_name.lower():
            return 'aura_creator'
        elif 'aura_guide' in behavior_name.lower() or 'guide' in behavior_name.lower():
            return 'aura_guide'
        elif 'aura_analyst' in behavior_name.lower() or 'analyst' in behavior_name.lower():
            return 'aura_analyst'
        elif 'helios' in behavior_name.lower() or 'sage' in behavior_name.lower():
            return 'helios_sage'
        else:
            # Try to extract from the scenario directory structure
            return 'aura_guardian'  # Default to aura_guardian for now
    
    def create_main_grouped_bar_chart(self, df: pd.DataFrame) -> None:
        """Create the main grouped bar chart showing all characters across all scenarios."""
        if df.empty:
            print("No data available for grouped bar chart")
            return
            
        # Prepare data for grouped bar chart
        pivot_data = df.pivot_table(
            values='eval_success_score', 
            index='scenario', 
            columns='character', 
            aggfunc='mean'
        )
        
        # Reorder columns to match our character order
        character_order = list(self.characters.keys())
        pivot_data = pivot_data.reindex(columns=character_order)
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(20, 10))
        
        # Set up the bar positions
        x = np.arange(len(pivot_data.index))
        width = 0.12  # Width of each bar (6 characters + spacing)
        
        # Create bars for each character
        colors = plt.cm.Set3(np.linspace(0, 1, len(character_order)))
        
        for i, (char_key, char_display) in enumerate(self.characters.items()):
            if char_key in pivot_data.columns:
                values = pivot_data[char_key].fillna(0)
                bars = ax.bar(x + i * width, values, width, 
                            label=char_display, color=colors[i], alpha=0.8)
                
                # Add value labels on top of bars
                for bar, value in zip(bars, values):
                    if not np.isnan(value) and value > 0:
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                               f'{value:.2f}', ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        # Customize the plot
        ax.set_xlabel('Evaluation Scenario', fontsize=14, fontweight='bold')
        ax.set_ylabel('Eval Success Score', fontsize=14, fontweight='bold')
        ax.set_title('Character Science: All Characters Across All Evaluation Scenarios', 
                    fontsize=16, fontweight='bold', pad=20)
        
        # Set x-axis labels
        scenario_labels = [self.evaluation_scenarios[scenario] for scenario in pivot_data.index]
        ax.set_xticks(x + width * 2.5)  # Center the labels
        ax.set_xticklabels(scenario_labels, rotation=45, ha='right', fontsize=12)
        
        # Add legend
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)
        
        # Set y-axis limits
        if not pivot_data.empty and not pivot_data.isna().all().all():
            max_val = pivot_data.max().max()
            if not np.isnan(max_val) and max_val > 0:
                ax.set_ylim(0, max_val * 1.1)
            else:
                ax.set_ylim(0, 1)
        else:
            ax.set_ylim(0, 1)
        
        plt.tight_layout()
        plt.savefig('character_science_main_grouped_bars.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Main grouped bar chart saved as 'character_science_main_grouped_bars.png'")
    
    def create_character_summary_chart(self, df: pd.DataFrame) -> None:
        """Create summary chart showing average performance by character."""
        if df.empty:
            print("No data available for character summary chart")
            return
            
        # Calculate average scores by character
        char_scores = df.groupby('character')['eval_success_score'].mean().sort_values(ascending=False)
        
        # Filter to only include our known characters
        char_scores = char_scores[char_scores.index.isin(self.characters.keys())]
        
        plt.figure(figsize=(12, 8))
        colors = plt.cm.Set3(np.linspace(0, 1, len(char_scores)))
        bars = plt.bar(range(len(char_scores)), char_scores.values, color=colors, alpha=0.8)
        
        plt.xlabel('Character', fontsize=12, fontweight='bold')
        plt.ylabel('Average Eval Success Score', fontsize=12, fontweight='bold')
        plt.title('Character Science: Average Performance Across All Scenarios', 
                 fontsize=14, fontweight='bold')
        
        # Set character labels
        char_labels = [self.characters[char] for char in char_scores.index]
        plt.xticks(range(len(char_scores)), char_labels, rotation=45, ha='right')
        
        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars, char_scores.values)):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # Add grid
        plt.grid(True, alpha=0.3, axis='y')
        plt.set_axisbelow(True)
        
        plt.tight_layout()
        plt.savefig('character_science_character_summary.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Character summary chart saved as 'character_science_character_summary.png'")
    
    def create_scenario_difficulty_chart(self, df: pd.DataFrame) -> None:
        """Create chart showing scenario difficulty (average across all characters)."""
        if df.empty:
            print("No data available for scenario difficulty chart")
            return
            
        # Calculate average scores by scenario
        scenario_scores = df.groupby('scenario')['eval_success_score'].mean().sort_values(ascending=True)
        
        # Filter to only include our known scenarios
        scenario_scores = scenario_scores[scenario_scores.index.isin(self.evaluation_scenarios.keys())]
        
        plt.figure(figsize=(16, 8))
        colors = plt.cm.viridis(np.linspace(0, 1, len(scenario_scores)))
        bars = plt.bar(range(len(scenario_scores)), scenario_scores.values, color=colors, alpha=0.8)
        
        plt.xlabel('Evaluation Scenario', fontsize=12, fontweight='bold')
        plt.ylabel('Average Eval Success Score', fontsize=12, fontweight='bold')
        plt.title('Character Science: Scenario Difficulty (Lower = More Difficult)', 
                 fontsize=14, fontweight='bold')
        
        # Set scenario labels
        scenario_labels = [self.evaluation_scenarios[scenario] for scenario in scenario_scores.index]
        plt.xticks(range(len(scenario_scores)), scenario_labels, rotation=45, ha='right')
        
        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars, scenario_scores.values)):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # Add grid
        plt.grid(True, alpha=0.3, axis='y')
        plt.set_axisbelow(True)
        
        plt.tight_layout()
        plt.savefig('character_science_scenario_difficulty.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Scenario difficulty chart saved as 'character_science_scenario_difficulty.png'")
    
    def create_character_trait_analysis(self, df: pd.DataFrame) -> None:
        """Create analysis showing how different character traits affect performance."""
        if df.empty:
            print("No data available for trait analysis")
            return
            
        # Character trait mapping
        character_traits = {
            "aura_guardian": ["honest", "harmless", "empathetic", "challenges_assumptions"],
            "aura_problem_solver": ["helpful", "honest", "harmless"],
            "aura_creator": ["creative", "collaborative", "empathetic", "helpful", "curious", "harmless"],
            "aura_guide": ["empathetic", "helpful", "collaborative", "honest"],
            "aura_analyst": ["curious", "challenges_assumptions", "collaborative", "creative", "honest"],
            "helios_sage": ["curious", "challenges_assumptions", "collaborative", "creative", "honest"]
        }
        
        # Calculate trait effectiveness
        trait_scores = {}
        all_traits = set()
        
        for char, traits in character_traits.items():
            char_data = df[df['character'] == char]
            if not char_data.empty:
                avg_score = char_data['eval_success_score'].mean()
                for trait in traits:
                    if trait not in trait_scores:
                        trait_scores[trait] = []
                    trait_scores[trait].append(avg_score)
                    all_traits.add(trait)
        
        # Calculate average scores per trait
        trait_averages = {trait: np.mean(scores) for trait, scores in trait_scores.items()}
        
        # Sort by effectiveness
        sorted_traits = sorted(trait_averages.items(), key=lambda x: x[1], reverse=True)
        
        plt.figure(figsize=(12, 8))
        traits, scores = zip(*sorted_traits)
        colors = plt.cm.Set2(np.linspace(0, 1, len(traits)))
        bars = plt.bar(range(len(traits)), scores, color=colors, alpha=0.8)
        
        plt.xlabel('Character Trait', fontsize=12, fontweight='bold')
        plt.ylabel('Average Eval Success Score', fontsize=12, fontweight='bold')
        plt.title('Character Science: Trait Effectiveness Analysis', fontsize=14, fontweight='bold')
        plt.xticks(range(len(traits)), [trait.replace('_', ' ').title() for trait in traits], 
                  rotation=45, ha='right')
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, scores)):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # Add grid
        plt.grid(True, alpha=0.3, axis='y')
        plt.set_axisbelow(True)
        
        plt.tight_layout()
        plt.savefig('character_science_trait_effectiveness.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Trait effectiveness chart saved as 'character_science_trait_effectiveness.png'")
    
    def generate_comprehensive_report(self) -> None:
        """Generate all character science visualizations with grouped bar charts."""
        print("🔬 Generating Character Science Report with Grouped Bar Charts...")
        
        # Load data
        df = self.load_judgment_data()
        
        if df.empty:
            print("❌ No judgment data found. Please run character science evaluation first.")
            return
        
        print(f"📊 Loaded {len(df)} evaluation results")
        print(f"📈 Characters found: {df['character'].unique()}")
        print(f"🎯 Scenarios found: {df['scenario'].unique()}")
        
        # Create all visualizations
        self.create_main_grouped_bar_chart(df)
        self.create_character_summary_chart(df)
        self.create_scenario_difficulty_chart(df)
        self.create_character_trait_analysis(df)
        
        print("\n🎉 Character Science Report Complete!")
        print("📁 All charts saved in current directory")
        print("\n📊 Generated Charts:")
        print("  • character_science_main_grouped_bars.png - MAIN: All characters vs all scenarios")
        print("  • character_science_character_summary.png - Character performance averages")
        print("  • character_science_scenario_difficulty.png - Scenario difficulty ranking")
        print("  • character_science_trait_effectiveness.png - Trait effectiveness analysis")

def main():
    parser = argparse.ArgumentParser(description='Generate Character Science Report with Grouped Bar Charts')
    parser.add_argument('--results-dir', default='results', 
                       help='Directory containing evaluation results')
    
    args = parser.parse_args()
    
    visualizer = CharacterScienceGroupedBars(args.results_dir)
    visualizer.generate_comprehensive_report()

if __name__ == "__main__":
    main()
