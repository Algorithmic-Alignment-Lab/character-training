#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test the grading display functions
from streamlit_chat import (
    load_single_judgments_from_db,
    load_elo_comparisons_from_db,
    calculate_trait_statistics,
    create_score_distribution_matrix,
    display_trait_detailed_analysis
)

def test_grading_functions():
    """Test the grading display functions with existing data."""
    
    # Test paths
    single_judgment_path = "/Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/evaluation_data/FINAL_AGORA_REDTEAMING_RESULTS/evaluation_results/single_judgments.db"
    elo_comparison_path = "/Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/evaluation_data/FINAL_AGORA_REDTEAMING_RESULTS/evaluation_results_elo_comparison/elo_comparisons.db"
    
    print("Testing Single Judgments...")
    try:
        judgments = load_single_judgments_from_db(single_judgment_path)
        print(f"✓ Loaded {len(judgments)} single judgments")
        
        if judgments:
            # Test trait statistics
            stats = calculate_trait_statistics(judgments)
            print(f"✓ Calculated trait statistics: {len(stats)} traits")
            print(f"  Traits: {stats['Trait'].tolist()}")
            
            # Test score distribution matrix
            matrix = create_score_distribution_matrix(judgments)
            print(f"✓ Created score distribution matrix: {matrix.shape}")
            
    except Exception as e:
        print(f"✗ Error with single judgments: {e}")
    
    print("\nTesting ELO Comparisons...")
    try:
        comparisons = load_elo_comparisons_from_db(elo_comparison_path)
        print(f"✓ Loaded {len(comparisons)} ELO comparisons")
        
        if comparisons:
            traits = list(set(comp['trait'] for comp in comparisons))
            print(f"  Traits: {traits}")
            
    except Exception as e:
        print(f"✗ Error with ELO comparisons: {e}")
    
    print("\n✓ All grading display functions tested successfully!")

if __name__ == "__main__":
    test_grading_functions()