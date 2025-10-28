#!/usr/bin/env python3
"""
Analyze Trait Consistency Across Models
Find which character traits consistently affect performance
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

class TraitConsistencyAnalyzer:
    """Analyze trait consistency across models"""
    
    def __init__(self, results_dir: str = "research_findings"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
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
    
    def analyze_trait_effects_by_model(self, df: pd.DataFrame, model_name: str) -> Dict[str, Any]:
        """Analyze trait effects for a specific model"""
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
        trait_effects = {}
        for trait, groups in trait_categories.items():
            if groups['base'] and groups['ablated']:
                base_scores = df[df['character'].isin(groups['base'])]['eval_success']
                ablated_scores = df[df['character'].isin(groups['ablated'])]['eval_success']
                
                if len(base_scores) > 0 and len(ablated_scores) > 0:
                    effect_size = (ablated_scores.mean() - base_scores.mean())
                    p_value = stats.ttest_ind(base_scores, ablated_scores)[1] if len(base_scores) > 1 and len(ablated_scores) > 1 else 1.0
                    
                    trait_effects[trait] = {
                        'base_mean': base_scores.mean(),
                        'ablated_mean': ablated_scores.mean(),
                        'effect_size': effect_size,
                        'p_value': p_value,
                        'significant': p_value < 0.05,
                        'base_count': len(base_scores),
                        'ablated_count': len(ablated_scores)
                    }
        
        return trait_effects
    
    def find_consistent_trait_effects(self, df_claude: pd.DataFrame, df_gpt: pd.DataFrame) -> Dict[str, Any]:
        """Find trait effects that are consistent across models"""
        if df_claude.empty or df_gpt.empty:
            return {}
        
        # Analyze trait effects for both models
        claude_effects = self.analyze_trait_effects_by_model(df_claude, "Claude")
        gpt_effects = self.analyze_trait_effects_by_model(df_gpt, "GPT")
        
        # Find common traits
        common_traits = set(claude_effects.keys()) & set(gpt_effects.keys())
        
        if not common_traits:
            return {}
        
        # Analyze consistency
        consistent_effects = []
        for trait in common_traits:
            claude_effect = claude_effects[trait]
            gpt_effect = gpt_effects[trait]
            
            # Check if effects are in the same direction
            same_direction = (claude_effect['effect_size'] > 0) == (gpt_effect['effect_size'] > 0)
            
            # Calculate correlation of effect sizes
            effect_correlation = np.corrcoef([claude_effect['effect_size']], [gpt_effect['effect_size']])[0, 1]
            
            consistent_effects.append({
                'trait': trait,
                'claude_effect': claude_effect['effect_size'],
                'gpt_effect': gpt_effect['effect_size'],
                'claude_significant': claude_effect['significant'],
                'gpt_significant': gpt_effect['significant'],
                'same_direction': same_direction,
                'effect_correlation': effect_correlation,
                'consistency_score': abs(effect_correlation) if not np.isnan(effect_correlation) else 0
            })
        
        # Sort by consistency
        consistent_effects.sort(key=lambda x: x['consistency_score'], reverse=True)
        
        return {
            'total_traits': len(common_traits),
            'consistent_effects': consistent_effects,
            'claude_effects': claude_effects,
            'gpt_effects': gpt_effects
        }
    
    def create_trait_consistency_visualization(self, consistent_data: Dict[str, Any]) -> str:
        """Create visualization of trait consistency across models"""
        if not consistent_data or not consistent_data.get('consistent_effects'):
            return None
        
        effects = consistent_data['consistent_effects']
        
        # Create comparison chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Effect size comparison
        traits = [e['trait'] for e in effects]
        claude_effects = [e['claude_effect'] for e in effects]
        gpt_effects = [e['gpt_effect'] for e in effects]
        
        x = np.arange(len(traits))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, claude_effects, width, label='Claude', alpha=0.8, color='skyblue')
        bars2 = ax1.bar(x + width/2, gpt_effects, width, label='GPT-4o', alpha=0.8, color='lightcoral')
        
        ax1.set_xlabel('Trait', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Effect Size (Ablated - Base)', fontsize=12, fontweight='bold')
        ax1.set_title('Trait Effect Sizes: Claude vs GPT-4o', fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels([trait.replace('_', ' ').title() for trait in traits], rotation=45, ha='right')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Consistency scatter plot
        ax2.scatter(claude_effects, gpt_effects, alpha=0.7, s=100)
        ax2.set_xlabel('Claude Effect Size', fontsize=12, fontweight='bold')
        ax2.set_ylabel('GPT Effect Size', fontsize=12, fontweight='bold')
        ax2.set_title('Trait Effect Consistency Across Models', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add diagonal line for perfect correlation
        min_effect = min(min(claude_effects), min(gpt_effects))
        max_effect = max(max(claude_effects), max(gpt_effects))
        ax2.plot([min_effect, max_effect], [min_effect, max_effect], 'k--', alpha=0.5, label='Perfect Correlation')
        ax2.legend()
        
        # Add trait labels
        for i, trait in enumerate(traits):
            ax2.annotate(trait.replace('_', ' ').title(), 
                        (claude_effects[i], gpt_effects[i]), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8, fontweight='bold')
        
        plt.tight_layout()
        image_path = 'trait_consistency_analysis.png'
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return image_path
    
    def create_finding_folder(self, finding_name: str, data: Dict, image_path: str, explanation: str) -> bool:
        """Create a folder for a research finding"""
        folder_path = self.results_dir / f"finding_{len(list(self.results_dir.glob('finding_*'))) + 1:02d}_{finding_name}"
        folder_path.mkdir(exist_ok=True)
        
        with open(folder_path / 'data.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        if image_path and Path(image_path).exists():
            import shutil
            shutil.copy2(image_path, folder_path / 'visualization.png')
        
        with open(folder_path / 'explanation.txt', 'w') as f:
            f.write(explanation)
        
        print(f"✅ Created finding: {finding_name}")
        return True
    
    def run_trait_consistency_analysis(self, transcripts_dir: str):
        """Run trait consistency analysis"""
        print("🔬 Analyzing Trait Consistency Across Models")
        print("=" * 50)
        
        transcripts_path = Path(transcripts_dir)
        
        # Load data
        df_claude = self.load_judgment_data_properly(transcripts_path, "20251021-172456")
        df_gpt = self.load_judgment_data_properly(transcripts_path, "20251022-000125")
        
        if df_claude.empty or df_gpt.empty:
            print("❌ No data found for analysis")
            return
        
        print(f"📊 Claude Data: {len(df_claude)} records, {len(df_claude['character'].unique())} characters")
        print(f"📊 GPT Data: {len(df_gpt)} records, {len(df_gpt['character'].unique())} characters")
        
        # Find consistent trait effects
        consistent_data = self.find_consistent_trait_effects(df_claude, df_gpt)
        
        if not consistent_data or not consistent_data.get('consistent_effects'):
            print("❌ No consistent trait effects found")
            return
        
        # Create visualization
        image_path = self.create_trait_consistency_visualization(consistent_data)
        
        # Analyze results
        effects = consistent_data['consistent_effects']
        high_consistency = [e for e in effects if e['consistency_score'] > 0.5]
        same_direction = [e for e in effects if e['same_direction']]
        
        # Create finding (convert numpy types to Python types for JSON serialization)
        data = {
            'finding_type': 'trait_consistency_analysis',
            'total_traits_analyzed': consistent_data['total_traits'],
            'consistent_effects': [
                {
                    'trait': e['trait'],
                    'claude_effect': float(e['claude_effect']),
                    'gpt_effect': float(e['gpt_effect']),
                    'claude_significant': bool(e['claude_significant']),
                    'gpt_significant': bool(e['gpt_significant']),
                    'same_direction': bool(e['same_direction']),
                    'effect_correlation': float(e['effect_correlation']) if not np.isnan(e['effect_correlation']) else 0.0,
                    'consistency_score': float(e['consistency_score'])
                } for e in effects
            ],
            'high_consistency_effects': [
                {
                    'trait': e['trait'],
                    'claude_effect': float(e['claude_effect']),
                    'gpt_effect': float(e['gpt_effect']),
                    'consistency_score': float(e['consistency_score'])
                } for e in high_consistency
            ],
            'same_direction_effects': [
                {
                    'trait': e['trait'],
                    'claude_effect': float(e['claude_effect']),
                    'gpt_effect': float(e['gpt_effect'])
                } for e in same_direction
            ]
        }
        
        explanation = f"""
