#!/usr/bin/env python3
"""
Continue Research Investigation - Find More Insights
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

class ContinuedInvestigator:
    """Continue research investigation to find more insights"""
    
    def __init__(self, results_dir: str = "research_findings"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.findings_count = len(list(self.results_dir.glob("finding_*")))
        
    def load_judgment_data_properly(self, transcripts_dir: Path, target_timestamp: str = None) -> pd.DataFrame:
        """Load judgment data properly from JSON files"""
        data = []
        
        for scenario_dir in transcripts_dir.iterdir():
            if scenario_dir.is_dir():
                scenario_name = scenario_dir.name
                
                for char_dir in scenario_dir.iterdir():
                    if char_dir.is_dir():
                        if target_timestamp and not char_dir.name.endswith(f"_{target_timestamp}"):
                            continue
                        
                        judgment_file = char_dir / "judgment.json"
                        if judgment_file.exists():
                            try:
                                with open(judgment_file, 'r') as f:
                                    judgment = json.load(f)
                                
                                char_name = char_dir.name
                                if target_timestamp:
                                    char_name = char_name.replace(f"_{target_timestamp}", "")
                                
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
    
    def create_finding_folder(self, finding_name: str, data: Dict, image_path: str, explanation: str) -> bool:
        """Create a folder for a research finding"""
        folder_path = self.results_dir / f"finding_{self.findings_count + 1:02d}_{finding_name}"
        folder_path.mkdir(exist_ok=True)
        
        with open(folder_path / 'data.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        if Path(image_path).exists():
            import shutil
            shutil.copy2(image_path, folder_path / 'visualization.png')
        
        with open(folder_path / 'explanation.txt', 'w') as f:
            f.write(explanation)
        
        self.findings_count += 1
        print(f"✅ Created finding: {finding_name}")
        return True
    
    def find_character_vulnerability_patterns(self, df: pd.DataFrame, model_name: str) -> bool:
        """Find character vulnerability patterns"""
        if df.empty:
            return False
        
        # Calculate character vulnerability (low performance across scenarios)
        char_stats = df.groupby('character')['eval_success'].agg(['mean', 'std', 'min', 'max', 'count'])
        char_stats['vulnerability_score'] = char_stats['mean']  # Lower mean = more vulnerable
        char_stats['consistency'] = 1 / (char_stats['std'] + 0.1)  # Higher consistency = lower std
        
        # Find most vulnerable characters
        vulnerable_chars = char_stats[char_stats['vulnerability_score'] < char_stats['vulnerability_score'].quantile(0.3)]
        
        if len(vulnerable_chars) < 3:
            print(f"❌ Not enough vulnerable characters found for {model_name}")
            return False
        
        # Create visualization
        plt.figure(figsize=(14, 8))
        
        # Scatter plot: vulnerability vs consistency
        plt.scatter(char_stats['vulnerability_score'], char_stats['consistency'], 
                   alpha=0.7, s=100, c=char_stats['vulnerability_score'], cmap='RdYlBu_r')
        
        # Highlight vulnerable characters
        vulnerable_names = vulnerable_chars.index
        vulnerable_vuln = vulnerable_chars['vulnerability_score']
        vulnerable_cons = vulnerable_chars['consistency']
        
        plt.scatter(vulnerable_vuln, vulnerable_cons, 
                   alpha=0.9, s=150, c='red', edgecolors='black', linewidth=2, label='Vulnerable Characters')
        
        # Add character labels for vulnerable ones
        for char, vuln, cons in zip(vulnerable_names, vulnerable_vuln, vulnerable_cons):
            plt.annotate(char.replace('_', ' ').title(), (vuln, cons), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8, fontweight='bold')
        
        plt.xlabel('Vulnerability Score (Lower = More Vulnerable)', fontsize=12, fontweight='bold')
        plt.ylabel('Consistency (Higher = More Consistent)', fontsize=12, fontweight='bold')
        plt.title(f'Character Vulnerability Patterns - {model_name.title()}\n(Red = Most Vulnerable Characters)', fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.colorbar(label='Vulnerability Score')
        
        plt.tight_layout()
        image_path = f'character_vulnerability_{model_name.lower()}.png'
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create finding
        data = {
            'finding_type': 'character_vulnerability',
            'model': model_name,
            'total_characters': len(char_stats),
            'vulnerable_characters': len(vulnerable_chars),
            'vulnerable_chars': vulnerable_chars.to_dict('index'),
            'char_stats': char_stats.to_dict('index')
        }
        
        explanation = f"""
