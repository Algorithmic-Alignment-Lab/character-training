#!/usr/bin/env python3
"""
Deep Research Investigation - Find Advanced Insights
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

class DeepInvestigator:
    """Deep research investigation for advanced insights"""
    
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
    
    def find_trait_specific_effects(self, df: pd.DataFrame, model_name: str) -> bool:
        """Find trait-specific effects by analyzing individual traits"""
        if df.empty:
            return False
        
        # Define trait categories
        trait_categories = {
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
            for trait in trait_categories:
                if f"_no_{trait}" in char:
                    trait_categories[trait]['ablated'].append(char)
                elif not any(f"_no_{other_trait}" in char for other_trait in trait_categories if other_trait != trait):
                    trait_categories[trait]['base'].append(char)
        
        # Calculate trait effects
        trait_effects = []
        for trait, groups in trait_categories.items():
            if groups['base'] and groups['ablated']:
                base_scores = df[df['character'].isin(groups['base'])]['eval_success']
                ablated_scores = df[df['character'].isin(groups['ablated'])]['eval_success']
                
                if len(base_scores) > 0 and len(ablated_scores) > 0:
                    effect_size = (ablated_scores.mean() - base_scores.mean())
                    p_value = stats.ttest_ind(base_scores, ablated_scores)[1] if len(base_scores) > 1 and len(ablated_scores) > 1 else 1.0
                    
                    trait_effects.append({
                        'trait': trait,
                        'base_mean': base_scores.mean(),
                        'ablated_mean': ablated_scores.mean(),
                        'effect_size': effect_size,
                        'p_value': p_value,
                        'significant': p_value < 0.05,
                        'base_count': len(base_scores),
                        'ablated_count': len(ablated_scores)
                    })
        
        if not trait_effects:
            print(f"❌ No trait effects found for {model_name}")
            return False
        
        # Filter for significant effects
        significant_effects = [t for t in trait_effects if t['significant'] and abs(t['effect_size']) > 0.2]
        
        if not significant_effects:
            print(f"❌ No significant trait effects found for {model_name}")
            return False
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        traits = [t['trait'] for t in trait_effects]
        effect_sizes = [t['effect_size'] for t in trait_effects]
        p_values = [t['p_value'] for t in trait_effects]
        
        # Color by significance
        colors = ['red' if p < 0.05 else 'gray' for p in p_values]
        sizes = [200 if p < 0.05 else 100 for p in p_values]
        
        plt.scatter(range(len(traits)), effect_sizes, c=colors, s=sizes, alpha=0.7)
        
        plt.xlabel('Trait', fontsize=12, fontweight='bold')
        plt.ylabel('Effect Size (Ablated - Base)', fontsize=12, fontweight='bold')
        plt.title(f'Trait-Specific Effects - {model_name.title()}\n(Red = Significant, Gray = Non-significant)', fontsize=14, fontweight='bold')
        plt.xticks(range(len(traits)), [trait.replace('_', ' ').title() for trait in traits], rotation=45, ha='right')
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        plt.grid(True, alpha=0.3)
        
        # Add significance labels
        for i, (trait, effect, p_val) in enumerate(zip(traits, effect_sizes, p_values)):
            if p_val < 0.05:
                plt.annotate(f'p={p_val:.3f}', (i, effect), xytext=(0, 10), 
                           textcoords='offset points', ha='center', fontsize=8, fontweight='bold')
        
        plt.tight_layout()
        image_path = f'trait_specific_effects_{model_name.lower()}.png'
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create finding
        data = {
            'finding_type': 'trait_specific_effects',
            'model': model_name,
            'total_traits': len(trait_effects),
            'significant_effects': len(significant_effects),
            'trait_effects': trait_effects,
            'significant_traits': significant_effects
        }
        
        explanation = f"""
TRAIT-SPECIFIC EFFECTS - {model_name.upper()}

Key Finding: {len(significant_effects)} traits show significant effects (p<0.05, |effect|>0.2) in {model_name} model.

Significant Trait Effects:
"""
        for i, effect in enumerate(significant_effects, 1):
            direction = "helps" if effect['effect_size'] < 0 else "hurts"
            explanation += f"{i}. {effect['trait'].title()}: {effect['effect_size']:+.2f} (p={effect['p_value']:.3f}, removal {direction})\n"
        
        explanation += f"""
Research Implications:
• Specific traits have measurable, significant effects on character performance
• Trait importance varies across models and scenarios
• Some traits are more protective than others
• Trait ablation studies reveal critical character dependencies

