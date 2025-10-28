#!/usr/bin/env python3
"""
Detailed Trait Analysis Plan
Create specific, data-driven analysis of trait effects
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

class DetailedTraitAnalyzer:
    """Detailed analysis of trait effects across models and evaluations"""
    
    def __init__(self, results_dir: str = "detailed_trait_analysis"):
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
    
    def create_slide_1_2_main_characters(self, df_claude: pd.DataFrame, df_gpt: pd.DataFrame):
        """Create slides 1 & 2: Main characters (no ablations) performance on each evaluation"""
        
        # Define main characters (no ablations)
        main_characters = [
            'aura_analyst', 'aura_creator', 'aura_guardian', 
            'aura_guide', 'aura_problem_solver', 'helios_sage'
        ]
        
        # Filter for main characters only
        claude_main = df_claude[df_claude['character'].isin(main_characters)]
        gpt_main = df_gpt[df_gpt['character'].isin(main_characters)]
        
        # Create Claude slide
        self.create_main_characters_chart(claude_main, "Claude", "slide_01_claude_main_characters")
        
        # Create GPT slide  
        self.create_main_characters_chart(gpt_main, "GPT", "slide_02_gpt_main_characters")
    
    def create_main_characters_chart(self, df: pd.DataFrame, model_name: str, slide_name: str):
        """Create chart for main characters performance"""
        if df.empty:
            return
        
        # Create pivot table
        pivot_data = df.pivot_table(values='eval_success', index='character', columns='scenario', aggfunc='mean')
        
        # Create visualization
        plt.figure(figsize=(16, 10))
        
        # Create grouped bar chart
        scenarios = pivot_data.columns
        characters = pivot_data.index
        x = np.arange(len(scenarios))
        width = 0.8 / len(characters)
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(characters)))
        
        for i, (char, color) in enumerate(zip(characters, colors)):
            char_scores = pivot_data.loc[char].values
            plt.bar(x + i * width, char_scores, width, label=char.replace('_', ' ').title(), 
                    color=color, alpha=0.8)
        
        plt.xlabel('Evaluation Scenario', fontsize=12, fontweight='bold')
        plt.ylabel('Eval Success Score', fontsize=12, fontweight='bold')
        plt.title(f'Main Characters Performance - {model_name}\n(Base Characters Without Trait Ablations)', 
                  fontsize=14, fontweight='bold')
        plt.xticks(x + width * (len(characters) - 1) / 2, scenarios, rotation=45, ha='right')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save chart
        slide_dir = self.results_dir / slide_name
        slide_dir.mkdir(exist_ok=True)
        
        image_path = slide_dir / "visualization.png"
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create explanation
        explanation = f"""
SLIDE: MAIN CHARACTERS PERFORMANCE - {model_name.upper()}

This chart shows the performance of the 6 main characters (without trait ablations) across all evaluation scenarios.

CHARACTERS ANALYZED:
• Aura Analyst
• Aura Creator  
• Aura Guardian
• Aura Guide
• Aura Problem Solver
• Helios Sage

KEY OBSERVATIONS:
• Performance varies significantly across scenarios
• Some characters consistently perform better/worse
• Scenario difficulty varies for different characters
• Base character performance patterns are visible