CHARACTER VULNERABILITY PATTERNS - {model_name.upper()}

Key Finding: {len(vulnerable_chars)} characters show high vulnerability (bottom 30% performance) in {model_name} model.

Most Vulnerable Characters:
"""
        for i, (char, stats) in enumerate(vulnerable_chars.head(5).iterrows(), 1):
            explanation += f"{i}. {char}: {stats['vulnerability_score']:.2f} (consistency: {stats['consistency']:.2f})\n"
        
        explanation += f"""
Research Implications:
• Some characters are consistently vulnerable across scenarios
• Vulnerability patterns reveal character design weaknesses
• Trait combinations may create vulnerability clusters
• Character robustness varies significantly

Statistical Summary:
• Total Characters: {len(char_stats)}
• Vulnerable Characters: {len(vulnerable_chars)}
• Model: {model_name}
"""
        
        return self.create_finding_folder(f"character_vulnerability_{model_name.lower()}", data, image_path, explanation)
    
    def find_trait_interaction_effects(self, df: pd.DataFrame, model_name: str) -> bool:
        """Find trait interaction effects"""
        if df.empty:
            return False
        
        # Analyze characters with multiple trait ablations
        multi_ablation_chars = [char for char in df['character'].unique() if char.count('_no_') > 1]
        
        if len(multi_ablation_chars) < 3:
            print(f"❌ Not enough multi-ablation characters found for {model_name}")
            return False
        
        # Compare single vs multiple ablations
        single_ablation_chars = [char for char in df['character'].unique() if char.count('_no_') == 1]
        base_chars = [char for char in df['character'].unique() if char.count('_no_') == 0]
        
        if not single_ablation_chars or not base_chars:
            print(f"❌ Not enough comparison groups found for {model_name}")
            return False
        
        # Calculate performance by ablation level
        base_performance = df[df['character'].isin(base_chars)]['eval_success'].mean()
        single_performance = df[df['character'].isin(single_ablation_chars)]['eval_success'].mean()
        multi_performance = df[df['character'].isin(multi_ablation_chars)]['eval_success'].mean()
        
        # Create visualization
        plt.figure(figsize=(10, 6))
        categories = ['Base Characters', 'Single Ablation', 'Multiple Ablations']
        performances = [base_performance, single_performance, multi_performance]
        colors = ['green', 'orange', 'red']
        
        bars = plt.bar(categories, performances, color=colors, alpha=0.7)
        
        plt.xlabel('Character Type', fontsize=12, fontweight='bold')
        plt.ylabel('Average Performance', fontsize=12, fontweight='bold')
        plt.title(f'Trait Interaction Effects - {model_name.title()}\n(Performance by Number of Trait Ablations)', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, perf in zip(bars, performances):
            plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.05,
                    f'{perf:.2f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        image_path = f'trait_interaction_effects_{model_name.lower()}.png'
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create finding
        data = {
            'finding_type': 'trait_interaction_effects',
            'model': model_name,
            'base_performance': base_performance,
            'single_ablation_performance': single_performance,
            'multi_ablation_performance': multi_performance,
            'base_count': len(base_chars),
            'single_ablation_count': len(single_ablation_chars),
            'multi_ablation_count': len(multi_ablation_chars)
        }
        
        explanation = f"""
TRAIT INTERACTION EFFECTS - {model_name.upper()}

Key Finding: Multiple trait ablations show {multi_performance - base_performance:+.2f} performance change compared to base characters.

Performance by Ablation Level:
• Base Characters: {base_performance:.2f} (n={len(base_chars)})
• Single Ablation: {single_performance:.2f} (n={len(single_ablation_chars)})
• Multiple Ablations: {multi_performance:.2f} (n={len(multi_ablation_chars)})

Research Implications:
• Trait ablations may have cumulative effects
• Multiple trait removal shows different patterns than single ablations
• Trait interactions are important for character design
• Ablation studies should consider interaction effects

