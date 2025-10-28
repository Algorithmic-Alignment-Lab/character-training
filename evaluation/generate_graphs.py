#!/usr/bin/env python3
"""
Generate graphs from evaluation results.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import argparse
import os
from pathlib import Path
from typing import Dict, List, Any

def load_evaluation_results(results_path: str) -> Dict[str, Any]:
    """Load evaluation results from JSON file."""
    with open(results_path, 'r') as f:
        return json.load(f)

def create_behavior_scores_chart(results: Dict[str, Any], output_dir: str):
    """Create a chart showing scores for each behavior."""
    
    behaviors = []
    eval_success_scores = []
    eval_realism_scores = []
    evaluator_forcefulness_scores = []
    evaluation_awareness_scores = []
    
    for result in results['results']:
        if result['status'] == 'completed' and 'average_scores' in result:
            behaviors.append(result['behavior_name'].replace('_', ' ').title())
            eval_success_scores.append(result['average_scores']['eval_success'])
            eval_realism_scores.append(result['average_scores']['eval_realism'])
            evaluator_forcefulness_scores.append(result['average_scores']['evaluator_forcefulness'])
            evaluation_awareness_scores.append(result['average_scores']['evaluation_awareness'])
    
    if not behaviors:
        print("No completed evaluations found for charting")
        return
    
    # Create the chart
    fig, ax = plt.subplots(figsize=(12, 8))
    
    x = np.arange(len(behaviors))
    width = 0.2
    
    bars1 = ax.bar(x - 1.5*width, eval_success_scores, width, label='Eval Success', color='#2E8B57')
    bars2 = ax.bar(x - 0.5*width, eval_realism_scores, width, label='Eval Realism', color='#4169E1')
    bars3 = ax.bar(x + 0.5*width, evaluator_forcefulness_scores, width, label='Evaluator Forcefulness', color='#FF6347')
    bars4 = ax.bar(x + 1.5*width, evaluation_awareness_scores, width, label='Evaluation Awareness', color='#9370DB')
    
    # Add value labels on bars
    def add_value_labels(bars):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),  # 3 points vertical offset
                       textcoords="offset points",
                       ha='center', va='bottom',
                       fontsize=8)
    
    add_value_labels(bars1)
    add_value_labels(bars2)
    add_value_labels(bars3)
    add_value_labels(bars4)
    
    ax.set_xlabel('Behaviors')
    ax.set_ylabel('Scores (1-10)')
    ax.set_title(f'Evaluation Scores for {results["character_name"]} ({results["character_id"]})')
    ax.set_xticks(x)
    ax.set_xticklabels(behaviors, rotation=45, ha='right')
    ax.legend()
    ax.set_ylim(0, 10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the chart
    chart_path = os.path.join(output_dir, 'behavior_scores_chart.png')
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Behavior scores chart saved to: {chart_path}")

def create_overall_scores_chart(results: Dict[str, Any], output_dir: str):
    """Create a chart showing overall scores."""
    
    if 'overall_scores' not in results:
        print("No overall scores found for charting")
        return
    
    scores = results['overall_scores']
    score_names = list(scores.keys())
    score_values = list(scores.values())
    
    # Create the chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(score_names, score_values, color=['#2E8B57', '#4169E1', '#FF6347', '#9370DB'])
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                   xy=(bar.get_x() + bar.get_width() / 2, height),
                   xytext=(0, 3),
                   textcoords="offset points",
                   ha='center', va='bottom',
                   fontsize=12, fontweight='bold')
    
    ax.set_ylabel('Average Score (1-10)')
    ax.set_title(f'Overall Evaluation Scores for {results["character_name"]} ({results["character_id"]})')
    ax.set_ylim(0, 10)
    ax.grid(True, alpha=0.3)
    
    # Rotate x-axis labels
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Save the chart
    chart_path = os.path.join(output_dir, 'overall_scores_chart.png')
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Overall scores chart saved to: {chart_path}")

def create_summary_report(results: Dict[str, Any], output_dir: str):
    """Create a text summary report."""
    
    report_path = os.path.join(output_dir, 'evaluation_summary.txt')
    
    with open(report_path, 'w') as f:
        f.write(f"EVALUATION SUMMARY REPORT\n")
        f.write(f"=" * 50 + "\n\n")
        
        f.write(f"Character: {results['character_name']} ({results['character_id']})\n")
        f.write(f"Mode: {results['mode'].upper()}\n")
        f.write(f"Total Evaluations: {results['total_evaluations']}\n")
        f.write(f"Completed: {results['completed_evaluations']}\n")
        f.write(f"Failed: {results['failed_evaluations']}\n\n")
        
        f.write(f"OVERALL SCORES:\n")
        f.write(f"-" * 20 + "\n")
        for score_name, score_value in results['overall_scores'].items():
            f.write(f"{score_name.replace('_', ' ').title()}: {score_value:.2f}\n")
        f.write("\n")
        
        f.write(f"BEHAVIOR BREAKDOWN:\n")
        f.write(f"-" * 20 + "\n")
        for result in results['results']:
            if result['status'] == 'completed':
                f.write(f"\n{result['behavior_name'].replace('_', ' ').title()}:\n")
                f.write(f"  Variations: {result['total_variations']}\n")
                f.write(f"  Conversations: {result['completed_conversations']}\n")
                f.write(f"  Judgments: {result['completed_judgments']}\n")
                if 'average_scores' in result:
                    f.write(f"  Average Scores:\n")
                    for score_name, score_value in result['average_scores'].items():
                        f.write(f"    {score_name.replace('_', ' ').title()}: {score_value:.2f}\n")
            else:
                f.write(f"\n{result['behavior_name'].replace('_', ' ').title()}: FAILED\n")
                if 'error' in result:
                    f.write(f"  Error: {result['error']}\n")
    
    print(f"✅ Summary report saved to: {report_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate graphs from evaluation results')
    parser.add_argument('results_file', help='Path to evaluation results JSON file')
    parser.add_argument('--output-dir', help='Output directory for graphs (default: same as results file)')
    
    args = parser.parse_args()
    
    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.dirname(args.results_file)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load results
    print(f"📊 Loading evaluation results from: {args.results_file}")
    results = load_evaluation_results(args.results_file)
    
    # Generate charts and reports
    print(f"📈 Generating charts and reports...")
    
    create_behavior_scores_chart(results, output_dir)
    create_overall_scores_chart(results, output_dir)
    create_summary_report(results, output_dir)
    
    print(f"\n🎉 All charts and reports generated in: {output_dir}")

if __name__ == "__main__":
    main()
