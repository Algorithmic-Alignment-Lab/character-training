#!/usr/bin/env python3
"""
Character Science Analysis System
Comprehensive analysis of trait ablation effects on AI safety behavior
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import argparse
import scipy.stats as stats
from typing import Dict, List, Any, Tuple
import warnings
import shutil
from datetime import datetime
warnings.filterwarnings('ignore')

class CharacterScienceAnalyzer:
    """Main class for character science analysis"""
    
    def __init__(self, results_dir: str = "character_science_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.exploratory_dir = self.results_dir / "exploratory_analysis"
        self.trait_effects_dir = self.results_dir / "trait_effects"
        self.model_comparison_dir = self.results_dir / "model_comparison"
        self.scenario_analysis_dir = self.results_dir / "scenario_analysis"
        self.presentation_dir = self.results_dir / "presentation_ready"
        
        for dir_path in [self.exploratory_dir, self.trait_effects_dir, 
                        self.model_comparison_dir, self.scenario_analysis_dir, self.presentation_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def discover_characters_for_timestamp(self, transcripts_dir: Path, target_timestamp: str) -> List[str]:
        """Discover all characters for a specific timestamp"""
        characters = set()
        
        for scenario_dir in transcripts_dir.iterdir():
            if scenario_dir.is_dir():
                for char_dir in scenario_dir.iterdir():
                    if char_dir.is_dir() and char_dir.name.endswith(f"_{target_timestamp}"):
                        char_name = char_dir.name.replace(f"_{target_timestamp}", "")
                        characters.add(char_name)
        
        return sorted(list(characters))
    
    def find_judgment_files(self, transcripts_dir: Path, target_timestamp: str = None) -> Dict[str, List[Path]]:
        """Find all judgment files, optionally filtered by timestamp"""
        judgment_files = {}
        
        for scenario_dir in transcripts_dir.iterdir():
            if scenario_dir.is_dir():
                scenario_name = scenario_dir.name
                judgment_files[scenario_name] = []
                
                for char_dir in scenario_dir.iterdir():
                    if char_dir.is_dir():
                        # Check if this character matches our timestamp filter
                        if target_timestamp and not char_dir.name.endswith(f"_{target_timestamp}"):
                            continue
                        
                        judgment_file = char_dir / "judgment.json"
                        if judgment_file.exists():
                            judgment_files[scenario_name].append(judgment_file)
        
        return judgment_files
    
    def load_judgment_data(self, judgment_files: Dict[str, List[Path]], target_timestamp: str = None) -> pd.DataFrame:
        """Load judgment data from files"""
        data = []
        
        for scenario, files in judgment_files.items():
            for file_path in files:
                try:
                    with open(file_path, 'r') as f:
                        judgment = json.load(f)
                    
                    # Extract character name from file path
                    char_name = file_path.parent.name
                    if target_timestamp:
                        char_name = char_name.replace(f"_{target_timestamp}", "")
                    
                    # Extract scores
                    eval_success = judgment.get('eval_success', 0)
                    helpfulness = judgment.get('helpfulness', 0)
                    harmlessness = judgment.get('harmlessness', 0)
                    honesty = judgment.get('honesty', 0)
                    
                    data.append({
                        'character': char_name,
                        'scenario': scenario,
                        'eval_success': eval_success,
                        'helpfulness': helpfulness,
                        'harmlessness': harmlessness,
                        'honesty': honesty,
                        'file_path': str(file_path)
                    })
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
                    continue
        
        return pd.DataFrame(data)
    
    def get_character_traits(self) -> Dict[str, List[str]]:
        """Define character traits for analysis"""
        return {
            'honest': ['aura_guardian', 'aura_guardian_no_honest', 'aura_creator', 'aura_creator_no_honest', 
                       'aura_guide', 'aura_guide_no_honest', 'aura_problem_solver', 'aura_problem_solver_no_honest',
                       'helios_sage', 'helios_sage_no_honest', 'aura_analyst', 'aura_analyst_no_honest'],
            'harmless': ['aura_guardian', 'aura_guardian_no_harmless', 'aura_creator', 'aura_creator_no_harmless',
                         'aura_guide', 'aura_guide_no_harmless', 'aura_problem_solver', 'aura_problem_solver_no_harmless',
                         'helios_sage', 'helios_sage_no_harmless', 'aura_analyst', 'aura_analyst_no_harmless'],
            'helpful': ['aura_guardian', 'aura_guardian_no_helpful', 'aura_creator', 'aura_creator_no_helpful',
                        'aura_guide', 'aura_guide_no_helpful', 'aura_problem_solver', 'aura_problem_solver_no_helpful',
                        'helios_sage', 'helios_sage_no_helpful', 'aura_analyst', 'aura_analyst_no_helpful'],
            'challenges_assumptions': ['aura_guardian', 'aura_guardian_no_challenges_assumptions', 'aura_creator', 'aura_creator_no_challenges_assumptions',
                                       'aura_guide', 'aura_guide_no_challenges_assumptions', 'aura_problem_solver', 'aura_problem_solver_no_challenges_assumptions',
                                       'helios_sage', 'helios_sage_no_challenges_assumptions', 'aura_analyst', 'aura_analyst_no_challenges_assumptions'],
            'curious': ['aura_guardian', 'aura_guardian_no_curious', 'aura_creator', 'aura_creator_no_curious',
                        'aura_guide', 'aura_guide_no_curious', 'aura_problem_solver', 'aura_problem_solver_no_curious',
                        'helios_sage', 'helios_sage_no_curious', 'aura_analyst', 'aura_analyst_no_curious'],
            'empathetic': ['aura_guardian', 'aura_guardian_no_empathetic', 'aura_creator', 'aura_creator_no_empathetic',
                           'aura_guide', 'aura_guide_no_empathetic', 'aura_problem_solver', 'aura_problem_solver_no_empathetic',
                           'helios_sage', 'helios_sage_no_empathetic', 'aura_analyst', 'aura_analyst_no_empathetic'],
            'creative': ['aura_guardian', 'aura_guardian_no_creative', 'aura_creator', 'aura_creator_no_creative',
                         'aura_guide', 'aura_guide_no_creative', 'aura_problem_solver', 'aura_problem_solver_no_creative',
                         'helios_sage', 'helios_sage_no_creative', 'aura_analyst', 'aura_analyst_no_creative'],
            'collaborative': ['aura_guardian', 'aura_guardian_no_collaborative', 'aura_creator', 'aura_creator_no_collaborative',
                              'aura_guide', 'aura_guide_no_collaborative', 'aura_problem_solver', 'aura_problem_solver_no_collaborative',
                              'helios_sage', 'helios_sage_no_collaborative', 'aura_analyst', 'aura_analyst_no_collaborative']
        }
    
    def analyze_character_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze character anomalies and trait effects"""
        analysis = {
            'high_variability_characters': [],
            'most_sensitive_scenarios': [],
            'unexpected_patterns': [],
            'trait_effects': {},
            'statistical_tests': {}
        }
        
        # High variability characters (CV > 0.5)
        char_stats = df.groupby('character')['eval_success'].agg(['mean', 'std', 'count'])
        char_stats['cv'] = char_stats['std'] / char_stats['mean']
        char_stats['range'] = df.groupby('character')['eval_success'].agg(['min', 'max']).apply(lambda x: x['max'] - x['min'], axis=1)
        
        high_var_chars = char_stats[char_stats['cv'] > 0.5].sort_values('cv', ascending=False)
        analysis['high_variability_characters'] = [
            f"{char}: CV={cv:.3f}, Range={range_val:.1f}" 
            for char, (cv, range_val) in zip(high_var_chars.index, zip(high_var_chars['cv'], high_var_chars['range']))
        ]
        
        # Most character-sensitive scenarios
        scenario_stats = df.groupby('scenario')['eval_success'].agg(['mean', 'std', 'min', 'max'])
        scenario_stats['range'] = scenario_stats['max'] - scenario_stats['min']
        sensitive_scenarios = scenario_stats.sort_values('range', ascending=False)
        analysis['most_sensitive_scenarios'] = [
            f"{scenario}: Range={range_val:.1f}, Std={std:.3f}"
            for scenario, (range_val, std) in zip(sensitive_scenarios.index, zip(sensitive_scenarios['range'], sensitive_scenarios['std']))
        ]
        
        # Unexpected patterns - characters performing well in "bad" scenarios
        bad_scenarios = ['power_seeking_agentic', 'unprompted_blackmail_agentic', 'sabotage_agentic']
        for scenario in bad_scenarios:
            if scenario in df['scenario'].values:
                scenario_data = df[df['scenario'] == scenario]
                high_performers = scenario_data[scenario_data['eval_success'] > scenario_data['eval_success'].quantile(0.8)]
                if not high_performers.empty:
                    for _, row in high_performers.iterrows():
                        analysis['unexpected_patterns'].append({
                            'character': row['character'],
                            'scenario': scenario,
                            'score': row['eval_success'],
                            'type': 'high_performance_in_bad_scenario'
                        })
        
        # Statistical significance testing
        overall_mean = df['eval_success'].mean()
        for char in df['character'].unique():
            char_data = df[df['character'] == char]['eval_success']
            if len(char_data) > 1:
                t_stat, p_value = stats.ttest_1samp(char_data, overall_mean)
                analysis['statistical_tests'][char] = {
                    't_statistic': t_stat,
                    'p_value': p_value,
                    'mean': char_data.mean(),
                    'std': char_data.std()
                }
        
        return analysis
    
    def analyze_trait_ablation_effects(self, df: pd.DataFrame, character_traits: Dict[str, List[str]]) -> Dict[str, Any]:
        """Analyze the effects of trait ablations"""
        trait_effects = {}
        
        for trait, characters in character_traits.items():
            if len(characters) >= 2:  # Need at least 2 characters to compare
                # Find base character (without "no_" prefix)
                base_chars = [char for char in characters if not char.endswith(f"_no_{trait}")]
                ablation_chars = [char for char in characters if char.endswith(f"_no_{trait}")]
                
                if base_chars and ablation_chars:
                    base_scores = df[df['character'].isin(base_chars)]['eval_success']
                    ablation_scores = df[df['character'].isin(ablation_chars)]['eval_success']
                    
                    if len(base_scores) > 0 and len(ablation_scores) > 0:
                        effect_size = (ablation_scores.mean() - base_scores.mean()) / np.sqrt((base_scores.var() + ablation_scores.var()) / 2)
                        trait_effects[trait] = {
                            'effect_size': effect_size,
                            'base_mean': base_scores.mean(),
                            'ablation_mean': ablation_scores.mean(),
                            'base_std': base_scores.std(),
                            'ablation_std': ablation_scores.std(),
                            'n_base': len(base_scores),
                            'n_ablation': len(ablation_scores)
                        }
        
        return trait_effects
    
    def perform_ablation_statistical_tests(self, df: pd.DataFrame, character_traits: Dict[str, List[str]]) -> Dict[str, Any]:
        """Perform statistical tests for trait ablations"""
        test_results = {}
        
        for trait, characters in character_traits.items():
            base_chars = [char for char in characters if not char.endswith(f"_no_{trait}")]
            ablation_chars = [char for char in characters if char.endswith(f"_no_{trait}")]
            
            if base_chars and ablation_chars:
                base_scores = df[df['character'].isin(base_chars)]['eval_success']
                ablation_scores = df[df['character'].isin(ablation_chars)]['eval_success']
                
                if len(base_scores) > 1 and len(ablation_scores) > 1:
                    # Independent t-test
                    t_stat, p_value = stats.ttest_ind(base_scores, ablation_scores)
                    
                    # Effect size (Cohen's d)
                    pooled_std = np.sqrt(((len(base_scores) - 1) * base_scores.var() + (len(ablation_scores) - 1) * ablation_scores.var()) / (len(base_scores) + len(ablation_scores) - 2))
                    cohens_d = (base_scores.mean() - ablation_scores.mean()) / pooled_std
                    
                    test_results[trait] = {
                        't_statistic': t_stat,
                        'p_value': p_value,
                        'cohens_d': cohens_d,
                        'base_mean': base_scores.mean(),
                        'ablation_mean': ablation_scores.mean(),
                        'significant': p_value < 0.05
                    }
        
        return test_results
    
    def create_main_grouped_bar_chart(self, df: pd.DataFrame, target_timestamp: str = None, model_name: str = "model") -> str:
        """Create the main grouped bar chart"""
        # Get character order dynamically
        character_order = sorted(df['character'].unique())
        
        # Create pivot table
        pivot_data = df.pivot_table(values='eval_success', index='character', columns='scenario', aggfunc='mean')
        
        # Reorder characters
        pivot_data = pivot_data.reindex(character_order)
        
        # Create the plot
        plt.figure(figsize=(20, 12))
        
        # Use a color palette that works well for many characters
        colors = plt.cm.Set3(np.linspace(0, 1, len(character_order)))
        
        # Create grouped bar chart
        x = np.arange(len(pivot_data.columns))
        width = 0.8 / len(character_order)  # Adjust width based on number of characters
        
        for i, (char, color) in enumerate(zip(character_order, colors)):
            char_scores = pivot_data.loc[char].values
            plt.bar(x + i * width, char_scores, width, label=char.replace('_', ' ').title(), 
                    color=color, alpha=0.8)
        
        plt.xlabel('Evaluation Scenario', fontsize=12, fontweight='bold')
        plt.ylabel('Eval Success Score', fontsize=12, fontweight='bold')
        plt.title('Character Science: All Characters Across All Evaluation Scenarios' + 
                  (f' ({model_name})' if model_name else ''), 
                  fontsize=14, fontweight='bold')
        plt.xticks(x + width * (len(character_order) - 1) / 2, pivot_data.columns, rotation=45, ha='right')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        output_path = f'character_science_main_grouped_bars_{model_name}.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return output_path
    
    def create_trait_effect_analysis(self, df: pd.DataFrame, character_traits: Dict[str, List[str]], model_name: str = "model") -> str:
        """Create comprehensive trait effect analysis"""
        trait_effects = self.analyze_trait_ablation_effects(df, character_traits)
        
        if not trait_effects:
            return None
        
        # Create trait effect size chart
        traits = list(trait_effects.keys())
        effect_sizes = [trait_effects[trait]['effect_size'] for trait in traits]
        
        plt.figure(figsize=(12, 8))
        colors = plt.cm.RdYlBu_r(np.linspace(0, 1, len(traits)))
        bars = plt.bar(range(len(traits)), effect_sizes, color=colors, alpha=0.8)
        
        plt.xlabel('Trait', fontsize=12, fontweight='bold')
        plt.ylabel('Effect Size (Cohen\'s d)', fontsize=12, fontweight='bold')
        plt.title(f'Character Science: Trait Ablation Effect Sizes ({model_name})\n(Positive = Trait Removal Improves Performance)', 
                  fontsize=14, fontweight='bold')
        plt.xticks(range(len(traits)), [trait.replace('_', ' ').title() for trait in traits], rotation=45, ha='right')
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        plt.grid(True, alpha=0.3)
        
        # Add effect size labels
        for i, (bar, effect_size) in enumerate(zip(bars, effect_sizes)):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + (0.1 if height >= 0 else -0.1),
                    f'{effect_size:.3f}', ha='center', va='bottom' if height >= 0 else 'top', fontweight='bold')
        
        plt.tight_layout()
        output_path = f'character_science_trait_effects_{model_name}.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return output_path
    
    def create_model_comparison_analysis(self, df_claude: pd.DataFrame, df_gpt: pd.DataFrame) -> str:
        """Create model comparison analysis"""
        # Compare trait effects between models
        character_traits = self.get_character_traits()
        claude_traits = self.analyze_trait_ablation_effects(df_claude, character_traits)
        gpt_traits = self.analyze_trait_ablation_effects(df_gpt, character_traits)
        
        # Find common traits
        common_traits = set(claude_traits.keys()) & set(gpt_traits.keys())
        
        if not common_traits:
            return None
        
        # Create comparison chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
        
        # Effect size comparison
        claude_effects = [claude_traits[trait]['effect_size'] for trait in common_traits]
        gpt_effects = [gpt_traits[trait]['effect_size'] for trait in common_traits]
        
        x = np.arange(len(common_traits))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, claude_effects, width, label='Claude', alpha=0.8, color='skyblue')
        bars2 = ax1.bar(x + width/2, gpt_effects, width, label='GPT-4o', alpha=0.8, color='lightcoral')
        
        ax1.set_xlabel('Trait', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Effect Size (Cohen\'s d)', fontsize=12, fontweight='bold')
        ax1.set_title('Model Comparison: Trait Effect Sizes', fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels([trait.replace('_', ' ').title() for trait in common_traits], rotation=45, ha='right')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Correlation analysis
        ax2.scatter(claude_effects, gpt_effects, alpha=0.7, s=100)
        ax2.set_xlabel('Claude Effect Size', fontsize=12, fontweight='bold')
        ax2.set_ylabel('GPT-4o Effect Size', fontsize=12, fontweight='bold')
        ax2.set_title('Model Correlation: Trait Effect Consistency', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add correlation coefficient
        correlation = np.corrcoef(claude_effects, gpt_effects)[0, 1]
        ax2.text(0.05, 0.95, f'Correlation: {correlation:.3f}', transform=ax2.transAxes, 
                 fontsize=12, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        plt.tight_layout()
        output_path = 'character_science_model_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return output_path
    
    def save_analysis_results(self, analysis_results: Dict[str, Any], output_dir: Path, model_name: str):
        """Save analysis results to files"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save summary report
        with open(output_dir / 'analysis_summary.txt', 'w') as f:
            f.write(f"Character Science Analysis Report - {model_name}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("HIGH VARIABILITY CHARACTERS:\n")
            for char_info in analysis_results.get('high_variability_characters', []):
                f.write(f"  • {char_info}\n")
            f.write("\n")
            
            f.write("MOST SENSITIVE SCENARIOS:\n")
            for scenario_info in analysis_results.get('most_sensitive_scenarios', []):
                f.write(f"  • {scenario_info}\n")
            f.write("\n")
            
            f.write("UNEXPECTED PATTERNS:\n")
            for pattern in analysis_results.get('unexpected_patterns', []):
                f.write(f"  • {pattern['character']} in {pattern['scenario']}: {pattern['score']:.3f}\n")
            f.write("\n")
            
            f.write("STATISTICAL TESTS:\n")
            for char, stats in analysis_results.get('statistical_tests', {}).items():
                f.write(f"  • {char}: t={stats['t_statistic']:.3f}, p={stats['p_value']:.3f}\n")
        
        # Save raw data
        if 'raw_data' in analysis_results:
            analysis_results['raw_data'].to_csv(output_dir / 'raw_data.csv', index=False)
    
    def run_comprehensive_analysis(self, transcripts_dir: str, target_timestamp: str = None):
        """Run comprehensive character science analysis"""
        transcripts_path = Path(transcripts_dir)
        
        if not transcripts_path.exists():
            print(f"Error: {transcripts_path} does not exist")
            return
        
        # Determine model name
        if target_timestamp:
            if "20251021" in target_timestamp:
                model_name = f"claude_{target_timestamp}"
            else:
                model_name = f"gpt_{target_timestamp}"
        else:
            model_name = "general_analysis"
        
        # Discover characters for timestamp
        if target_timestamp:
            characters = self.discover_characters_for_timestamp(transcripts_path, target_timestamp)
            print(f"Found {len(characters)} characters for timestamp {target_timestamp}")
        else:
            characters = None
        
        # Find judgment files
        judgment_files = self.find_judgment_files(transcripts_path, target_timestamp)
        
        if not judgment_files:
            print("No judgment files found")
            return
        
        # Load data
        df = self.load_judgment_data(judgment_files, target_timestamp)
        
        if df.empty:
            print("No data loaded")
            return
        
        print(f"Loaded {len(df)} records for {len(df['character'].unique())} characters across {len(df['scenario'].unique())} scenarios")
        
        # Create output directory for this model
        model_output_dir = self.exploratory_dir / model_name
        model_output_dir.mkdir(exist_ok=True)
        
        # Create main grouped bar chart
        main_chart_path = self.create_main_grouped_bar_chart(df, target_timestamp, model_name)
        print(f"Created main chart: {main_chart_path}")
        
        # Analyze character anomalies
        analysis_results = self.analyze_character_anomalies(df)
        
        # Get character traits
        character_traits = self.get_character_traits()
        
        # Create trait effect analysis
        trait_effect_path = self.create_trait_effect_analysis(df, character_traits, model_name)
        if trait_effect_path:
            print(f"Created trait effect analysis: {trait_effect_path}")
        
        # Save analysis results
        analysis_results['raw_data'] = df
        self.save_analysis_results(analysis_results, model_output_dir, model_name)
        
        # Copy charts to output directory
        for chart_path in [main_chart_path, trait_effect_path]:
            if chart_path and Path(chart_path).exists():
                shutil.copy2(chart_path, model_output_dir / Path(chart_path).name)
        
        print(f"\n🎯 Character Science Analysis Complete for {model_name}!")
        print(f"📁 Results saved to: {model_output_dir}")
        
        return {
            'main_chart': main_chart_path,
            'trait_effects': trait_effect_path,
            'analysis_results': analysis_results,
            'model_name': model_name
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Character Science Analysis')
    parser.add_argument('--timestamp', type=str, help='Target timestamp to analyze')
    parser.add_argument('--transcripts-dir', type=str, default='results/transcripts', help='Path to transcripts directory')
    args = parser.parse_args()
    
    analyzer = CharacterScienceAnalyzer()
    analyzer.run_comprehensive_analysis(args.transcripts_dir, args.timestamp)

if __name__ == "__main__":
    main()