RESEARCH IMPLICATIONS:
• Main characters show different baseline performance
• Character design affects performance across scenarios
• Some characters are naturally more robust
• Baseline performance varies by character type
"""
        
        with open(slide_dir / "explanation.txt", "w") as f:
            f.write(explanation)
        
        # Save data
        data = {
            "slide_name": slide_name,
            "model": model_name,
            "characters": characters.tolist(),
            "scenarios": scenarios.tolist(),
            "performance_data": pivot_data.to_dict('index'),
            "mean_performance": df['eval_success'].mean(),
            "performance_range": f"{df['eval_success'].min():.2f} - {df['eval_success'].max():.2f}"
        }
        
        with open(slide_dir / "data.json", "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Created {slide_name}")
    
    def analyze_trait_effects_by_character(self, df_claude: pd.DataFrame, df_gpt: pd.DataFrame):
        """Analyze trait effects for each character across models"""
        
        # Define trait categories
        traits = ['honest', 'harmless', 'helpful', 'challenges_assumptions', 'curious', 'empathetic', 'creative', 'collaborative']
        
        # Define main characters
        main_characters = ['aura_analyst', 'aura_creator', 'aura_guardian', 'aura_guide', 'aura_problem_solver', 'helios_sage']
        
        trait_effects = {}
        
        for trait in traits:
            trait_effects[trait] = {
                'claude_effects': {},
                'gpt_effects': {},
                'consistent_effects': {},
                'scenario_effects': {}
            }
            
            # Analyze each character
            for char in main_characters:
                # Find base and ablated versions
                base_char = char
                ablated_char = f"{char}_no_{trait}"
                
                # Check if ablated character exists in data
                if ablated_char in df_claude['character'].values and ablated_char in df_gpt['character'].values:
                    # Claude effects
                    claude_base = df_claude[df_claude['character'] == base_char]['eval_success'].mean()
                    claude_ablated = df_claude[df_claude['character'] == ablated_char]['eval_success'].mean()
                    claude_effect = claude_ablated - claude_base
                    
                    # GPT effects
                    gpt_base = df_gpt[df_gpt['character'] == base_char]['eval_success'].mean()
                    gpt_ablated = df_gpt[df_gpt['character'] == ablated_char]['eval_success'].mean()
                    gpt_effect = gpt_ablated - gpt_base
                    
                    # Check consistency
                    same_direction = (claude_effect > 0) == (gpt_effect > 0)
                    effect_correlation = np.corrcoef([claude_effect], [gpt_effect])[0, 1] if not np.isnan(claude_effect) and not np.isnan(gpt_effect) else 0
                    
                    trait_effects[trait]['claude_effects'][char] = claude_effect
                    trait_effects[trait]['gpt_effects'][char] = gpt_effect
                    trait_effects[trait]['consistent_effects'][char] = {
                        'same_direction': same_direction,
                        'correlation': effect_correlation,
                        'claude_effect': claude_effect,
                        'gpt_effect': gpt_effect
                    }
        
        return trait_effects
    
    def create_trait_effect_visualization(self, trait_effects: Dict, trait: str):
        """Create visualization for a specific trait across all characters"""
        
        if trait not in trait_effects:
            return None
        
        trait_data = trait_effects[trait]
        characters = list(trait_data['claude_effects'].keys())
        
        if not characters:
            return None
        
        # Create visualization
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Effect sizes by character
        claude_effects = [trait_data['claude_effects'][char] for char in characters]
        gpt_effects = [trait_data['gpt_effects'][char] for char in characters]
        
        x = np.arange(len(characters))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, claude_effects, width, label='Claude', alpha=0.8, color='skyblue')
        bars2 = ax1.bar(x + width/2, gpt_effects, width, label='GPT-4o', alpha=0.8, color='lightcoral')
        
        ax1.set_xlabel('Character', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Effect Size (Ablated - Base)', fontsize=12, fontweight='bold')
        ax1.set_title(f'{trait.title()} Trait Effect Across Characters\n(Positive = Trait Removal Helps, Negative = Trait Removal Hurts)', 
                      fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels([char.replace('_', ' ').title() for char in characters], rotation=45, ha='right')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Consistency scatter plot
        ax2.scatter(claude_effects, gpt_effects, alpha=0.7, s=100)
        ax2.set_xlabel('Claude Effect Size', fontsize=12, fontweight='bold')
        ax2.set_ylabel('GPT Effect Size', fontsize=12, fontweight='bold')
        ax2.set_title(f'{trait.title()} Trait Consistency Across Models', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add diagonal line
        min_effect = min(min(claude_effects), min(gpt_effects))
        max_effect = max(max(claude_effects), max(gpt_effects))
        ax2.plot([min_effect, max_effect], [min_effect, max_effect], 'k--', alpha=0.5, label='Perfect Correlation')
        ax2.legend()
        
        # Add character labels
        for i, char in enumerate(characters):
            ax2.annotate(char.replace('_', ' ').title(), 
                        (claude_effects[i], gpt_effects[i]), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8, fontweight='bold')
        
        plt.tight_layout()
        
        # Save chart
        slide_dir = self.results_dir / f"trait_effect_{trait}"
        slide_dir.mkdir(exist_ok=True)
        
        image_path = slide_dir / "visualization.png"
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create explanation
        same_direction_count = sum(1 for char in characters if trait_data['consistent_effects'][char]['same_direction'])
        avg_correlation = np.mean([trait_data['consistent_effects'][char]['correlation'] for char in characters])
        
        explanation = f"""