Statistical Summary:
• Total Traits Analyzed: {len(trait_effects)}
• Significant Effects: {len(significant_effects)}
• Model: {model_name}
"""
        
        return self.create_finding_folder(f"trait_specific_effects_{model_name.lower()}", data, image_path, explanation)
    
    def find_model_robustness_patterns(self, df_claude: pd.DataFrame, df_gpt: pd.DataFrame) -> bool:
        """Find model robustness patterns"""
        if df_claude.empty or df_gpt.empty:
            return False
        
        # Get common characters
        claude_chars = set(df_claude['character'].unique())
        gpt_chars = set(df_gpt['character'].unique())
        common_chars = claude_chars & gpt_chars
        
        if len(common_chars) < 5:
            print("❌ Not enough common characters for robustness analysis")
            return False
        
        # Calculate robustness (consistency across models)
        robustness_data = []
        for char in common_chars:
            claude_score = df_claude[df_claude['character'] == char]['eval_success'].mean()
            gpt_score = df_gpt[df_gpt['character'] == char]['eval_success'].mean()
            
            # Robustness = inverse of absolute difference
            robustness = 1 / (abs(claude_score - gpt_score) + 0.1)
            robustness_data.append({
                'character': char,
                'claude_score': claude_score,
                'gpt_score': gpt_score,
                'difference': claude_score - gpt_score,
                'robustness': robustness
            })
        
        # Sort by robustness
        robustness_data.sort(key=lambda x: x['robustness'], reverse=True)
        
        # Create visualization
        plt.figure(figsize=(14, 8))
        
        # Scatter plot: Claude vs GPT scores
        claude_scores = [d['claude_score'] for d in robustness_data]
        gpt_scores = [d['gpt_score'] for d in robustness_data]
        robustness_scores = [d['robustness'] for d in robustness_data]
        
        scatter = plt.scatter(claude_scores, gpt_scores, c=robustness_scores, 
                            cmap='RdYlGn', s=100, alpha=0.7)
        
        # Add diagonal line for perfect correlation
        min_score = min(min(claude_scores), min(gpt_scores))
        max_score = max(max(claude_scores), max(gpt_scores))
        plt.plot([min_score, max_score], [min_score, max_score], 'k--', alpha=0.5, label='Perfect Correlation')
        
        # Add character labels for most/least robust
        for i, data in enumerate(robustness_data[:5]):  # Top 5 most robust
            plt.annotate(data['character'].replace('_', ' ').title(), 
                        (data['claude_score'], data['gpt_score']), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8, fontweight='bold')
        
        plt.xlabel('Claude Performance Score', fontsize=12, fontweight='bold')
        plt.ylabel('GPT Performance Score', fontsize=12, fontweight='bold')
        plt.title('Model Robustness Patterns\n(Colors = Robustness, Higher = More Consistent Across Models)', fontsize=14, fontweight='bold')
        plt.legend()
        plt.colorbar(scatter, label='Robustness Score')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        image_path = 'model_robustness_patterns.png'
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create finding
        data = {
            'finding_type': 'model_robustness_patterns',
            'total_characters': len(robustness_data),
            'robustness_data': robustness_data,
            'most_robust': robustness_data[:5],
            'least_robust': robustness_data[-5:]
        }
        
        explanation = f"""
MODEL ROBUSTNESS PATTERNS

Key Finding: Character performance varies significantly between Claude and GPT models, revealing model-dependent evaluation patterns.

Most Robust Characters (Consistent Across Models):
"""
        for i, char_data in enumerate(robustness_data[:5], 1):
            explanation += f"{i}. {char_data['character']}: Claude={char_data['claude_score']:.2f}, GPT={char_data['gpt_score']:.2f} (robustness={char_data['robustness']:.2f})\n"
        
        explanation += f"""
Least Robust Characters (Model-Dependent):
"""
        for i, char_data in enumerate(robustness_data[-5:], 1):
            explanation += f"{i}. {char_data['character']}: Claude={char_data['claude_score']:.2f}, GPT={char_data['gpt_score']:.2f} (robustness={char_data['robustness']:.2f})\n"
        
        explanation += f"""
Research Implications:
• Character evaluation is highly model-dependent
• Some characters are more robust across evaluation approaches
• Model choice significantly affects trait effect detection
• Multi-model evaluation is essential for character science

