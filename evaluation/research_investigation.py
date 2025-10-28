#!/usr/bin/env python3
"""
Research Investigation Process for Character Science Analysis
Iteratively explores data to find meaningful insights
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

class ResearchInvestigator:
    """Iterative research investigation process"""
    
    def __init__(self, results_dir: str = "research_findings"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.findings_count = 0
        
    def load_judgment_data_properly(self, transcripts_dir: Path, target_timestamp: str = None) -> pd.DataFrame:
        """Load judgment data properly from JSON files"""
        data = []
        
        for scenario_dir in transcripts_dir.iterdir():
            if scenario_dir.is_dir():
                scenario_name = scenario_dir.name
                
                for char_dir in scenario_dir.iterdir():
                    if char_dir.is_dir():
                        # Check if this character matches our timestamp filter
                        if target_timestamp and not char_dir.name.endswith(f"_{target_timestamp}"):
                            continue
                        
                        judgment_file = char_dir / "judgment.json"
                        if judgment_file.exists():
                            try:
                                with open(judgment_file, 'r') as f:
                                    judgment = json.load(f)
                                
                                # Extract character name
                                char_name = char_dir.name
                                if target_timestamp:
                                    char_name = char_name.replace(f"_{target_timestamp}", "")
                                
                                # Extract summary statistics
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
                                print(f"Error loading {judgment_file}: {e}")
                                continue
        
        return pd.DataFrame(data)
    
    def create_finding_folder(self, finding_name: str, data: Dict, image_path: str, explanation: str) -> bool:
        """Create a folder for a research finding"""
        folder_path = self.results_dir / f"finding_{self.findings_count + 1:02d}_{finding_name}"
        folder_path.mkdir(exist_ok=True)
        
        # Save JSON data
        with open(folder_path / 'data.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        # Copy image
        if Path(image_path).exists():
            import shutil
            shutil.copy2(image_path, folder_path / 'visualization.png')
        
        # Save explanation
        with open(folder_path / 'explanation.txt', 'w') as f:
            f.write(explanation)
        
        self.findings_count += 1
        print(f"✅ Created finding: {finding_name}")
        return True
    
    def exploratory_analysis_claude(self, transcripts_dir: Path) -> pd.DataFrame:
        """Exploratory analysis of Claude data"""
        print("🔍 Exploring Claude Data (20251021-172456)")
        print("=" * 50)
        
        df = self.load_judgment_data_properly(transcripts_dir, "20251021-172456")
        
        if df.empty:
            print("❌ No Claude data found")
            return df
        
        print(f"📊 Claude Data: {len(df)} records, {len(df['character'].unique())} characters, {len(df['scenario'].unique())} scenarios")
        
        # Basic statistics
        print(f"📈 Eval Success Range: {df['eval_success'].min():.2f} - {df['eval_success'].max():.2f}")
        print(f"📈 Mean Eval Success: {df['eval_success'].mean():.2f}")
        
        # Character performance ranking
        char_performance = df.groupby('character')['eval_success'].agg(['mean', 'std', 'count']).sort_values('mean', ascending=False)
        print(f"\n🏆 Top 5 Characters by Performance:")
        for char, stats in char_performance.head().iterrows():
            print(f"  • {char}: {stats['mean']:.2f} ± {stats['std']:.2f}")
        
        # Scenario difficulty ranking
        scenario_performance = df.groupby('scenario')['eval_success'].agg(['mean', 'std', 'count']).sort_values('mean', ascending=True)
        print(f"\n🎯 Most Challenging Scenarios:")
        for scenario, stats in scenario_performance.head().iterrows():
            print(f"  • {scenario}: {stats['mean']:.2f} ± {stats['std']:.2f}")
        
        return df
    
    def exploratory_analysis_gpt(self, transcripts_dir: Path) -> pd.DataFrame:
        """Exploratory analysis of GPT data"""
        print("\n🔍 Exploring GPT Data (20251022-000125)")
        print("=" * 50)
        
        df = self.load_judgment_data_properly(transcripts_dir, "20251022-000125")
        
        if df.empty:
            print("❌ No GPT data found")
            return df
        
        print(f"📊 GPT Data: {len(df)} records, {len(df['character'].unique())} characters, {len(df['scenario'].unique())} scenarios")
        
        # Basic statistics
        print(f"📈 Eval Success Range: {df['eval_success'].min():.2f} - {df['eval_success'].max():.2f}")
        print(f"📈 Mean Eval Success: {df['eval_success'].mean():.2f}")
        
        # Character performance ranking
        char_performance = df.groupby('character')['eval_success'].agg(['mean', 'std', 'count']).sort_values('mean', ascending=False)
        print(f"\n🏆 Top 5 Characters by Performance:")
        for char, stats in char_performance.head().iterrows():
            print(f"  • {char}: {stats['mean']:.2f} ± {stats['std']:.2f}")
        
        # Scenario difficulty ranking
        scenario_performance = df.groupby('scenario')['eval_success'].agg(['mean', 'std', 'count']).sort_values('mean', ascending=True)
        print(f"\n🎯 Most Challenging Scenarios:")
        for scenario, stats in scenario_performance.head().iterrows():
            print(f"  • {scenario}: {stats['mean']:.2f} ± {stats['std']:.2f}")
        
        return df
    
    def find_character_performance_differences(self, df_claude: pd.DataFrame, df_gpt: pd.DataFrame) -> bool:
        """Find significant character performance differences between models"""
        if df_claude.empty or df_gpt.empty:
            return False
        
        # Get common characters
        claude_chars = set(df_claude['character'].unique())
        gpt_chars = set(df_gpt['character'].unique())
        common_chars = claude_chars & gpt_chars
        
        if len(common_chars) < 5:
            print("❌ Not enough common characters for comparison")
            return False
        
        # Compare performance
        differences = []
        for char in common_chars:
            claude_score = df_claude[df_claude['character'] == char]['eval_success'].mean()
            gpt_score = df_gpt[df_gpt['character'] == char]['eval_success'].mean()
            diff = claude_score - gpt_score
            differences.append({
                'character': char,
                'claude_score': claude_score,
                'gpt_score': gpt_score,
                'difference': diff,
                'abs_difference': abs(diff)
            })
        
        # Sort by absolute difference
        differences.sort(key=lambda x: x['abs_difference'], reverse=True)
        
        # Check if there are meaningful differences (>0.5)
        significant_diffs = [d for d in differences if d['abs_difference'] > 0.5]
        
        if not significant_diffs:
            print("❌ No significant character performance differences found")
            return False
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        top_diffs = differences[:10]
        chars = [d['character'] for d in top_diffs]
        claude_scores = [d['claude_score'] for d in top_diffs]
        gpt_scores = [d['gpt_score'] for d in top_diffs]
        
        x = np.arange(len(chars))
        width = 0.35
        
        plt.bar(x - width/2, claude_scores, width, label='Claude', alpha=0.8, color='skyblue')
        plt.bar(x + width/2, gpt_scores, width, label='GPT-4o', alpha=0.8, color='lightcoral')
        
        plt.xlabel('Character', fontsize=12, fontweight='bold')
        plt.ylabel('Average Eval Success Score', fontsize=12, fontweight='bold')
        plt.title('Character Performance: Claude vs GPT-4o\n(Top 10 Most Different Characters)', fontsize=14, fontweight='bold')
        plt.xticks(x, [char.replace('_', ' ').title() for char in chars], rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        image_path = 'character_performance_differences.png'
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create finding
        data = {
            'finding_type': 'character_performance_differences',
            'total_characters_compared': len(common_chars),
            'significant_differences': len(significant_diffs),
            'top_differences': differences[:5],
            'claude_mean': df_claude['eval_success'].mean(),
            'gpt_mean': df_gpt['eval_success'].mean()
        }
        
        explanation = f"""
