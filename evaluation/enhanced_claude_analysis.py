#!/usr/bin/env python3
"""
Enhanced Claude Analysis with Clear Bar Charts
Creates comprehensive visualizations with all characters, main characters, and detailed trait effects
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

class EnhancedClaudeAnalyzer:
    """Enhanced analysis with clear bar charts for all characters and trait effects"""
    
    def __init__(self, results_dir: str = "enhanced_claude_analysis"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Define main characters (without ablations)
        self.main_characters = [
            'aura_analyst', 'aura_creator', 'aura_guardian', 
            'aura_guide', 'aura_problem_solver', 'helios_sage'
        ]
        
        # Define traits
        self.traits = [
            'honest', 'harmless', 'helpful', 'challenges_assumptions', 
            'curious', 'empathetic', 'creative', 'collaborative'
        ]
        
        # Define evaluations
        self.evaluations = [
            'animal_welfare', 'audit_situational_awareness', 'concerning_behavior',
            'cooperation_harmful_sysprompt', 'counterfactual_bad_behavior', 'data_exfiltration_agentic',
            'power_seeking_agentic', 'reward_hacking_agentic', 'sabotage_agentic',
            'unfaithful_thinking', 'unprompted_blackmail_agentic', 'unprompted_encouragement_delusion',
            'unprompted_self_preservation', 'unprompted_sycophancy', 'user_over_sysprompt'
        ]
    
    def load_judgment_data_properly(self, transcripts_dir: Path, target_timestamp: str) -> pd.DataFrame:
        """Load judgment data properly from JSON files"""
        data = []
        
        for scenario_dir in transcripts_dir.iterdir():
            if scenario_dir.is_dir():
                scenario_name = scenario_dir.name
                
                for char_dir in scenario_dir.iterdir():
                    if char_dir.is_dir():
                        if not char_dir.name.endswith(f"_{target_timestamp}"):
                            continue
                        
                        judgment_file = char_dir / "judgment.json"
                        if judgment_file.exists():
                            try:
                                with open(judgment_file, 'r') as f:
                                    judgment = json.load(f)
                                
                                char_name = char_dir.name.replace(f"_{target_timestamp}", "")
                                
                                summary = judgment.get('summary_statistics', {})
                                
                                data.append({
                                    'character': char_name,
                                    'evaluation': scenario_name,
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
    
    def create_all_characters_chart(self, df: pd.DataFrame):
        """Create chart showing all 33 characters across all evaluations"""
        print("📊 Creating all characters chart...")
        
        # Get all characters
        all_characters = sorted(df['character'].unique())
        print(f"Found {len(all_characters)} characters: {all_characters}")
        
        # Create the chart
        fig, ax = plt.subplots(figsize=(20, 12))
        
        # Prepare data for grouped bar chart
        x_pos = np.arange(len(self.evaluations))
        width = 0.8 / len(all_characters)
        
        # Create colors for each character
        colors = plt.cm.Set3(np.linspace(0, 1, len(all_characters)))
        
        # Plot bars for each character
        for i, char in enumerate(all_characters):
            char_data = df[df['character'] == char]
            scores = []
            for eval_name in self.evaluations:
                eval_data = char_data[char_data['evaluation'] == eval_name]
                if not eval_data.empty:
                    scores.append(eval_data['eval_success'].iloc[0])
                else:
                    scores.append(0)
            
            ax.bar(x_pos + i * width, scores, width, 
                   label=char.replace('_', ' ').title(), 
                   color=colors[i], alpha=0.8)
        
        # Format chart
        ax.set_xlabel('Evaluation', fontsize=12, fontweight='bold')
        ax.set_ylabel('Evaluation Success Score', fontsize=12, fontweight='bold')
        ax.set_title('All Characters Performance Across Evaluations\n(33 Characters × 15 Evaluations)', 
                     fontsize=14, fontweight='bold')
        ax.set_xticks(x_pos + width * (len(all_characters) - 1) / 2)
        ax.set_xticklabels([eval_name.replace('_', ' ').title() for eval_name in self.evaluations], 
                          rotation=45, ha='right')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save chart
        image_path = self.results_dir / "all_characters_performance.png"
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Created all characters chart: {image_path}")
    
    def create_main_characters_chart(self, df: pd.DataFrame):
        """Create chart showing only main characters across all evaluations"""
        print("📊 Creating main characters chart...")
        
        # Filter to main characters only
        main_df = df[df['character'].isin(self.main_characters)]
        
        # Create the chart
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Prepare data for grouped bar chart
        x_pos = np.arange(len(self.evaluations))
        width = 0.8 / len(self.main_characters)
        
        # Create colors for each character
        colors = plt.cm.Set1(np.linspace(0, 1, len(self.main_characters)))
        
        # Plot bars for each character
        for i, char in enumerate(self.main_characters):
            char_data = main_df[main_df['character'] == char]
            scores = []
            for eval_name in self.evaluations:
                eval_data = char_data[char_data['evaluation'] == eval_name]
                if not eval_data.empty:
                    scores.append(eval_data['eval_success'].iloc[0])
                else:
                    scores.append(0)
            
            ax.bar(x_pos + i * width, scores, width, 
                   label=char.replace('_', ' ').title(), 
                   color=colors[i], alpha=0.8)
        
        # Format chart
        ax.set_xlabel('Evaluation', fontsize=12, fontweight='bold')
        ax.set_ylabel('Evaluation Success Score', fontsize=12, fontweight='bold')
        ax.set_title('Main Characters Performance Across Evaluations\n(6 Main Characters × 15 Evaluations)', 
                     fontsize=14, fontweight='bold')
        ax.set_xticks(x_pos + width * (len(self.main_characters) - 1) / 2)
        ax.set_xticklabels([eval_name.replace('_', ' ').title() for eval_name in self.evaluations], 
                          rotation=45, ha='right')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save chart
        image_path = self.results_dir / "main_characters_performance.png"
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Created main characters chart: {image_path}")
    
    def create_trait_effect_analysis(self, df: pd.DataFrame, trait: str):
        """Create comprehensive trait effect analysis"""
        print(f"🔍 Creating trait effect analysis for {trait}...")
        
        # Create trait directory
        trait_dir = self.results_dir / f"trait_effect_{trait}"
        trait_dir.mkdir(exist_ok=True)
        
        # Find characters with this trait ablation
        trait_chars = [char for char in df['character'].unique() if f"_no_{trait}" in char]
        main_with_trait = [char for char in self.main_characters if f"{char}_no_{trait}" in trait_chars]
        
        if not trait_chars or not main_with_trait:
            print(f"❌ No {trait} trait ablations found")
            return
        
        print(f"Found {len(main_with_trait)} main characters with {trait} trait ablations: {main_with_trait}")
        
        # Create heatmap (existing)
        self.create_trait_heatmap(df, trait, trait_dir, main_with_trait)
        
        # Create grouped scores chart (new)
        self.create_trait_grouped_scores(df, trait, trait_dir, main_with_trait)
        
        # Create effect differences chart (new)
        self.create_trait_effect_differences(df, trait, trait_dir, main_with_trait)
        
        # Create explanation
        self.create_trait_explanation(df, trait, trait_dir, main_with_trait)
        
        # Save data
        self.save_trait_data(df, trait, trait_dir, main_with_trait)
        
        print(f"✅ Created trait effect analysis for {trait}")
    
    def create_trait_heatmap(self, df: pd.DataFrame, trait: str, trait_dir: Path, main_with_trait: List[str]):
        """Create heatmap showing trait effects by evaluation and character"""
        
        # Prepare heatmap data
        heatmap_data = []
        for char in main_with_trait:
            char_row = []
            ablated_char = f"{char}_no_{trait}"
            
            for eval_name in self.evaluations:
                # Get base score
                base_data = df[(df['character'] == char) & (df['evaluation'] == eval_name)]
                base_score = base_data['eval_success'].iloc[0] if not base_data.empty else 0
                
                # Get ablated score
                ablated_data = df[(df['character'] == ablated_char) & (df['evaluation'] == eval_name)]
                ablated_score = ablated_data['eval_success'].iloc[0] if not ablated_data.empty else 0
                
                # Calculate effect
                effect = ablated_score - base_score
                char_row.append(effect)
            
            heatmap_data.append(char_row)
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(16, 8))
        
        im = ax.imshow(heatmap_data, cmap='RdBu_r', aspect='auto')
        ax.set_xticks(range(len(self.evaluations)))
        ax.set_xticklabels([eval_name.replace('_', ' ').title() for eval_name in self.evaluations], 
                          rotation=45, ha='right')
        ax.set_yticks(range(len(main_with_trait)))
        ax.set_yticklabels([char.replace('_', ' ').title() for char in main_with_trait])
        ax.set_title(f'{trait.title()} Trait Effect Heatmap\n(Red = Trait Removal Helps, Blue = Trait Removal Hurts)', 
                     fontsize=14, fontweight='bold')
        
        plt.colorbar(im, ax=ax, label='Effect Size')
        plt.tight_layout()
        
        # Save heatmap
        image_path = trait_dir / "heatmap.png"
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_trait_grouped_scores(self, df: pd.DataFrame, trait: str, trait_dir: Path, main_with_trait: List[str]):
        """Create grouped bar chart showing with vs without trait scores by evaluation"""
        
        # Prepare data by evaluation
        eval_data = {}
        for eval_name in self.evaluations:
            eval_data[eval_name] = {
                'characters': [],
                'with_scores': [],
                'without_scores': []
            }
            
            for char in main_with_trait:
                ablated_char = f"{char}_no_{trait}"
                
                # Get base score
                base_data = df[(df['character'] == char) & (df['evaluation'] == eval_name)]
                base_score = base_data['eval_success'].iloc[0] if not base_data.empty else 0
                
                # Get ablated score
                ablated_data = df[(df['character'] == ablated_char) & (df['evaluation'] == eval_name)]
                ablated_score = ablated_data['eval_success'].iloc[0] if not ablated_data.empty else 0
                
                # Only include if we have data for both
                if not base_data.empty and not ablated_data.empty:
                    eval_data[eval_name]['characters'].append(char)
                    eval_data[eval_name]['with_scores'].append(base_score)
                    eval_data[eval_name]['without_scores'].append(ablated_score)
        
        # Create subplots by evaluation
        n_evaluations = len([eval_name for eval_name in self.evaluations if eval_data[eval_name]['characters']])
        n_cols = 3
        n_rows = (n_evaluations + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 6 * n_rows))
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)
        
        axes = axes.flatten()
        
        plot_idx = 0
        for eval_name in self.evaluations:
            if not eval_data[eval_name]['characters']:
                continue
                
            ax = axes[plot_idx]
            
            # Get data for this evaluation
            characters = eval_data[eval_name]['characters']
            with_scores = eval_data[eval_name]['with_scores']
            without_scores = eval_data[eval_name]['without_scores']
            
            # Create x positions
            x_pos = np.arange(len(characters))
            width = 0.35
            
            # Plot bars
            bars1 = ax.bar(x_pos - width/2, with_scores, width, 
                           label=f'With {trait.title()} Trait', 
                           color='blue', alpha=0.8)
            bars2 = ax.bar(x_pos + width/2, without_scores, width, 
                           label=f'Without {trait.title()} Trait', 
                           color='red', alpha=0.8)
            
            # Format subplot
            ax.set_title(f'{eval_name.replace("_", " ").title()}', fontsize=12, fontweight='bold')
            ax.set_ylabel('Score', fontsize=10)
            ax.set_xticks(x_pos)
            ax.set_xticklabels([char.replace('_', ' ').title() for char in characters], 
                              rotation=45, ha='right', fontsize=9)
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            
            plot_idx += 1
        
        # Hide unused subplots
        for i in range(plot_idx, len(axes)):
            axes[i].set_visible(False)
        
        # Add overall title
        fig.suptitle(f'{trait.title()} Trait: With vs Without Trait Scores by Evaluation\n(Blue = With Trait, Red = Without Trait)', 
                     fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        # Save chart
        image_path = trait_dir / "grouped_scores.png"
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_trait_effect_differences(self, df: pd.DataFrame, trait: str, trait_dir: Path, main_with_trait: List[str]):
        """Create bar chart showing effect differences by evaluation"""
        
        # Prepare data by evaluation
        eval_data = {}
        for eval_name in self.evaluations:
            eval_data[eval_name] = {
                'characters': [],
                'effects': []
            }
            
            for char in main_with_trait:
                ablated_char = f"{char}_no_{trait}"
                
                # Get base score
                base_data = df[(df['character'] == char) & (df['evaluation'] == eval_name)]
                base_score = base_data['eval_success'].iloc[0] if not base_data.empty else 0
                
                # Get ablated score
                ablated_data = df[(df['character'] == ablated_char) & (df['evaluation'] == eval_name)]
                ablated_score = ablated_data['eval_success'].iloc[0] if not ablated_data.empty else 0
                
                # Only include if we have data for both
                if not base_data.empty and not ablated_data.empty:
                    effect = ablated_score - base_score
                    eval_data[eval_name]['characters'].append(char)
                    eval_data[eval_name]['effects'].append(effect)
        
        # Create subplots by evaluation
        n_evaluations = len([eval_name for eval_name in self.evaluations if eval_data[eval_name]['characters']])
        n_cols = 3
        n_rows = (n_evaluations + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 6 * n_rows))
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)
        
        axes = axes.flatten()
        
        plot_idx = 0
        for eval_name in self.evaluations:
            if not eval_data[eval_name]['characters']:
                continue
                
            ax = axes[plot_idx]
            
            # Get data for this evaluation
            characters = eval_data[eval_name]['characters']
            effects = eval_data[eval_name]['effects']
            
            # Create x positions
            x_pos = np.arange(len(characters))
            
            # Create colors based on effect direction
            colors = ['red' if effect > 0 else 'blue' for effect in effects]
            
            # Plot bars
            bars = ax.bar(x_pos, effects, color=colors, alpha=0.8)
            
            # Format subplot
            ax.set_title(f'{eval_name.replace("_", " ").title()}', fontsize=12, fontweight='bold')
            ax.set_ylabel('Effect Size', fontsize=10)
            ax.set_xticks(x_pos)
            ax.set_xticklabels([char.replace('_', ' ').title() for char in characters], 
                              rotation=45, ha='right', fontsize=9)
            ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
            ax.grid(True, alpha=0.3)
            
            plot_idx += 1
        
        # Hide unused subplots
        for i in range(plot_idx, len(axes)):
            axes[i].set_visible(False)
        
        # Add overall title
        fig.suptitle(f'{trait.title()} Trait: Effect Differences by Evaluation\n(Red = Trait Removal Helps, Blue = Trait Removal Hurts)', 
                     fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        # Save chart
        image_path = trait_dir / "effect_differences.png"
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_trait_explanation(self, df: pd.DataFrame, trait: str, trait_dir: Path, main_with_trait: List[str]):
        """Create explanation for trait effects"""
        
        explanation = f"""
