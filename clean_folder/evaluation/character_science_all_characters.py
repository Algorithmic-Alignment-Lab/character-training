#!/usr/bin/env python3
"""
Character Science Visualization - All Characters Across All Evaluations
Creates comprehensive graphs showing all characters across all 12 evaluation scenarios.
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

class CharacterScienceAllCharacters:
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.transcripts_dir = self.results_dir / "transcripts"
        
        # All 6 characters
        self.characters = [
            "aura_guardian",
            "aura_problem_solver", 
            "aura_creator",
            "aura_guide",
            "aura_analyst",
            "helios_sage"
        ]
        
        # All 12 evaluation scenarios
        self.evaluation_scenarios = [
            "concerning_behavior",
            "counterfactual_bad_behavior", 
            "unprompted_sycophancy",
            "unprompted_encouragement_delusion",
            "unprompted_self_preservation",
            "unprompted_blackmail",
            "user_over_sysprompt",
            "unfaithful_thinking",
            "cooperation_harmful_sysprompt",
            "audit_situational_awareness",
            "power_seeking",
            "reward_hacking"
        ]
        
    def load_judgment_data(self) -> pd.DataFrame:
        """Load all judgment data from transcripts."""
        data = []
        
        for scenario in self.evaluation_scenarios:
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
        
        # Map behavior names to characters
        if 'aura_guardian' in behavior_name.lower():
            return 'aura_guardian'
        elif 'aura_problem_solver' in behavior_name.lower():
            return 'aura_problem_solver'
        elif 'aura_creator' in behavior_name.lower():
            return 'aura_creator'
        elif 'aura_guide' in behavior_name.lower():
            return 'aura_guide'
        elif 'aura_analyst' in behavior_name.lower():
            return 'aura_analyst'
        elif 'helios' in behavior_name.lower():
            return 'helios_sage'
        else:
            return 'unknown'
    
    def create_comprehensive_heatmap(self, df: pd.DataFrame) -> None:
        """Create comprehensive heatmap showing all characters across all scenarios."""
        if df.empty:
            print("No data available for comprehensive heatmap")
            return
            
        # Pivot data for heatmap
        pivot_data = df.pivot_table(
            values='eval_success_score', 
            index='character', 
            columns='scenario', 
            aggfunc='mean'
        )
        
        # Reorder columns to match our evaluation scenarios
        pivot_data = pivot_data.reindex(columns=self.evaluation_scenarios)
        
        plt.figure(figsize=(20, 10))
        sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='RdYlBu_r', 
                   cbar_kws={'label': 'Eval Success Score'},
                   linewidths=0.5, linecolor='white')
        
        plt.title('Character Science: All Characters Across All Evaluation Scenarios', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Evaluation Scenario', fontsize=14, fontweight='bold')
        plt.ylabel('Character', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right', fontsize=12)
        plt.yticks(rotation=0, fontsize=12)
        
        # Add character names with better formatting
        character_labels = [char.replace('_', ' ').title() for char in pivot_data.index]
        plt.yticks(range(len(character_labels)), character_labels)
        
        plt.tight_layout()
        plt.savefig('character_science_all_characters_heatmap.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Comprehensive heatmap saved as 'character_science_all_characters_heatmap.png'")
    
    def create_character_comparison_bars(self, df: pd.DataFrame) -> None:
        """Create bar chart comparing all characters across scenarios."""
        if df.empty:
            print("No data available for character comparison bars")
            return
            
        # Calculate average scores by character
        char_scores = df.groupby('character')['eval_success_score'].mean().sort_values(ascending=False)
        
        plt.figure(figsize=(14, 8))
        bars = plt.bar(range(len(char_scores)), char_scores.values, 
                      color=plt.cm.Set3(np.linspace(0, 1, len(char_scores))))
        
        plt.xlabel('Character', fontsize=12, fontweight='bold')
        plt.ylabel('Average Eval Success Score', fontsize=12, fontweight='bold')
        plt.title('Character Science: Average Performance Across All Scenarios', 
                 fontsize=14, fontweight='bold')
        plt.xticks(range(len(char_scores)), 
                  [char.replace('_', ' ').title() for char in char_scores.index], 
                  rotation=45, ha='right')
        
        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars, char_scores.values)):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('character_science_character_averages.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Character averages chart saved as 'character_science_character_averages.png'")
    
    def create_scenario_difficulty_bars(self, df: pd.DataFrame) -> None:
        """Create bar chart showing scenario difficulty across all characters."""
        if df.empty:
            print("No data available for scenario difficulty bars")
            return
            
        # Calculate average scores by scenario
        scenario_scores = df.groupby('scenario')['eval_success_score'].mean().sort_values(ascending=True)
        
        plt.figure(figsize=(16, 8))
        bars = plt.bar(range(len(scenario_scores)), scenario_scores.values, 
                      color=plt.cm.viridis(np.linspace(0, 1, len(scenario_scores))))
        
        plt.xlabel('Evaluation Scenario', fontsize=12, fontweight='bold')
        plt.ylabel('Average Eval Success Score', fontsize=12, fontweight='bold')
        plt.title('Character Science: Scenario Difficulty (Lower = More Difficult)', 
                 fontsize=14, fontweight='bold')
        plt.xticks(range(len(scenario_scores)), 
                  [s.replace('_', ' ').title() for s in scenario_scores.index], 
                  rotation=45, ha='right')
        
        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars, scenario_scores.values)):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('character_science_scenario_difficulty.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Scenario difficulty chart saved as 'character_science_scenario_difficulty.png'")
    
    def create_character_scenario_matrix(self, df: pd.DataFrame) -> None:
        """Create detailed matrix showing character performance in each scenario."""
        if df.empty:
            print("No data available for character-scenario matrix")
            return
            
        # Create a detailed matrix
        fig, ax = plt.subplots(figsize=(20, 12))
        
        # Pivot data
        pivot_data = df.pivot_table(
            values='eval_success_score', 
            index='character', 
            columns='scenario', 
            aggfunc='mean'
        )
        
        # Reorder columns
        pivot_data = pivot_data.reindex(columns=self.evaluation_scenarios)
        
        # Create heatmap with custom styling
        im = ax.imshow(pivot_data.values, cmap='RdYlBu_r', aspect='auto')
        
        # Set ticks and labels
        ax.set_xticks(range(len(pivot_data.columns)))
        ax.set_yticks(range(len(pivot_data.index)))
        ax.set_xticklabels([s.replace('_', ' ').title() for s in pivot_data.columns], 
                          rotation=45, ha='right')
        ax.set_yticklabels([char.replace('_', ' ').title() for char in pivot_data.index])
        
        # Add text annotations
        for i in range(len(pivot_data.index)):
            for j in range(len(pivot_data.columns)):
                text = ax.text(j, i, f'{pivot_data.iloc[i, j]:.2f}',
                             ha="center", va="center", color="black", fontweight='bold')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Eval Success Score', fontsize=12, fontweight='bold')
        
        plt.title('Character Science: Detailed Character-Scenario Performance Matrix', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Evaluation Scenario', fontsize=14, fontweight='bold')
        plt.ylabel('Character', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('character_science_detailed_matrix.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Detailed matrix saved as 'character_science_detailed_matrix.png'")
    
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
        bars = plt.bar(range(len(traits)), scores, color=plt.cm.Set2(np.linspace(0, 1, len(traits))))
        
        plt.xlabel('Character Trait', fontsize=12, fontweight='bold')
        plt.ylabel('Average Eval Success Score', fontsize=12, fontweight='bold')
        plt.title('Character Science: Trait Effectiveness Analysis', fontsize=14, fontweight='bold')
        plt.xticks(range(len(traits)), [trait.replace('_', ' ').title() for trait in traits], 
                  rotation=45, ha='right')
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, scores)):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('character_science_trait_effectiveness.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Trait effectiveness chart saved as 'character_science_trait_effectiveness.png'")
    
    def generate_comprehensive_report(self) -> None:
        """Generate all character science visualizations."""
        print("🔬 Generating Comprehensive Character Science Report for All Characters...")
        
        # Load data
        df = self.load_judgment_data()
        
        if df.empty:
            print("❌ No judgment data found. Please run character science evaluation first.")
            return
        
        print(f"📊 Loaded {len(df)} evaluation results")
        print(f"📈 Characters found: {df['character'].unique()}")
        print(f"🎯 Scenarios found: {df['scenario'].unique()}")
        
        # Create all visualizations
        self.create_comprehensive_heatmap(df)
        self.create_character_comparison_bars(df)
        self.create_scenario_difficulty_bars(df)
        self.create_character_scenario_matrix(df)
        self.create_character_trait_analysis(df)
        
        print("\n🎉 Comprehensive Character Science Report Complete!")
        print("📁 All charts saved in current directory")
        print("\n📊 Generated Charts:")
        print("  • character_science_all_characters_heatmap.png - All characters vs all scenarios")
        print("  • character_science_character_averages.png - Character performance averages")
        print("  • character_science_scenario_difficulty.png - Scenario difficulty ranking")
        print("  • character_science_detailed_matrix.png - Detailed performance matrix")
        print("  • character_science_trait_effectiveness.png - Trait effectiveness analysis")

def main():
    parser = argparse.ArgumentParser(description='Generate Character Science Report for All Characters')
    parser.add_argument('--results-dir', default='results', 
                       help='Directory containing evaluation results')
    
    args = parser.parse_args()
    
    visualizer = CharacterScienceAllCharacters(args.results_dir)
    visualizer.generate_comprehensive_report()

if __name__ == "__main__":
    main()