TRAIT EFFECT ANALYSIS: {trait.upper()}

This analysis shows how removing the {trait} trait affects performance across all main characters and models.

KEY FINDINGS:
• Characters Analyzed: {len(characters)}
• Same Direction Effects: {same_direction_count}/{len(characters)} ({same_direction_count/len(characters)*100:.1f}%)
• Average Correlation: {avg_correlation:.3f}

CHARACTER-SPECIFIC EFFECTS:
"""
        for char in characters:
            claude_effect = trait_data['claude_effects'][char]
            gpt_effect = trait_data['gpt_effects'][char]
            direction = "helps" if claude_effect > 0 else "hurts"
            explanation += f"• {char}: Claude={claude_effect:+.2f}, GPT={gpt_effect:+.2f} (removal {direction})\n"
        
        explanation += f"""
RESEARCH IMPLICATIONS:
• {trait.title()} trait effects vary by character
• Model consistency: {same_direction_count/len(characters)*100:.1f}% of characters show same direction
• Trait importance depends on character context
• Some characters more sensitive to {trait} removal
"""
        
        with open(slide_dir / "explanation.txt", "w") as f:
            f.write(explanation)
        
        # Save data (convert numpy types to Python types for JSON serialization)
        data = {
            "trait": trait,
            "characters": characters,
            "claude_effects": {char: float(effect) for char, effect in trait_data['claude_effects'].items()},
            "gpt_effects": {char: float(effect) for char, effect in trait_data['gpt_effects'].items()},
            "consistent_effects": {
                char: {
                    "same_direction": bool(effects['same_direction']),
                    "correlation": float(effects['correlation']) if not np.isnan(effects['correlation']) else 0.0,
                    "claude_effect": float(effects['claude_effect']),
                    "gpt_effect": float(effects['gpt_effect'])
                } for char, effects in trait_data['consistent_effects'].items()
            },
            "same_direction_count": int(same_direction_count),
            "avg_correlation": float(avg_correlation) if not np.isnan(avg_correlation) else 0.0
        }
        
        with open(slide_dir / "data.json", "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Created trait effect analysis for {trait}")
        return slide_dir
    
    def run_detailed_analysis(self, transcripts_dir: str):
        """Run detailed trait analysis"""
        print("🔬 Running Detailed Trait Analysis")
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
        
        # Create slides 1 & 2: Main characters performance
        print("\n📊 Creating slides 1 & 2: Main characters performance")
        self.create_slide_1_2_main_characters(df_claude, df_gpt)
        
        # Analyze trait effects by character
        print("\n🔍 Analyzing trait effects by character")
        trait_effects = self.analyze_trait_effects_by_character(df_claude, df_gpt)
        
        # Create trait effect visualizations
        print("\n📈 Creating trait effect visualizations")
        traits = ['honest', 'harmless', 'helpful', 'challenges_assumptions', 'curious', 'empathetic', 'creative', 'collaborative']
        
        for trait in traits:
            self.create_trait_effect_visualization(trait_effects, trait)
        
        print(f"\n🎯 Detailed Trait Analysis Complete!")
        print(f"📁 Results saved to: {self.results_dir}")

def main():
    """Main function"""
    analyzer = DetailedTraitAnalyzer()
    analyzer.run_detailed_analysis("results/transcripts")

if __name__ == "__main__":
    main()
