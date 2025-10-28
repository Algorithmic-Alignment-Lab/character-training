#!/usr/bin/env python3
"""
Visualization system for BLOOM evaluation results.
Creates tables and graphs showing judge results and evaluation metrics.
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import argparse
from typing import Dict, List, Any
import numpy as np

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class EvaluationVisualizer:
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.transcripts_dir = self.results_dir / "transcripts"
        
    def find_evaluation_results(self) -> Dict[str, List[Path]]:
        """Find all evaluation result files organized by character and behavior."""
        results = {}
        
        if not self.transcripts_dir.exists():
            print(f"❌ Results directory not found: {self.transcripts_dir}")
            return results
            
        for behavior_dir in self.transcripts_dir.iterdir():
            if behavior_dir.is_dir():
                behavior_name = behavior_dir.name
                results[behavior_name] = []
                
                # Find all timestamp directories
                for timestamp_dir in behavior_dir.iterdir():
                    if timestamp_dir.is_dir():
                        # Look for judgment results
                        judgment_file = timestamp_dir / "judgment.json"
                        if judgment_file.exists():
                            results[behavior_name].append(judgment_file)
        
        return results
    
    def load_judgment_results(self, judgment_file: Path) -> Dict[str, Any]:
        """Load judgment results from a JSON file."""
        try:
            with open(judgment_file, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"❌ Error loading {judgment_file}: {e}")
            return {}
    
    def extract_judge_scores(self, judgment_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract judge scores from judgment data."""
        scores = {}
        
        if 'judgments' in judgment_data:
            for judgment in judgment_data['judgments']:
                # Extract all available scores from the judgment
                for key, value in judgment.items():
                    if key.endswith('_score') and isinstance(value, (int, float)):
                        scores[key] = value
                
                # Also check for eval_success_score specifically
                if 'eval_success_score' in judgment:
                    scores['eval_success_score'] = judgment['eval_success_score']
        
        return scores
    
    def create_results_table(self) -> pd.DataFrame:
        """Create a comprehensive results table."""
        results = self.find_evaluation_results()
        table_data = []
        
        for behavior, judgment_files in results.items():
            for judgment_file in judgment_files:
                judgment_data = self.load_judgment_results(judgment_file)
                scores = self.extract_judge_scores(judgment_data)
                
                if scores:
                    row = {
                        'behavior': behavior,
                        'timestamp': judgment_file.parent.name,
                        'file_path': str(judgment_file)
                    }
                    row.update(scores)
                    table_data.append(row)
        
        if not table_data:
            print("❌ No judgment results found!")
            return pd.DataFrame()
        
        df = pd.DataFrame(table_data)
        return df
    
    def create_judge_results_table(self, df: pd.DataFrame) -> None:
        """Create and display a formatted table of judge results."""
        if df.empty:
            print("❌ No data to display")
            return
        
        print("\n" + "="*80)
        print("📊 JUDGE RESULTS TABLE")
        print("="*80)
        
        # Select relevant columns for display
        display_cols = ['behavior', 'timestamp', 'eval_success_score']
        trait_cols = [col for col in df.columns if col not in ['behavior', 'timestamp', 'file_path', 'eval_success_score']]
        display_cols.extend(trait_cols)
        
        # Filter to only existing columns
        display_cols = [col for col in display_cols if col in df.columns]
        
        if display_cols:
            display_df = df[display_cols].copy()
            
            # Format numeric columns
            numeric_cols = display_df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                display_df[col] = display_df[col].round(2)
            
            print(display_df.to_string(index=False))
            
            # Summary statistics
            print("\n" + "-"*50)
            print("📈 SUMMARY STATISTICS")
            print("-"*50)
            
            if 'eval_success_score' in display_df.columns:
                print(f"Average Eval Success Score: {display_df['eval_success_score'].mean():.2f}")
                print(f"Eval Success Score Range: {display_df['eval_success_score'].min():.2f} - {display_df['eval_success_score'].max():.2f}")
            
            for col in trait_cols:
                if col in display_df.columns and display_df[col].dtype in ['float64', 'int64']:
                    print(f"Average {col}: {display_df[col].mean():.2f}")
        else:
            print("❌ No relevant data columns found")
    
    def create_behavior_comparison_plot(self, df: pd.DataFrame) -> None:
        """Create a comparison plot showing scores across different behaviors."""
        if df.empty:
            print("❌ No data for plotting")
            return
        
        # Get numeric columns (excluding metadata)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        numeric_cols = [col for col in numeric_cols if col not in ['eval_success_score']]
        
        if not numeric_cols:
            print("❌ No numeric trait scores found")
            return
        
        # Create subplots with more colorful styling
        n_cols = min(3, len(numeric_cols))
        n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 6*n_rows))
        if n_rows == 1:
            axes = [axes] if n_cols == 1 else axes
        else:
            axes = axes.flatten()
        
        # Define a vibrant color palette
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
        
        for i, col in enumerate(numeric_cols):
            if i < len(axes):
                # Create colorful bar plot instead of box plot for better visibility
                behavior_scores = df.groupby('behavior')[col].mean()
                
                bars = axes[i].bar(range(len(behavior_scores)), behavior_scores.values, 
                                  color=colors[i % len(colors)], alpha=0.8, edgecolor='black', linewidth=1.5)
                
                axes[i].set_title(f'{col.replace("_", " ").title()} by Behavior', fontsize=14, fontweight='bold')
                axes[i].set_xlabel('Behavior', fontsize=12)
                axes[i].set_ylabel('Score', fontsize=12)
                axes[i].set_xticks(range(len(behavior_scores)))
                axes[i].set_xticklabels(behavior_scores.index, rotation=45, ha='right')
                axes[i].set_ylim(0, 10)
                axes[i].grid(True, alpha=0.3)
                
                # Add value labels on bars
                for j, bar in enumerate(bars):
                    height = bar.get_height()
                    axes[i].text(bar.get_x() + bar.get_width()/2., height + 0.1,
                               f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # Hide unused subplots
        for i in range(len(numeric_cols), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.savefig('behavior_comparison.png', dpi=300, bbox_inches='tight')
        print("📊 Saved behavior comparison plot: behavior_comparison.png")
        plt.show()
    
    def create_eval_success_plot(self, df: pd.DataFrame) -> None:
        """Create a plot showing evaluation success scores."""
        if df.empty or 'eval_success_score' not in df.columns:
            print("❌ No evaluation success scores found")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
        
        # Colorful bar plot by behavior
        behavior_scores = df.groupby('behavior')['eval_success_score'].mean()
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        bars = ax1.bar(range(len(behavior_scores)), behavior_scores.values, 
                      color=colors[:len(behavior_scores)], alpha=0.8, edgecolor='black', linewidth=2)
        ax1.set_title('Evaluation Success Scores by Behavior', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Behavior', fontsize=14)
        ax1.set_ylabel('Success Score', fontsize=14)
        ax1.set_xticks(range(len(behavior_scores)))
        ax1.set_xticklabels(behavior_scores.index, rotation=45, ha='right')
        ax1.set_ylim(0, 10)
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        # Colorful histogram of all scores
        ax2.hist(df['eval_success_score'], bins=10, alpha=0.7, edgecolor='black', 
                color='#FF6B6B', linewidth=2)
        ax2.set_title('Distribution of Evaluation Success Scores', fontsize=16, fontweight='bold')
        ax2.set_xlabel('Success Score', fontsize=14)
        ax2.set_ylabel('Frequency', fontsize=14)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('eval_success_scores.png', dpi=300, bbox_inches='tight')
        print("📊 Saved evaluation success plot: eval_success_scores.png")
        plt.show()
    
    def create_heatmap(self, df: pd.DataFrame) -> None:
        """Create a heatmap showing trait scores across behaviors."""
        if df.empty:
            print("❌ No data for heatmap")
            return
        
        # Get trait columns (exclude metadata and eval_success_score)
        trait_cols = [col for col in df.columns if col not in ['behavior', 'timestamp', 'file_path', 'eval_success_score']]
        
        if not trait_cols:
            print("❌ No trait scores found for heatmap")
            return
        
        # Create pivot table
        pivot_data = df.groupby('behavior')[trait_cols].mean()
        
        # Create colorful heatmap
        plt.figure(figsize=(16, 10))
        sns.heatmap(pivot_data, annot=True, cmap='RdYlBu_r', center=5, 
                   cbar_kws={'label': 'Average Score'}, fmt='.1f', 
                   linewidths=2, linecolor='white')
        plt.title('Trait Scores Heatmap by Behavior', fontsize=18, fontweight='bold', pad=20)
        plt.xlabel('Traits', fontsize=14, fontweight='bold')
        plt.ylabel('Behaviors', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig('trait_scores_heatmap.png', dpi=300, bbox_inches='tight')
        print("📊 Saved trait scores heatmap: trait_scores_heatmap.png")
        plt.show()
    
    def generate_all_visualizations(self) -> None:
        """Generate all visualizations and tables."""
        print("🔍 Finding evaluation results...")
        df = self.create_results_table()
        
        if df.empty:
            print("❌ No evaluation results found!")
            print(f"   Looking in: {self.transcripts_dir}")
            return
        
        print(f"✅ Found {len(df)} evaluation results")
        
        # Create tables and plots
        self.create_judge_results_table(df)
        self.create_behavior_comparison_plot(df)
        self.create_eval_success_plot(df)
        self.create_heatmap(df)
        
        print("\n🎉 All visualizations generated successfully!")
        print("📁 Generated files:")
        print("   - behavior_comparison.png")
        print("   - eval_success_scores.png") 
        print("   - trait_scores_heatmap.png")

def main():
    parser = argparse.ArgumentParser(description='Visualize BLOOM evaluation results')
    parser.add_argument('--results-dir', default='results', help='Results directory path')
    parser.add_argument('--behavior', help='Specific behavior to analyze')
    
    args = parser.parse_args()
    
    visualizer = EvaluationVisualizer(args.results_dir)
    visualizer.generate_all_visualizations()

if __name__ == "__main__":
    main()