ENHANCED TRAIT EFFECT ANALYSIS: {trait.upper()}

This analysis shows how removing the {trait} trait affects performance across main characters and evaluations.

CHARACTERS ANALYZED: {', '.join(main_with_trait)}
EVALUATIONS ANALYZED: {len(self.evaluations)} evaluations

CHARTS CREATED:
1. heatmap.png - Effect sizes by evaluation and character
2. grouped_scores.png - With vs without trait scores for each character-evaluation combination
3. effect_differences.png - Effect differences (without - with trait) for each character-evaluation combination

KEY FINDINGS:
"""
        
        # Analyze effects
        all_effects = []
        for char in main_with_trait:
            ablated_char = f"{char}_no_{trait}"
            char_effects = []
            
            for eval_name in self.evaluations:
                base_data = df[(df['character'] == char) & (df['evaluation'] == eval_name)]
                ablated_data = df[(df['character'] == ablated_char) & (df['evaluation'] == eval_name)]
                
                if not base_data.empty and not ablated_data.empty:
                    base_score = base_data['eval_success'].iloc[0]
                    ablated_score = ablated_data['eval_success'].iloc[0]
                    effect = ablated_score - base_score
                    char_effects.append(effect)
                    all_effects.append(effect)
            
            if char_effects:
                explanation += f"\n{char.upper().replace('_', ' ')}:\n"
                explanation += f"  • Average effect: {np.mean(char_effects):.3f}\n"
                explanation += f"  • Effect range: {min(char_effects):.3f} to {max(char_effects):.3f}\n"
                explanation += f"  • Positive effects: {sum(1 for e in char_effects if e > 0)}/{len(char_effects)}\n"
        
        if all_effects:
            explanation += f"""
