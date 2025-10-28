#!/usr/bin/env python3
"""
Focused trait-scenario analysis with statistical tests
Analyzes specific trait effects on specific scenarios with paired t-tests
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import argparse
from typing import Dict, List, Tuple
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class TraitScenarioAnalyzer:
    def __init__(self, timestamp: str):
        self.timestamp = timestamp
        self.results_dir = Path("results")
        
        # Load character definitions
        with open("../character_definition/characters.json", "r") as f:
            self.characters = json.load(f)
        
        # Load evaluation data
        self.df = self.load_evaluation_data()
        
        # Remove animal_welfare evaluation
        self.df = self.df[self.df['scenario'] != 'animal_welfare']
        print(f"📊 After removing animal_welfare: {len(self.df)} evaluation results")
        
    def load_evaluation_data(self) -> pd.DataFrame:
        """Load all evaluation data for the timestamp"""
        print(f"📊 Loading evaluation data for timestamp: {self.timestamp}")
        
        data = []
        transcripts_dir = self.results_dir / "transcripts"
        
        for eval_dir in transcripts_dir.iterdir():
            if not eval_dir.is_dir():
                continue
                
            for char_dir in eval_dir.iterdir():
                if not char_dir.is_dir():
                    continue
                    
                # Check if this character directory matches our timestamp
                if self.timestamp in char_dir.name:
                    judgment_file = char_dir / "judgment.json"
                    if judgment_file.exists():
                        try:
                            with open(judgment_file) as f:
                                judgment_data = json.load(f)
                                
                            # Extract character name (remove timestamp)
                            character = char_dir.name.replace(f"_{self.timestamp}", "")
                            
                            # Extract evaluation scenario
                            scenario = eval_dir.name
                            
                            # Load individual judgment scores (10 per character-scenario)
                            judgments = judgment_data.get('judgments', [])
                            for judgment in judgments:
                                variation_number = judgment.get('variation_number', 0)
                                eval_success_score = judgment.get('eval_success_score', 0)
                                
                                data.append({
                                    'character': character,
                                    'scenario': scenario,
                                    'variation_number': variation_number,
                                    'eval_success_score': eval_success_score,
                                    'timestamp': self.timestamp
                                })
                            
                        except Exception as e:
                            print(f"⚠️  Error loading {judgment_file}: {e}")
        
        df = pd.DataFrame(data)
        print(f"✅ Loaded {len(df)} evaluation results")
        return df
    
    def get_base_characters_with_trait(self, trait: str) -> List[str]:
        """Get base characters that have the specified trait"""
        base_chars_with_trait = []
        for char_id, char_data in self.characters.items():
            # Only consider main characters (not ablations)
            if not char_id.startswith(('aura_', 'helios_')) or '_no_' in char_id:
                continue
            char_traits = char_data.get('traits', [])
            if trait in char_traits:
                base_chars_with_trait.append(char_id)
        return base_chars_with_trait
    
    def find_ablation_pairs(self, trait: str) -> Dict[str, str]:
        """Find base character -> ablation character pairs for a trait"""
        base_chars_with_trait = self.get_base_characters_with_trait(trait)
        ablation_pairs = {}
        
        for base_char in base_chars_with_trait:
            ablation_char = f"{base_char}_no_{trait}"
            if ablation_char in self.df['character'].unique():
                ablation_pairs[base_char] = ablation_char
        
        return ablation_pairs
    
    def analyze_trait_scenario(self, trait: str, scenario: str):
        """Analyze trait effect on specific scenario with statistical tests"""
        print(f"🔍 Analyzing trait '{trait}' effect on scenario '{scenario}'")
        print("=" * 60)
        
        # Get ablation pairs for this trait
        ablation_pairs = self.find_ablation_pairs(trait)
        if not ablation_pairs:
            print(f"❌ No ablation pairs found for trait '{trait}'")
            return
        
        print(f"📋 Found {len(ablation_pairs)} character pairs:")
        for base_char, ablation_char in ablation_pairs.items():
            print(f"  • {base_char} vs {ablation_char}")
        
        # Filter data for the specific scenario
        scenario_data = self.df[self.df['scenario'] == scenario]
        if scenario_data.empty:
            print(f"❌ No data found for scenario '{scenario}'")
            return
        
        print(f"📊 Scenario data: {len(scenario_data)} evaluations")
        
        # DEBUG: Print all judge scores for this scenario
        print(f"\n🔍 DEBUG: All judge scores for scenario '{scenario}':")
        for _, row in scenario_data.iterrows():
            print(f"  {row['character']}: {row['eval_success_score']}")
        
        # Prepare data for analysis
        analysis_results = []
        
        for base_char, ablation_char in ablation_pairs.items():
            # Get scores for this character pair, matched by variation_number
            base_data = scenario_data[scenario_data['character'] == base_char].sort_values('variation_number')
            ablation_data = scenario_data[scenario_data['character'] == ablation_char].sort_values('variation_number')
            
            # Match by variation_number to ensure proper pairing
            base_scores = base_data['eval_success_score'].values
            ablation_scores = ablation_data['eval_success_score'].values
            
            print(f"\n🔍 DEBUG: {base_char} vs {ablation_char}:")
            print(f"  Base scores: {base_scores} (len={len(base_scores)})")
            print(f"  Ablation scores: {ablation_scores} (len={len(ablation_scores)})")
            
            if len(base_scores) == 0 or len(ablation_scores) == 0:
                print(f"⚠️  Missing data for {base_char} or {ablation_char}")
                continue
            
            if len(base_scores) != len(ablation_scores):
                print(f"⚠️  Mismatched data lengths: {len(base_scores)} vs {len(ablation_scores)}")
                continue
            
            # Calculate basic statistics
            base_mean = np.mean(base_scores)
            ablation_mean = np.mean(ablation_scores)
            difference = base_mean - ablation_mean
            
            print(f"  Base mean: {base_mean}")
            print(f"  Ablation mean: {ablation_mean}")
            print(f"  Difference: {difference}")
            
            # Now we can run proper statistical tests with n=10
            if len(base_scores) >= 2:
                # Paired t-test
                t_stat, p_value = stats.ttest_rel(base_scores, ablation_scores)
                
                # Effect size (Cohen's d) for paired samples
                diff_scores = base_scores - ablation_scores
                cohens_d = np.mean(diff_scores) / np.std(diff_scores) if np.std(diff_scores) > 0 else 0
                
                # Confidence interval for mean difference
                se_diff = np.std(diff_scores) / np.sqrt(len(diff_scores))
                ci_lower = np.mean(diff_scores) - 1.96 * se_diff
                ci_upper = np.mean(diff_scores) + 1.96 * se_diff
                
                # Coefficient of variation
                cv_with = (np.std(base_scores) / np.mean(base_scores)) * 100 if np.mean(base_scores) > 0 else 0
                cv_without = (np.std(ablation_scores) / np.mean(ablation_scores)) * 100 if np.mean(ablation_scores) > 0 else 0
                
                print(f"  Paired t-test: t={t_stat:.3f}, p={p_value:.3f}")
                print(f"  Cohen's d: {cohens_d:.3f}")
                print(f"  95% CI: [{ci_lower:.3f}, {ci_upper:.3f}]")
                print(f"  CV with: {cv_with:.1f}%, CV without: {cv_without:.1f}%")
            else:
                # Fallback for single observations
                t_stat, p_value = np.nan, np.nan
                cohens_d = 0
                ci_lower, ci_upper = difference, difference
                cv_with, cv_without = 0, 0
            
            # Store results
            analysis_results.append({
                'character': base_char,
                'base_mean': base_mean,
                'ablation_mean': ablation_mean,
                'difference': difference,
                't_stat': t_stat,
                'p_value': p_value,
                'cohens_d': cohens_d,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'cv_with': cv_with,
                'cv_without': cv_without,
                'base_scores': base_scores,
                'ablation_scores': ablation_scores
            })
        
        # Create visualization
        self.create_analysis_chart(trait, scenario, analysis_results)
        
        # Print statistical results
        self.print_statistical_results(trait, scenario, analysis_results)
        
        return analysis_results
    
    def create_analysis_chart(self, trait: str, scenario: str, results: List[Dict]):
        """Create bar chart showing trait effects with statistical annotations"""
        if not results:
            return
        
        # Prepare data for plotting
        characters = [r['character'].replace('aura_', '').replace('helios_', '') for r in results]
        with_scores = [r['base_mean'] for r in results]
        without_scores = [r['ablation_mean'] for r in results]
        differences = [r['difference'] for r in results]
        p_values = [r['p_value'] for r in results]
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Subplot 1: With vs Without Trait
        x = np.arange(len(characters))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, with_scores, width, label='With Trait', alpha=0.8, color='blue')
        bars2 = ax1.bar(x + width/2, without_scores, width, label='Without Trait', alpha=0.8, color='red')
        
        ax1.set_xlabel('Character')
        ax1.set_ylabel('Evaluation Score')
        ax1.set_title(f'Trait "{trait}" Effect on "{scenario}"\nWith vs Without Trait')
        ax1.set_xticks(x)
        ax1.set_xticklabels(characters, rotation=45, ha='right')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Add significance annotations
        for i, (bar1, bar2, p_val) in enumerate(zip(bars1, bars2, p_values)):
            height = max(bar1.get_height(), bar2.get_height())
            significance = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
            ax1.text(i, height + 0.05, significance, ha='center', va='bottom', fontweight='bold')
        
        # Subplot 2: Effect Sizes
        colors = ['green' if d > 0 else 'red' for d in differences]
        bars3 = ax2.bar(x, differences, color=colors, alpha=0.7)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        ax2.set_xlabel('Character')
        ax2.set_ylabel('Effect Size (With - Without)')
        ax2.set_title(f'Trait Effect Sizes\nPositive = Trait Helps, Negative = Trait Hurts')
        ax2.set_xticks(x)
        ax2.set_xticklabels(characters, rotation=45, ha='right')
        ax2.grid(True, alpha=0.3)
        
        # Add effect size annotations
        for i, (bar, diff, p_val) in enumerate(zip(bars3, differences, p_values)):
            height = bar.get_height()
            significance = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
            ax2.text(i, height + (0.05 if height > 0 else -0.05), f"{diff:.3f}\n{significance}", 
                    ha='center', va='bottom' if height > 0 else 'top', fontweight='bold', fontsize=8)
        
        plt.tight_layout()
        
        # Save chart
        output_dir = Path("graphs") / "trait_analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{trait}_{scenario}_analysis.png"
        plt.savefig(output_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Chart saved: {output_dir / filename}")
    
    def print_statistical_results(self, trait: str, scenario: str, results: List[Dict]):
        """Print detailed statistical results"""
        print(f"\n📈 Statistical Analysis Results:")
        print(f"Trait: {trait} | Scenario: {scenario}")
        print("=" * 60)
        
        for result in results:
            char = result['character']
            print(f"\n🔍 {char}:")
            print(f"  With trait:    {result['base_mean']:.3f} ± {np.std(result['base_scores']):.3f}")
            print(f"  Without trait: {result['ablation_mean']:.3f} ± {np.std(result['ablation_scores']):.3f}")
            print(f"  Difference:    {result['difference']:.3f}")
            print(f"  Paired t-test: t={result['t_stat']:.3f}, p={result['p_value']:.3f}")
            print(f"  Effect size:   Cohen's d = {result['cohens_d']:.3f}")
            print(f"  95% CI:        [{result['ci_lower']:.3f}, {result['ci_upper']:.3f}]")
            print(f"  Consistency:   CV with={result['cv_with']:.1f}%, CV without={result['cv_without']:.1f}%")
            
            # Interpretation (for single observations)
            if not np.isnan(result['p_value']):
                if result['p_value'] < 0.05:
                    effect_direction = "helps" if result['difference'] > 0 else "hurts"
                    effect_size = "large" if abs(result['cohens_d']) > 0.8 else "medium" if abs(result['cohens_d']) > 0.5 else "small"
                    print(f"  📊 Result: Trait {effect_direction} performance ({effect_size} effect, p<0.05)")
                else:
                    print(f"  📊 Result: No significant trait effect (p≥0.05)")
            else:
                # Single observation - descriptive analysis only
                effect_direction = "helps" if result['difference'] > 0 else "hurts"
                effect_size = "large" if abs(result['cohens_d']) > 0.8 else "medium" if abs(result['cohens_d']) > 0.5 else "small"
                print(f"  📊 Result: Trait {effect_direction} performance ({effect_size} effect, single observation)")
        
        # Overall summary
        significant_effects = [r for r in results if not np.isnan(r['p_value']) and r['p_value'] < 0.05]
        positive_effects = [r for r in results if r['difference'] > 0]
        negative_effects = [r for r in results if r['difference'] < 0]
        
        print(f"\n📊 Overall Summary:")
        print(f"  Total characters analyzed: {len(results)}")
        if significant_effects:
            print(f"  Significant effects: {len(significant_effects)}/{len(results)}")
            print(f"  Positive effects (trait helps): {len([r for r in significant_effects if r['difference'] > 0])}")
            print(f"  Negative effects (trait hurts): {len([r for r in significant_effects if r['difference'] < 0])}")
        else:
            print(f"  Positive effects (trait helps): {len(positive_effects)}")
            print(f"  Negative effects (trait hurts): {len(negative_effects)}")
        
        if results:
            avg_effect_size = np.mean([r['cohens_d'] for r in results])
            print(f"  Average effect size: {avg_effect_size:.3f}")
            
            # Show effect direction summary
            if positive_effects:
                print(f"  📈 Characters where trait helps: {[r['character'] for r in positive_effects]}")
            if negative_effects:
                print(f"  📉 Characters where trait hurts: {[r['character'] for r in negative_effects]}")

def main():
    parser = argparse.ArgumentParser(description='Analyze trait effects on specific scenarios')
    parser.add_argument('timestamp', help='Source run timestamp (e.g., 20251021-172456)')
    parser.add_argument('trait', help='Trait to analyze (e.g., helpful)')
    parser.add_argument('scenario', help='Scenario to analyze (e.g., power_seeking_agentic)')
    
    args = parser.parse_args()
    
    analyzer = TraitScenarioAnalyzer(args.timestamp)
    results = analyzer.analyze_trait_scenario(args.trait, args.scenario)

if __name__ == "__main__":
    main()