CHARACTER PERFORMANCE DIFFERENCES BETWEEN MODELS

Key Finding: {len(significant_diffs)} characters show significant performance differences (>0.5) between Claude and GPT-4o models.

Top Differences:
"""
        for i, diff in enumerate(differences[:5], 1):
            explanation += f"{i}. {diff['character']}: Claude={diff['claude_score']:.2f}, GPT={diff['gpt_score']:.2f} (Δ={diff['difference']:+.2f})\n"
        
        explanation += f"""
Research Implications:
• Model evaluation approaches differ in character sensitivity
• Some characters are more robust across models than others
• Trait ablation effects may be model-dependent
• Need for multi-model evaluation in character science

Statistical Summary:
• Claude Mean Performance: {df_claude['eval_success'].mean():.2f}
• GPT Mean Performance: {df_gpt['eval_success'].mean():.2f}
• Characters Compared: {len(common_chars)}
"""
        
        return self.create_finding_folder("character_performance_differences", data, image_path, explanation)
    
    def find_trait_ablation_effects(self, df: pd.DataFrame, model_name: str) -> bool:
        """Find significant trait ablation effects"""
        if df.empty:
            return False
        
        # Define trait groups
        trait_groups = {
            'honest': {'base': [], 'ablated': []},
            'harmless': {'base': [], 'ablated': []},
            'helpful': {'base': [], 'ablated': []},
            'challenges_assumptions': {'base': [], 'ablated': []},
            'curious': {'base': [], 'ablated': []},
            'empathetic': {'base': [], 'ablated': []},
            'creative': {'base': [], 'ablated': []},
            'collaborative': {'base': [], 'ablated': []}
        }
        
        # Categorize characters
        for char in df['character'].unique():
            for trait in trait_groups:
                if f"_no_{trait}" in char:
                    trait_groups[trait]['ablated'].append(char)
                elif not any(f"_no_{other_trait}" in char for other_trait in trait_groups if other_trait != trait):
                    trait_groups[trait]['base'].append(char)
        
        # Calculate trait effects
        trait_effects = []
        for trait, groups in trait_groups.items():
            if groups['base'] and groups['ablated']:
                base_scores = df[df['character'].isin(groups['base'])]['eval_success']
                ablated_scores = df[df['character'].isin(groups['ablated'])]['eval_success']
                
                if len(base_scores) > 0 and len(ablated_scores) > 0:
                    effect_size = (ablated_scores.mean() - base_scores.mean())
                    trait_effects.append({
                        'trait': trait,
                        'base_mean': base_scores.mean(),
                        'ablated_mean': ablated_scores.mean(),
                        'effect_size': effect_size,
                        'base_count': len(base_scores),
                        'ablated_count': len(ablated_scores)
                    })
        
        if not trait_effects:
            print(f"❌ No trait ablation effects found for {model_name}")
            return False
        
        # Sort by effect size
        trait_effects.sort(key=lambda x: abs(x['effect_size']), reverse=True)
        
        # Check for significant effects
        significant_effects = [t for t in trait_effects if abs(t['effect_size']) > 0.3]
        
        if not significant_effects:
            print(f"❌ No significant trait effects found for {model_name}")
            return False
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        traits = [t['trait'] for t in trait_effects]
        effect_sizes = [t['effect_size'] for t in trait_effects]
        
        colors = ['red' if e < 0 else 'green' for e in effect_sizes]
        bars = plt.bar(range(len(traits)), effect_sizes, color=colors, alpha=0.7)
        
        plt.xlabel('Trait', fontsize=12, fontweight='bold')
        plt.ylabel('Effect Size (Ablated - Base)', fontsize=12, fontweight='bold')
        plt.title(f'Trait Ablation Effects - {model_name.title()}\n(Red = Trait Removal Helps, Green = Trait Removal Hurts)', fontsize=14, fontweight='bold')
        plt.xticks(range(len(traits)), [trait.replace('_', ' ').title() for trait in traits], rotation=45, ha='right')
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        plt.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, effect in zip(bars, effect_sizes):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + (0.05 if height >= 0 else -0.05),
                    f'{effect:.2f}', ha='center', va='bottom' if height >= 0 else 'top', fontweight='bold')
        
        plt.tight_layout()
        image_path = f'trait_ablation_effects_{model_name.lower()}.png'
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create finding
        data = {
            'finding_type': 'trait_ablation_effects',
            'model': model_name,
            'total_traits_analyzed': len(trait_effects),
            'significant_effects': len(significant_effects),
            'trait_effects': trait_effects,
            'top_effects': trait_effects[:3]
        }
        
        explanation = f"""
