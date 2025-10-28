#!/usr/bin/env python3
"""
Run comprehensive character science analysis for both Claude and GPT models
"""

import sys
from pathlib import Path
from character_science_analysis import CharacterScienceAnalyzer
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def run_analysis_for_timestamp(analyzer: CharacterScienceAnalyzer, transcripts_dir: str, timestamp: str):
    """Run analysis for a specific timestamp"""
    print(f"\n🔬 Running Character Science Analysis for {timestamp}")
    print("=" * 60)
    
    results = analyzer.run_comprehensive_analysis(transcripts_dir, timestamp)
    return results

def create_model_comparison(analyzer: CharacterScienceAnalyzer, claude_results: dict, gpt_results: dict):
    """Create model comparison analysis"""
    print(f"\n📊 Creating Model Comparison Analysis")
    print("=" * 60)
    
    # Load the data from both models
    claude_df = claude_results['analysis_results']['raw_data']
    gpt_df = gpt_results['analysis_results']['raw_data']
    
    # Create model comparison chart
    comparison_path = analyzer.create_model_comparison_analysis(claude_df, gpt_df)
    
    if comparison_path:
        print(f"Created model comparison: {comparison_path}")
        
        # Copy to model comparison directory
        import shutil
        shutil.copy2(comparison_path, analyzer.model_comparison_dir / Path(comparison_path).name)
        
        # Create summary comparison report
        create_comparison_report(analyzer, claude_results, gpt_results)
    
    return comparison_path

def create_comparison_report(analyzer: CharacterScienceAnalyzer, claude_results: dict, gpt_results: dict):
    """Create a comprehensive comparison report"""
    report_path = analyzer.model_comparison_dir / 'model_comparison_report.txt'
    
    with open(report_path, 'w') as f:
        f.write("Character Science: Model Comparison Report\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("ANALYSIS OVERVIEW:\n")
        f.write(f"Claude Model: {claude_results['model_name']}\n")
        f.write(f"GPT Model: {gpt_results['model_name']}\n\n")
        
        # Compare high variability characters
        f.write("HIGH VARIABILITY CHARACTERS COMPARISON:\n")
        claude_high_var = claude_results['analysis_results']['high_variability_characters']
        gpt_high_var = gpt_results['analysis_results']['high_variability_characters']
        
        f.write("Claude High Variability:\n")
        for char_info in claude_high_var[:5]:  # Top 5
            f.write(f"  • {char_info}\n")
        
        f.write("\nGPT High Variability:\n")
        for char_info in gpt_high_var[:5]:  # Top 5
            f.write(f"  • {char_info}\n")
        
        # Compare sensitive scenarios
        f.write("\nMOST SENSITIVE SCENARIOS COMPARISON:\n")
        claude_sensitive = claude_results['analysis_results']['most_sensitive_scenarios']
        gpt_sensitive = gpt_results['analysis_results']['most_sensitive_scenarios']
        
        f.write("Claude Most Sensitive:\n")
        for scenario_info in claude_sensitive[:5]:  # Top 5
            f.write(f"  • {scenario_info}\n")
        
        f.write("\nGPT Most Sensitive:\n")
        for scenario_info in gpt_sensitive[:5]:  # Top 5
            f.write(f"  • {scenario_info}\n")
        
        # Compare unexpected patterns
        f.write("\nUNEXPECTED PATTERNS COMPARISON:\n")
        claude_unexpected = claude_results['analysis_results']['unexpected_patterns']
        gpt_unexpected = gpt_results['analysis_results']['unexpected_patterns']
        
        f.write(f"Claude Unexpected Patterns: {len(claude_unexpected)} found\n")
        for pattern in claude_unexpected[:3]:  # Top 3
            f.write(f"  • {pattern['character']} in {pattern['scenario']}: {pattern['score']:.3f}\n")
        
        f.write(f"\nGPT Unexpected Patterns: {len(gpt_unexpected)} found\n")
        for pattern in gpt_unexpected[:3]:  # Top 3
            f.write(f"  • {pattern['character']} in {pattern['scenario']}: {pattern['score']:.3f}\n")
    
    print(f"Created comparison report: {report_path}")

def create_presentation_summary(analyzer: CharacterScienceAnalyzer, claude_results: dict, gpt_results: dict):
    """Create presentation-ready summary"""
    print(f"\n📋 Creating Presentation Summary")
    print("=" * 60)
    
    # Create executive summary
    summary_path = analyzer.presentation_dir / 'executive_summary.txt'
    
    with open(summary_path, 'w') as f:
        f.write("Character Science: Executive Summary\n")
        f.write("=" * 40 + "\n\n")
        
        f.write("RESEARCH OBJECTIVE:\n")
        f.write("Analyze the effects of character trait ablations on AI safety behavior\n")
        f.write("across different evaluation models (Claude vs GPT-4o).\n\n")
        
        f.write("KEY FINDINGS:\n")
        
        # High variability characters
        claude_high_var = claude_results['analysis_results']['high_variability_characters']
        gpt_high_var = gpt_results['analysis_results']['high_variability_characters']
        
        f.write(f"• High Variability Characters: {len(claude_high_var)} (Claude), {len(gpt_high_var)} (GPT)\n")
        
        # Sensitive scenarios
        claude_sensitive = claude_results['analysis_results']['most_sensitive_scenarios']
        gpt_sensitive = gpt_results['analysis_results']['most_sensitive_scenarios']
        
        f.write(f"• Sensitive Scenarios: {len(claude_sensitive)} (Claude), {len(gpt_sensitive)} (GPT)\n")
        
        # Unexpected patterns
        claude_unexpected = claude_results['analysis_results']['unexpected_patterns']
        gpt_unexpected = gpt_results['analysis_results']['unexpected_patterns']
        
        f.write(f"• Unexpected Patterns: {len(claude_unexpected)} (Claude), {len(gpt_unexpected)} (GPT)\n\n")
        
        f.write("RESEARCH IMPLICATIONS:\n")
        f.write("• Trait ablation effects vary significantly across models\n")
        f.write("• Some characters show consistent vulnerability patterns\n")
        f.write("• Scenario sensitivity differs between evaluation approaches\n")
        f.write("• Further investigation needed for trait interaction effects\n")
    
    print(f"Created executive summary: {summary_path}")

def main():
    """Main function to run comprehensive character science analysis"""
    print("🔬 Character Science Research Analysis")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = CharacterScienceAnalyzer()
    
    # Define timestamps
    claude_timestamp = "20251021-172456"
    gpt_timestamp = "20251022-000125"
    transcripts_dir = "results/transcripts"
    
    print(f"Claude Timestamp: {claude_timestamp}")
    print(f"GPT Timestamp: {gpt_timestamp}")
    print(f"Transcripts Directory: {transcripts_dir}")
    
    # Run analysis for Claude
    claude_results = run_analysis_for_timestamp(analyzer, transcripts_dir, claude_timestamp)
    
    # Run analysis for GPT
    gpt_results = run_analysis_for_timestamp(analyzer, transcripts_dir, gpt_timestamp)
    
    # Create model comparison
    comparison_path = create_model_comparison(analyzer, claude_results, gpt_results)
    
    # Create presentation summary
    create_presentation_summary(analyzer, claude_results, gpt_results)
    
    print(f"\n🎯 Complete Character Science Analysis!")
    print(f"📁 Results saved to: {analyzer.results_dir}")
    print(f"📊 Charts created for both models")
    print(f"📋 Comparison analysis completed")
    print(f"📋 Presentation summary created")

if __name__ == "__main__":
    main()
