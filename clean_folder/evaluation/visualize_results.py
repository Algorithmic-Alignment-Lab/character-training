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
                if 'eval_success_score' in judgment:
                    scores['eval_success_score'] = judgment['eval_success_score']
                
                if 'trait_scores' in judgment:
                    for trait, score in judgment['trait_scores'].items():
                        scores[trait] = score
        
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
        
        # Create subplots
        n_cols = min(3, len(numeric_cols))
        n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5*n_rows))
        if n_rows == 1:
            axes = [axes] if n_cols == 1 else axes
        else:
            axes = axes.flatten()
        
        for i, col in enumerate(numeric_cols):
            if i < len(axes):
                # Create box plot
                sns.boxplot(data=df, x='behavior', y=col, ax=axes[i])
                axes[i].set_title(f'{col.replace("_", " ").title()} by Behavior')
                axes[i].set_xlabel('Behavior')
                axes[i].set_ylabel('Score')
                axes[i].tick_params(axis='x', rotation=45)
        
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
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Box plot by behavior
        sns.boxplot(data=df, x='behavior', y='eval_success_score', ax=ax1)
        ax1.set_title('Evaluation Success Scores by Behavior')
        ax1.set_xlabel('Behavior')
        ax1.set_ylabel('Success Score')
        ax1.tick_params(axis='x', rotation=45)
        
        # Histogram of all scores
        ax2.hist(df['eval_success_score'], bins=20, alpha=0.7, edgecolor='black')
        ax2.set_title('Distribution of Evaluation Success Scores')
        ax2.set_xlabel('Success Score')
        ax2.set_ylabel('Frequency')
        
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
        
        # Create heatmap
        plt.figure(figsize=(12, 8))
        sns.heatmap(pivot_data, annot=True, cmap='RdYlBu_r', center=0.5, 
                   cbar_kws={'label': 'Average Score'})
        plt.title('Trait Scores Heatmap by Behavior')
        plt.xlabel('Traits')
        plt.ylabel('Behaviors')
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