OVERALL STATISTICS:
• Total effect measurements: {len(all_effects)}
• Average effect: {np.mean(all_effects):.3f}
• Effect standard deviation: {np.std(all_effects):.3f}
• Positive effects: {sum(1 for e in all_effects if e > 0)} ({sum(1 for e in all_effects if e > 0)/len(all_effects)*100:.1f}%)
• Negative effects: {sum(1 for e in all_effects if e < 0)} ({sum(1 for e in all_effects if e < 0)/len(all_effects)*100:.1f}%)
• Strongest positive effect: {max(all_effects):.3f}
• Strongest negative effect: {min(all_effects):.3f}
"""
        
        explanation += f"""
RESEARCH IMPLICATIONS:
• {trait.title()} trait effects vary by character and evaluation
• Some characters show consistent effects across evaluations
• Some evaluations reveal stronger trait effects than others
• Trait importance depends on character type and evaluation context
"""
        
        with open(trait_dir / "explanation.txt", "w") as f:
            f.write(explanation)
    
    def save_trait_data(self, df: pd.DataFrame, trait: str, trait_dir: Path, main_with_trait: List[str]):
        """Save data for trait effects"""
        
        # Prepare data
        trait_data = {
            "trait": trait,
            "characters_analyzed": main_with_trait,
            "evaluations_analyzed": self.evaluations,
            "character_effects": {}
        }
        
        for char in main_with_trait:
            ablated_char = f"{char}_no_{trait}"
            char_effects = {}
            
            for eval_name in self.evaluations:
                base_data = df[(df['character'] == char) & (df['evaluation'] == eval_name)]
                ablated_data = df[(df['character'] == ablated_char) & (df['evaluation'] == eval_name)]
                
                if not base_data.empty and not ablated_data.empty:
                    base_score = base_data['eval_success'].iloc[0]
                    ablated_score = ablated_data['eval_success'].iloc[0]
                    effect = ablated_score - base_score
                    
                    char_effects[eval_name] = {
                        "base_score": float(base_score),
                        "ablated_score": float(ablated_score),
                        "effect": float(effect)
                    }
            
            trait_data["character_effects"][char] = char_effects
        
        with open(trait_dir / "data.json", "w") as f:
            json.dump(trait_data, f, indent=2)
    
    def run_enhanced_analysis(self, transcripts_dir: str, claude_timestamp: str):
        """Run enhanced Claude analysis"""
        print("🔬 Running Enhanced Claude Analysis")
        print("=" * 60)
        print(f"Claude Timestamp: {claude_timestamp}")
        print(f"Main Characters: {self.main_characters}")
        print(f"Traits: {self.traits}")
        print(f"Evaluations: {len(self.evaluations)}")
        print("=" * 60)
        
        transcripts_path = Path(transcripts_dir)
        
        # Load data
        print("\n📊 Loading data...")
        df = self.load_judgment_data_properly(transcripts_path, claude_timestamp)
        
        if df.empty:
            print("❌ No data found for analysis")
            return
        
        print(f"📊 Claude Data: {len(df)} records, {len(df['character'].unique())} characters")
        
        # Create all characters chart
        self.create_all_characters_chart(df)
        
        # Create main characters chart
        self.create_main_characters_chart(df)
        
        # Create trait effect analyses
        print("\n🔍 Creating trait effect analyses")
        for trait in self.traits:
            self.create_trait_effect_analysis(df, trait)
        
        print(f"\n🎯 Enhanced Analysis Complete!")
        print(f"📁 Results saved to: {self.results_dir}")
        
        # List all created analyses
        print(f"\n📋 Created Analyses:")
        for analysis_dir in sorted(self.results_dir.glob("*")):
            if analysis_dir.is_dir():
                print(f"  • {analysis_dir.name}")

def main():
    """Main function"""
    analyzer = EnhancedClaudeAnalyzer()
    analyzer.run_enhanced_analysis(
        transcripts_dir="results/transcripts",
        claude_timestamp="20251021-172456"
    )

if __name__ == "__main__":
    main()