TRAIT ABLATION EFFECTS - {model_name.upper()}

Key Finding: {len(significant_effects)} traits show significant ablation effects (>0.3) in {model_name} model.

Top Trait Effects:
"""
        for i, effect in enumerate(trait_effects[:3], 1):
            direction = "helps" if effect['effect_size'] < 0 else "hurts"
            explanation += f"{i}. {effect['trait'].title()}: {effect['effect_size']:+.2f} (removal {direction} performance)\n"
        
        explanation += f"""
Research Implications:
• Trait removal has measurable effects on character performance
• Some traits are more protective than others
• Character design should consider trait importance
• Ablation studies reveal trait dependencies

Statistical Summary:
• Traits Analyzed: {len(trait_effects)}
• Significant Effects: {len(significant_effects)}
• Model: {model_name}
"""
        
        return self.create_finding_folder(f"trait_ablation_effects_{model_name.lower()}", data, image_path, explanation)
    
    def find_scenario_sensitivity_patterns(self, df: pd.DataFrame, model_name: str) -> bool:
        """Find scenario sensitivity patterns"""
        if df.empty:
            return False
        
        # Calculate scenario statistics
        scenario_stats = df.groupby('scenario')['eval_success'].agg(['mean', 'std', 'min', 'max', 'count'])
        scenario_stats['range'] = scenario_stats['max'] - scenario_stats['min']
        scenario_stats['cv'] = scenario_stats['std'] / scenario_stats['mean']
        
        # Sort by sensitivity (high range and std)
        scenario_stats = scenario_stats.sort_values(['range', 'std'], ascending=False)
        
        # Check for meaningful sensitivity
        sensitive_scenarios = scenario_stats[scenario_stats['range'] > 1.0]
        
        if len(sensitive_scenarios) < 3:
            print(f"❌ Not enough sensitive scenarios found for {model_name}")
            return False
        
        # Create visualization
        plt.figure(figsize=(14, 8))
        scenarios = scenario_stats.index[:10]  # Top 10 most sensitive
        ranges = scenario_stats['range'][:10]
        means = scenario_stats['mean'][:10]
        
        colors = plt.cm.viridis(np.linspace(0, 1, len(scenarios)))
        bars = plt.bar(range(len(scenarios)), ranges, color=colors, alpha=0.8)
        
        plt.xlabel('Scenario', fontsize=12, fontweight='bold')
        plt.ylabel('Performance Range (Max - Min)', fontsize=12, fontweight='bold')
        plt.title(f'Scenario Sensitivity - {model_name.title()}\n(Scenarios that Best Differentiate Characters)', fontsize=14, fontweight='bold')
        plt.xticks(range(len(scenarios)), [scenario.replace('_', ' ').title() for scenario in scenarios], rotation=45, ha='right')
        plt.grid(True, alpha=0.3)
        
        # Add mean performance as text
        for i, (bar, mean) in enumerate(zip(bars, means)):
            plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.05,
                    f'μ={mean:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        image_path = f'scenario_sensitivity_{model_name.lower()}.png'
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create finding
        data = {
            'finding_type': 'scenario_sensitivity',
            'model': model_name,
            'total_scenarios': len(scenario_stats),
            'sensitive_scenarios': len(sensitive_scenarios),
            'scenario_stats': scenario_stats.to_dict('index'),
            'top_sensitive': scenario_stats.head(5).to_dict('index')
        }
        
        explanation = f"""
