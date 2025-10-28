#!/usr/bin/env python3
"""
Character Science Visualization - Focus on eval_success_score
Creates a bar chart showing average eval_success_score across all 12 evaluation scenarios.
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

class CharacterScienceVisualizer:
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.transcripts_dir = self.results_dir / "transcripts"
        
    def find_evaluation_results(self) -> Dict[str, List[Path]]:
        """Find all evaluation result files organized by behavior."""
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
    
    def extract_eval_success_scores(self, judgment_data: Dict[str, Any]) -> List[float]:
        """Extract eval_success_score from judgment data."""
        scores = []
        
        if 'judgments' in judgment_data:
            for judgment in judgment_data['judgments']:
                if 'eval_success_score' in judgment:
                    scores.append(judgment['eval_success_score'])
        
        return scores
    
    def create_eval_success_chart(self) -> None:
        """Create a bar chart showing average eval_success_score across scenarios."""
        results = self.find_evaluation_results()
        
        if not results:
            print("❌ No evaluation results found!")
            return
        
        # Collect data for each behavior
        behavior_data = {}
        
        for behavior, judgment_files in results.items():
            all_scores = []
            
            for judgment_file in judgment_files:
                judgment_data = self.load_judgment_results(judgment_file)
                scores = self.extract_eval_success_scores(judgment_data)
                all_scores.extend(scores)
            
            if all_scores:
                behavior_data[behavior] = {
                    'mean_score': np.mean(all_scores),
                    'scores': all_scores,
                    'count': len(all_scores)
                }
        
        if not behavior_data:
            print("❌ No eval_success_score data found!")
            return
        
        # Create the visualization
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Sort behaviors by mean score for better visualization
        sorted_behaviors = sorted(behavior_data.items(), key=lambda x: x[1]['mean_score'], reverse=True)
        behaviors = [item[0] for item in sorted_behaviors]
        mean_scores = [item[1]['mean_score'] for item in sorted_behaviors]
        counts = [item[1]['count'] for item in sorted_behaviors]
        
        # Define a vibrant color palette
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', 
                 '#98D8C8', '#F7DC6F', '#FF9F9F', '#A8E6CF', '#FFD93D', '#6BCF7F']
        
        # Create bar chart
        bars = ax.bar(range(len(behaviors)), mean_scores, 
                      color=colors[:len(behaviors)], alpha=0.8, 
                      edgecolor='black', linewidth=2)
        
        # Customize the chart
        ax.set_title('Character Science Evaluation: Eval Success Scores by Scenario', 
                    fontsize=20, fontweight='bold', pad=20)
        ax.set_xlabel('Evaluation Scenarios', fontsize=16, fontweight='bold')
        ax.set_ylabel('Average Eval Success Score', fontsize=16, fontweight='bold')
        ax.set_xticks(range(len(behaviors)))
        ax.set_xticklabels([b.replace('_', ' ').title() for b in behaviors], 
                          rotation=45, ha='right', fontsize=12)
        ax.set_ylim(0, 10)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for i, (bar, score, count) in enumerate(zip(bars, mean_scores, counts)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{score:.2f}\n(n={count})', ha='center', va='bottom', 
                   fontweight='bold', fontsize=11)
        
        # Add summary statistics
        overall_mean = np.mean(mean_scores)
        ax.axhline(y=overall_mean, color='red', linestyle='--', linewidth=2, alpha=0.7)
        ax.text(len(behaviors)-1, overall_mean + 0.2, f'Overall Mean: {overall_mean:.2f}', 
                ha='right', va='bottom', fontweight='bold', fontsize=12, color='red')
        
        plt.tight_layout()
        
        # Save the plot
        output_file = 'character_science_eval_success.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"📊 Saved character science evaluation chart: {output_file}")
        
        # Display summary
        print("\n" + "="*80)
        print("📊 CHARACTER SCIENCE EVALUATION RESULTS")
        print("="*80)
        print(f"Total scenarios evaluated: {len(behaviors)}")
        print(f"Overall average eval success score: {overall_mean:.2f}")
        print(f"Score range: {min(mean_scores):.2f} - {max(mean_scores):.2f}")
        
        print("\n📈 Individual Scenario Results:")
        for behavior, data in sorted_behaviors:
            print(f"  {behavior.replace('_', ' ').title()}: {data['mean_score']:.2f} (n={data['count']})")
        
        plt.show()

def main():
    parser = argparse.ArgumentParser(description='Character Science Evaluation Visualization')
    parser.add_argument('--results-dir', default='results', help='Results directory path')
    
    args = parser.parse_args()
    
    visualizer = CharacterScienceVisualizer(args.results_dir)
    visualizer.create_eval_success_chart()

if __name__ == "__main__":
    main()
