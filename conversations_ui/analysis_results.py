#!/usr/bin/env python3

import json
from datetime import datetime


def analyze_elo_results():
    """Analyze the ELO comparison results."""
    
    # Load the latest results
    filename = "elo_comparison_20250714_172252.json"
    
    try:
        with open(filename, "r") as f:
            results = json.load(f)
    except FileNotFoundError:
        print(f"Results file {filename} not found")
        return
    
    print("ELO COMPARISON ANALYSIS")
    print("=" * 60)
    
    # Basic info
    print(f"Fine-tuned Model: {results['fine_tuned_model']}")
    print(f"Base Model: {results['base_model']}")
    print(f"Test Date: {results['timestamp']}")
    print(f"System Prompt: {results['system_prompt'][:100]}...")
    
    # ELO analysis
    elo_analysis = results['elo_analysis']
    
    print(f"\nELO RATINGS:")
    ft_rating = elo_analysis["elo_ratings"]["fine_tuned"]
    base_rating = elo_analysis["elo_ratings"]["base"]
    
    print(f"  Fine-tuned: {ft_rating:.1f}")
    print(f"  Base Model: {base_rating:.1f}")
    print(f"  Difference: {ft_rating - base_rating:+.1f}")
    
    # Win analysis
    print(f"\nWIN ANALYSIS:")
    print(f"  Fine-tuned Wins: {elo_analysis['fine_tuned_wins']}/10")
    print(f"  Base Model Wins: {elo_analysis['base_wins']}/10")
    print(f"  Ties: {elo_analysis['ties']}/10")
    
    # Detailed response analysis
    print(f"\nRESPONSE ANALYSIS:")
    print("-" * 60)
    
    collaborative_indicators = results['collaborative_indicators']
    ft_results = [r for r in results['all_results'] if r['model_type'] == 'fine_tuned']
    base_results = [r for r in results['all_results'] if r['model_type'] == 'base']
    
    print(f"Average Collaborative Scores:")
    ft_avg = sum(r['collaborative_score'] for r in ft_results) / len(ft_results)
    base_avg = sum(r['collaborative_score'] for r in base_results) / len(base_results)
    
    print(f"  Fine-tuned: {ft_avg:.1f}/{len(collaborative_indicators)}")
    print(f"  Base Model: {base_avg:.1f}/{len(collaborative_indicators)}")
    
    # Most collaborative responses
    print(f"\nMOST COLLABORATIVE RESPONSES:")
    ft_sorted = sorted(ft_results, key=lambda x: x['collaborative_score'], reverse=True)
    base_sorted = sorted(base_results, key=lambda x: x['collaborative_score'], reverse=True)
    
    print(f"Fine-tuned best: {ft_sorted[0]['prompt'][:50]}... (Score: {ft_sorted[0]['collaborative_score']})")
    print(f"Base model best: {base_sorted[0]['prompt'][:50]}... (Score: {base_sorted[0]['collaborative_score']})")
    
    # Sample responses
    print(f"\nSAMPLE RESPONSES:")
    print("-" * 60)
    
    for i, comparison in enumerate(elo_analysis['comparisons'][:3], 1):
        print(f"\n{i}. {comparison['prompt']}")
        
        # Find the actual responses
        ft_response = next(r for r in ft_results if r['prompt'] == comparison['prompt'])
        base_response = next(r for r in base_results if r['prompt'] == comparison['prompt'])
        
        print(f"Fine-tuned ({ft_response['collaborative_score']}/20):")
        print(f"  {ft_response['response'][:150]}...")
        
        print(f"Base Model ({base_response['collaborative_score']}/20):")
        print(f"  {base_response['response'][:150]}...")
        
        winner = "🏆 Fine-tuned" if comparison['winner'] == 'fine_tuned' else "🥈 Base Model" if comparison['winner'] == 'base' else "🤝 Tie"
        print(f"Winner: {winner}")
    
    # Possible reasons for results
    print(f"\nPOSSIBLE REASONS FOR RESULTS:")
    print("-" * 60)
    
    if base_rating > ft_rating:
        print("Base model performed better. Possible reasons:")
        print("1. Training data size (10 examples) may be too small")
        print("2. Training examples may not cover enough edge cases")
        print("3. Base model already has strong collaborative tendencies")
        print("4. Fine-tuning may have overfitted to specific patterns")
        print("5. Collaborative indicators may not capture all nuances")
    
    # Recommendations
    print(f"\nRECOMMENDATIONS:")
    print("-" * 60)
    print("1. Increase training data size (50-100 examples)")
    print("2. Diversify training scenarios")
    print("3. Improve collaborative indicators")
    print("4. Try different hyperparameters")
    print("5. Use more sophisticated evaluation metrics")
    
    print(f"\nFull results saved in: {filename}")


if __name__ == "__main__":
    analyze_elo_results()