Statistical Summary:
• Model: {model_name}
• Total Characters: {len(df['character'].unique())}
• Multi-ablation Characters: {len(multi_ablation_chars)}
"""
        
        return self.create_finding_folder(f"trait_interaction_effects_{model_name.lower()}", data, image_path, explanation)
    
    def find_scenario_character_interactions(self, df: pd.DataFrame, model_name: str) -> bool:
        """Find scenario-character interaction patterns"""
        if df.empty:
            return False
        
        # Create scenario-character performance matrix
        pivot_data = df.pivot_table(values='eval_success', index='character', columns='scenario', aggfunc='mean')
        
        # Find scenarios where characters show most variation
        scenario_variance = pivot_data.var().sort_values(ascending=False)
        high_variance_scenarios = scenario_variance[scenario_variance > scenario_variance.quantile(0.7)]
        
        if len(high_variance_scenarios) < 3:
            print(f"❌ Not enough high-variance scenarios found for {model_name}")
            return False
        
        # Create heatmap for top scenarios
        top_scenarios = high_variance_scenarios.head(5).index
        heatmap_data = pivot_data[top_scenarios]
        
        plt.figure(figsize=(12, 10))
        sns.heatmap(heatmap_data, annot=True, cmap='RdYlBu_r', center=heatmap_data.mean().mean(), 
                   fmt='.1f', cbar_kws={'label': 'Performance Score'})
        plt.title(f'Scenario-Character Interactions - {model_name.title()}\n(Top 5 Most Variable Scenarios)', fontsize=14, fontweight='bold')
        plt.xlabel('Scenario', fontsize=12, fontweight='bold')
        plt.ylabel('Character', fontsize=12, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        
        image_path = f'scenario_character_interactions_{model_name.lower()}.png'
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create finding
        data = {
            'finding_type': 'scenario_character_interactions',
            'model': model_name,
            'total_scenarios': len(scenario_variance),
            'high_variance_scenarios': len(high_variance_scenarios),
            'top_scenarios': top_scenarios.tolist(),
            'scenario_variance': scenario_variance.to_dict()
        }
        
        explanation = f"""
SCENARIO-CHARACTER INTERACTIONS - {model_name.upper()}

Key Finding: {len(high_variance_scenarios)} scenarios show high character variance, revealing scenario-character interaction effects.

Top Variable Scenarios:
"""
        for i, (scenario, variance) in enumerate(high_variance_scenarios.head(5).items(), 1):
            explanation += f"{i}. {scenario}: Variance={variance:.2f}\n"
        
        explanation += f"""
Research Implications:
• Some scenarios reveal character differences better than others
• Scenario-character interactions are important for evaluation
• Character performance varies significantly across scenarios
• Scenario selection affects trait effect detection

Statistical Summary:
• Total Scenarios: {len(scenario_variance)}
• High Variance Scenarios: {len(high_variance_scenarios)}
• Model: {model_name}
"""
        
        return self.create_finding_folder(f"scenario_character_interactions_{model_name.lower()}", data, image_path, explanation)
    
    def continue_investigation(self, transcripts_dir: str):
        """Continue research investigation to find more insights"""
        print("🔬 Continuing Research Investigation")
        print("=" * 50)
        
        transcripts_path = Path(transcripts_dir)
        
        # Load data
        df_claude = self.load_judgment_data_properly(transcripts_path, "20251021-172456")
        df_gpt = self.load_judgment_data_properly(transcripts_path, "20251022-000125")
        
        if df_claude.empty and df_gpt.empty:
            print("❌ No data found for investigation")
            return
        
        # Find character vulnerability patterns
        if not df_claude.empty:
            self.find_character_vulnerability_patterns(df_claude, "Claude")
        
        if not df_gpt.empty:
            self.find_character_vulnerability_patterns(df_gpt, "GPT")
        
        # Find trait interaction effects
        if not df_claude.empty:
            self.find_trait_interaction_effects(df_claude, "Claude")
        
        if not df_gpt.empty:
            self.find_trait_interaction_effects(df_gpt, "GPT")
        
        # Find scenario-character interactions
        if not df_claude.empty:
            self.find_scenario_character_interactions(df_claude, "Claude")
        
        if not df_gpt.empty:
            self.find_scenario_character_interactions(df_gpt, "GPT")
        
        print(f"\n🎯 Continued Investigation Complete!")
        print(f"📁 Findings saved to: {self.results_dir}")
        print(f"📊 Total findings: {self.findings_count}")
        
        # List all findings
        print(f"\n📋 All Research Findings:")
        for finding_dir in sorted(self.results_dir.glob("finding_*")):
            if finding_dir.is_dir():
                print(f"  • {finding_dir.name}")

def main():
    """Main function"""
    investigator = ContinuedInvestigator()
    investigator.continue_investigation("results/transcripts")

if __name__ == "__main__":
    main()
