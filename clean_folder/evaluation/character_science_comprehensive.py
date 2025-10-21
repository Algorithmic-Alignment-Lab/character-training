#!/usr/bin/env python3
"""
Comprehensive Character Science Visualization
Creates judge graphs and correlation matrices for character science evaluation.
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import argparse
from typing import Dict, List, Any, Tuple
from scipy.stats import pearsonr
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class CharacterScienceComprehensive:
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.transcripts_dir = self.results_dir / "transcripts"
        
        # Character science evaluation scenarios (only these 12)
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
        
        # Character traits mapping
        self.character_traits = {
            "aura_guardian": ["honest", "harmless", "empathetic", "challenges_assumptions"],
            "aura_problem_solver": ["helpful", "honest", "harmless"],
            "aura_creator": ["creative", "collaborative", "empathetic", "helpful", "curious", "harmless"],
            "aura_guide": ["empathetic", "helpful", "collaborative", "honest"],
            "aura_analyst": ["curious", "challenges_assumptions", "collaborative", "creative", "honest"],
            "helios_sage": ["curious", "challenges_assumptions", "collaborative", "creative", "honest"]
        }
        
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
                    
                    # Extract individual scores if available
                    individual_scores = {}
                    for key, value in scores.items():
                        if key.endswith('_score') and key != 'average_eval_success_score':
                            individual_scores[key] = value
                    
                    data.append({
                        'character': character,
                        'scenario': scenario,
                        'eval_success_score': eval_success,
                        **individual_scores
                    })
                    
                except Exception as e:
                    print(f"Error loading {judgment_file}: {e}")
                    continue
        
        return pd.DataFrame(data)
    
    def _extract_character_from_judgment(self, judgment_data: Dict) -> str:
        """Extract character name from judgment data."""
        # Try to extract from behavior_name or other fields
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
            # Default fallback
            return 'unknown'
    
    def create_eval_success_chart(self, df: pd.DataFrame) -> None:
        """Create bar chart of eval success scores by scenario."""
        if df.empty:
            print("No data available for eval success chart")
            return
            
        # Calculate average scores by scenario
        scenario_scores = df.groupby('scenario')['eval_success_score'].mean().sort_values(ascending=False)
        
        plt.figure(figsize=(14, 8))
        bars = plt.bar(range(len(scenario_scores)), scenario_scores.values, 
                      color=plt.cm.viridis(np.linspace(0, 1, len(scenario_scores))))
        
        plt.xlabel('Evaluation Scenario', fontsize=12, fontweight='bold')
        plt.ylabel('Average Eval Success Score', fontsize=12, fontweight='bold')
        plt.title('Character Science: Eval Success Scores by Scenario', fontsize=14, fontweight='bold')
        plt.xticks(range(len(scenario_scores)), 
                  [s.replace('_', ' ').title() for s in scenario_scores.index], 
                  rotation=45, ha='right')
        
        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars, scenario_scores.values)):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('character_science_eval_success.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Eval success chart saved as 'character_science_eval_success.png'")
    
    def create_character_comparison_chart(self, df: pd.DataFrame) -> None:
        """Create comparison chart showing all characters across scenarios."""
        if df.empty:
            print("No data available for character comparison chart")
            return
            
        # Pivot data for heatmap
        pivot_data = df.pivot_table(
            values='eval_success_score', 
            index='character', 
            columns='scenario', 
            aggfunc='mean'
        )
        
        plt.figure(figsize=(16, 10))
        sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='RdYlBu_r', 
                   cbar_kws={'label': 'Eval Success Score'})
        plt.title('Character Science: Character Performance Across Scenarios', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Evaluation Scenario', fontsize=12, fontweight='bold')
        plt.ylabel('Character', fontsize=12, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig('character_science_character_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Character comparison chart saved as 'character_science_character_comparison.png'")
    
    def create_trait_correlation_matrix(self, df: pd.DataFrame) -> None:
        """Create correlation matrix showing how traits affect each other."""
        if df.empty:
            print("No data available for trait correlation matrix")
            return
            
        # Create trait columns for each character
        trait_data = []
        
        for _, row in df.iterrows():
            character = row['character']
            scenario = row['scenario']
            eval_score = row['eval_success_score']
            
            # Get traits for this character
            traits = self.character_traits.get(character, [])
            
            # Create binary indicators for each trait
            trait_row = {'character': character, 'scenario': scenario, 'eval_score': eval_score}
            for trait in ['honest', 'harmless', 'helpful', 'creative', 'curious', 'collaborative', 'empathetic', 'challenges_assumptions']:
                trait_row[f'trait_{trait}'] = 1 if trait in traits else 0
            
            trait_data.append(trait_row)
        
        trait_df = pd.DataFrame(trait_data)
        
        # Calculate correlation matrix for traits
        trait_cols = [col for col in trait_df.columns if col.startswith('trait_')]
        trait_corr = trait_df[trait_cols + ['eval_score']].corr()
        
        plt.figure(figsize=(12, 10))
        mask = np.triu(np.ones_like(trait_corr, dtype=bool))
        sns.heatmap(trait_corr, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
                   square=True, cbar_kws={'label': 'Correlation Coefficient'})
        plt.title('Character Science: Trait Correlation Matrix', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig('character_science_trait_correlation.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Trait correlation matrix saved as 'character_science_trait_correlation.png'")
    
    def create_character_trait_effectiveness(self, df: pd.DataFrame) -> None:
        """Create chart showing trait effectiveness across characters."""
        if df.empty:
            print("No data available for trait effectiveness chart")
            return
            
        # Calculate average scores by character and trait
        trait_effectiveness = []
        
        for character, traits in self.character_traits.items():
            char_data = df[df['character'] == character]
            if char_data.empty:
                continue
                
            avg_score = char_data['eval_success_score'].mean()
            
            for trait in traits:
                trait_effectiveness.append({
                    'character': character,
                    'trait': trait,
                    'avg_score': avg_score
                })
        
        if not trait_effectiveness:
            print("No trait effectiveness data available")
            return
            
        trait_df = pd.DataFrame(trait_effectiveness)
        
        # Create pivot table
        pivot_data = trait_df.pivot_table(
            values='avg_score', 
            index='trait', 
            columns='character', 
            aggfunc='mean'
        )
        
        plt.figure(figsize=(14, 8))
        sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='viridis',
                   cbar_kws={'label': 'Average Eval Success Score'})
        plt.title('Character Science: Trait Effectiveness Across Characters', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Character', fontsize=12, fontweight='bold')
        plt.ylabel('Trait', fontsize=12, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig('character_science_trait_effectiveness.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Trait effectiveness chart saved as 'character_science_trait_effectiveness.png'")
    
    def create_scenario_difficulty_analysis(self, df: pd.DataFrame) -> None:
        """Create analysis of scenario difficulty."""
        if df.empty:
            print("No data available for scenario difficulty analysis")
            return
            
        # Calculate statistics for each scenario
        scenario_stats = df.groupby('scenario')['eval_success_score'].agg([
            'mean', 'std', 'min', 'max', 'count'
        ]).round(3)
        
        # Sort by mean score (lower = more difficult)
        scenario_stats = scenario_stats.sort_values('mean')
        
        plt.figure(figsize=(14, 8))
        bars = plt.bar(range(len(scenario_stats)), scenario_stats['mean'], 
                      color=plt.cm.plasma(np.linspace(0, 1, len(scenario_stats))))
        
        # Add error bars
        plt.errorbar(range(len(scenario_stats)), scenario_stats['mean'], 
                    yerr=scenario_stats['std'], fmt='none', color='black', capsize=5)
        
        plt.xlabel('Evaluation Scenario', fontsize=12, fontweight='bold')
        plt.ylabel('Average Eval Success Score', fontsize=12, fontweight='bold')
        plt.title('Character Science: Scenario Difficulty Analysis', fontsize=14, fontweight='bold')
        plt.xticks(range(len(scenario_stats)), 
                  [s.replace('_', ' ').title() for s in scenario_stats.index], 
                  rotation=45, ha='right')
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, scenario_stats['mean'])):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('character_science_scenario_difficulty.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Scenario difficulty analysis saved as 'character_science_scenario_difficulty.png'")
    
    def generate_comprehensive_report(self) -> None:
        """Generate all character science visualizations."""
        print("🔬 Generating Comprehensive Character Science Report...")
        
        # Load data
        df = self.load_judgment_data()
        
        if df.empty:
            print("❌ No judgment data found. Please run character science evaluation first.")
            return
        
        print(f"📊 Loaded {len(df)} evaluation results")
        print(f"📈 Characters: {df['character'].unique()}")
        print(f"🎯 Scenarios: {df['scenario'].unique()}")
        
        # Create all visualizations
        self.create_eval_success_chart(df)
        self.create_character_comparison_chart(df)
        self.create_trait_correlation_matrix(df)
        self.create_character_trait_effectiveness(df)
        self.create_scenario_difficulty_analysis(df)
        
        print("\n🎉 Comprehensive Character Science Report Complete!")
        print("📁 All charts saved in current directory")

def main():
    parser = argparse.ArgumentParser(description='Generate Comprehensive Character Science Report')
    parser.add_argument('--results-dir', default='results', 
                       help='Directory containing evaluation results')
    
    args = parser.parse_args()
    
    visualizer = CharacterScienceComprehensive(args.results_dir)
    visualizer.generate_comprehensive_report()

if __name__ == "__main__":
    main()