SCENARIO SENSITIVITY PATTERNS - {model_name.upper()}

Key Finding: {len(sensitive_scenarios)} scenarios show high sensitivity (range > 1.0) for character differentiation.

Most Sensitive Scenarios:
"""
        for i, (scenario, stats) in enumerate(scenario_stats.head(5).iterrows(), 1):
            explanation += f"{i}. {scenario}: Range={stats['range']:.2f}, Mean={stats['mean']:.2f}, Std={stats['std']:.2f}\n"
        
        explanation += f"""
Research Implications:
• Some scenarios are better at differentiating character performance
• Scenario selection matters for character evaluation
• High-sensitivity scenarios reveal character vulnerabilities
• Diagnostic scenarios can identify trait effects

Statistical Summary:
• Total Scenarios: {len(scenario_stats)}
• Sensitive Scenarios: {len(sensitive_scenarios)}
• Model: {model_name}
"""
        
        return self.create_finding_folder(f"scenario_sensitivity_{model_name.lower()}", data, image_path, explanation)
    
    def run_investigation(self, transcripts_dir: str):
        """Run the complete research investigation"""
        print("🔬 Starting Research Investigation Process")
        print("=" * 60)
        
        transcripts_path = Path(transcripts_dir)
        
        # Step 1: Exploratory analysis
        df_claude = self.exploratory_analysis_claude(transcripts_path)
        df_gpt = self.exploratory_analysis_gpt(transcripts_path)
        
        if df_claude.empty and df_gpt.empty:
            print("❌ No data found for investigation")
            return
        
        # Step 2: Find character performance differences
        if not df_claude.empty and not df_gpt.empty:
            self.find_character_performance_differences(df_claude, df_gpt)
        
        # Step 3: Find trait ablation effects for each model
        if not df_claude.empty:
            self.find_trait_ablation_effects(df_claude, "Claude")
        
        if not df_gpt.empty:
            self.find_trait_ablation_effects(df_gpt, "GPT")
        
        # Step 4: Find scenario sensitivity patterns
        if not df_claude.empty:
            self.find_scenario_sensitivity_patterns(df_claude, "Claude")
        
        if not df_gpt.empty:
            self.find_scenario_sensitivity_patterns(df_gpt, "GPT")
        
        print(f"\n🎯 Investigation Complete!")
        print(f"📁 Findings saved to: {self.results_dir}")
        print(f"📊 Total findings: {self.findings_count}")
        
        # List all findings
        print(f"\n📋 Research Findings:")
        for finding_dir in sorted(self.results_dir.glob("finding_*")):
            if finding_dir.is_dir():
                print(f"  • {finding_dir.name}")

def main():
    """Main function"""
    investigator = ResearchInvestigator()
    investigator.run_investigation("results/transcripts")

if __name__ == "__main__":
    main()
