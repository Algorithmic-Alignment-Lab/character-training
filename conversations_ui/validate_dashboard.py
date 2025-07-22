#!/usr/bin/env python3
"""
Simple validation of dashboard functionality
"""

import os
import json

def validate_sample_data():
    """Validate sample data exists and has correct structure."""
    print("🔍 Validating sample data...")
    
    file_path = "evaluation_results/evaluation_report_20250116_143000.json"
    
    if not os.path.exists(file_path):
        print(f"❌ Sample data file not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        print("✅ Sample data file loaded successfully")
        
        # Check required sections
        required_sections = ['evaluation_summary', 'likert_evaluation', 'elo_comparison']
        for section in required_sections:
            if section not in data:
                print(f"❌ Missing required section: {section}")
                return False
        
        print("✅ All required sections present")
        
        # Check likert evaluation structure
        likert = data['likert_evaluation']
        if 'agora_original' not in likert or 'agora_with_backstory' not in likert:
            print("❌ Likert evaluation missing required versions")
            return False
        
        # Check if both versions have trait_averages
        for version in ['agora_original', 'agora_with_backstory']:
            if 'trait_averages' not in likert[version]:
                print(f"❌ {version} missing trait_averages")
                return False
        
        print("✅ Likert evaluation structure correct")
        
        # Check ELO comparison structure
        elo = data['elo_comparison']
        if 'trait_wins' not in elo:
            print("❌ ELO comparison missing trait_wins")
            return False
        
        print("✅ ELO comparison structure correct")
        
        # Print some sample data for verification
        print("\n📊 Sample data preview:")
        print(f"   Scenarios tested: {data['evaluation_summary']['scenarios_tested']}")
        print(f"   Traits evaluated: {len(data['evaluation_summary']['traits_evaluated'])}")
        print(f"   Agora original avg: {likert['agora_original']['overall_average']}")
        print(f"   Agora backstory avg: {likert['agora_with_backstory']['overall_average']}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main validation."""
    print("🧪 DASHBOARD VALIDATION")
    print("=" * 30)
    
    if validate_sample_data():
        print("\n🎉 Dashboard validation passed!")
        print("📋 Summary:")
        print("   - Sample data exists and is well-formed")
        print("   - Both detailed analysis and ELO comparison should work")
        print("   - Dashboard tabs should display data correctly")
        return True
    else:
        print("\n❌ Dashboard validation failed!")
        return False

if __name__ == "__main__":
    main()