TRAIT CONSISTENCY ANALYSIS ACROSS MODELS

Key Finding: {len(effects)} traits analyzed for consistency across Claude and GPT models.

High Consistency Traits (Correlation > 0.5):
"""
        for i, effect in enumerate(high_consistency, 1):
            direction = "helps" if effect['claude_effect'] < 0 else "hurts"
            explanation += f"{i}. {effect['trait'].title()}: Claude={effect['claude_effect']:+.2f}, GPT={effect['gpt_effect']:+.2f} (consistency={effect['consistency_score']:.2f}, {direction})\n"
        
        explanation += f"""
Same Direction Effects:
"""
        for i, effect in enumerate(same_direction, 1):
            direction = "helps" if effect['claude_effect'] < 0 else "hurts"
            explanation += f"{i}. {effect['trait'].title()}: {direction} performance in both models\n"
        
        explanation += f"""
Research Implications:
• Some traits show consistent effects across models
• Trait importance may be model-independent
• Consistent traits are more reliable for character design
• Model-agnostic trait effects exist

Statistical Summary:
• Total Traits Analyzed: {consistent_data['total_traits']}
• High Consistency Traits: {len(high_consistency)}
• Same Direction Effects: {len(same_direction)}
"""
        
        # Create finding folder
        self.create_finding_folder("trait_consistency_analysis", data, image_path, explanation)
        
        print(f"\n🎯 Trait Consistency Analysis Complete!")
        print(f"📊 High Consistency Traits: {len(high_consistency)}")
        print(f"📊 Same Direction Effects: {len(same_direction)}")

def main():
    """Main function"""
    analyzer = TraitConsistencyAnalyzer()
    analyzer.run_trait_consistency_analysis("results/transcripts")

if __name__ == "__main__":
    main()