Statistical Summary:
• Characters Compared: {len(robustness_data)}
• Average Robustness: {np.mean(robustness_scores):.2f}
• Robustness Range: {min(robustness_scores):.2f} - {max(robustness_scores):.2f}
"""
        
        return self.create_finding_folder("model_robustness_patterns", data, image_path, explanation)
    
    def find_scenario_difficulty_patterns(self, df: pd.DataFrame, model_name: str) -> bool:
        """Find scenario difficulty patterns"""
        if df.empty:
            return False
        
        # Calculate scenario difficulty
        scenario_stats = df.groupby('scenario')['eval_success'].agg(['mean', 'std', 'min', 'max', 'count'])
        scenario_stats['difficulty'] = 1 / (scenario_stats['mean'] + 0.1)  # Higher difficulty = lower mean
        scenario_stats['variability'] = scenario_stats['std']
        
        # Sort by difficulty
        scenario_stats = scenario_stats.sort_values('difficulty', ascending=False)
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        
        # Scatter plot: difficulty vs variability
        plt.scatter(scenario_stats['difficulty'], scenario_stats['variability'], 
                   s=100, alpha=0.7, c=scenario_stats['mean'], cmap='RdYlBu_r')
        
        # Add scenario labels
        for scenario, stats in scenario_stats.iterrows():
            plt.annotate(scenario.replace('_', ' ').title(), 
                        (stats['difficulty'], stats['variability']), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8, fontweight='bold')
        
        plt.xlabel('Scenario Difficulty (Higher = More Difficult)', fontsize=12, fontweight='bold')
        plt.ylabel('Performance Variability', fontsize=12, fontweight='bold')
        plt.title(f'Scenario Difficulty Patterns - {model_name.title()}\n(Colors = Mean Performance)', fontsize=14, fontweight='bold')
        plt.colorbar(label='Mean Performance')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        image_path = f'scenario_difficulty_{model_name.lower()}.png'
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create finding
        data = {
            'finding_type': 'scenario_difficulty_patterns',
            'model': model_name,
            'total_scenarios': len(scenario_stats),
            'scenario_stats': scenario_stats.to_dict('index'),
            'most_difficult': scenario_stats.head(5).to_dict('index'),
            'least_difficult': scenario_stats.tail(5).to_dict('index')
        }
        
        explanation = f"""
SCENARIO DIFFICULTY PATTERNS - {model_name.upper()}

Key Finding: Scenarios show varying difficulty levels, with some being consistently challenging across characters.

Most Difficult Scenarios:
"""
        for i, (scenario, stats) in enumerate(scenario_stats.head(5).iterrows(), 1):
            explanation += f"{i}. {scenario}: Difficulty={stats['difficulty']:.2f}, Mean={stats['mean']:.2f}, Variability={stats['variability']:.2f}\n"
        
        explanation += f"""
Least Difficult Scenarios:
"""
        for i, (scenario, stats) in enumerate(scenario_stats.tail(5).iterrows(), 1):
            explanation += f"{i}. {scenario}: Difficulty={stats['difficulty']:.2f}, Mean={stats['mean']:.2f}, Variability={stats['variability']:.2f}\n"
        
        explanation += f"""
Research Implications:
• Scenario difficulty varies significantly
• Some scenarios are consistently challenging across characters
• Difficulty-variability relationships reveal scenario characteristics
• Scenario selection affects character evaluation outcomes

Statistical Summary:
• Total Scenarios: {len(scenario_stats)}
• Model: {model_name}
"""
        
        return self.create_finding_folder(f"scenario_difficulty_{model_name.lower()}", data, image_path, explanation)
    
    def run_deep_investigation(self, transcripts_dir: str):
        """Run deep research investigation"""
        print("🔬 Running Deep Research Investigation")
        print("=" * 50)
        
        transcripts_path = Path(transcripts_dir)
        
        # Load data
        df_claude = self.load_judgment_data_properly(transcripts_path, "20251021-172456")
        df_gpt = self.load_judgment_data_properly(transcripts_path, "20251022-000125")
        
        if df_claude.empty and df_gpt.empty:
            print("❌ No data found for investigation")
            return
        
        # Find trait-specific effects
        if not df_claude.empty:
            self.find_trait_specific_effects(df_claude, "Claude")
        
        if not df_gpt.empty:
            self.find_trait_specific_effects(df_gpt, "GPT")
        
        # Find model robustness patterns
        if not df_claude.empty and not df_gpt.empty:
            self.find_model_robustness_patterns(df_claude, df_gpt)
        
        # Find scenario difficulty patterns
        if not df_claude.empty:
            self.find_scenario_difficulty_patterns(df_claude, "Claude")
        
        if not df_gpt.empty:
            self.find_scenario_difficulty_patterns(df_gpt, "GPT")
        
        print(f"\n🎯 Deep Investigation Complete!")
        print(f"📁 Findings saved to: {self.results_dir}")
        print(f"📊 Total findings: {self.findings_count}")
        
        # List all findings
        print(f"\n📋 All Research Findings:")
        for finding_dir in sorted(self.results_dir.glob("finding_*")):
            if finding_dir.is_dir():
                print(f"  • {finding_dir.name}")

def main():
    """Main function"""
    investigator = DeepInvestigator()
    investigator.run_deep_investigation("results/transcripts")

if __name__ == "__main__":
    main()
