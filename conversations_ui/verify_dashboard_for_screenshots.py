#!/usr/bin/env python3
"""
Verify Dashboard for Screenshots
===============================

This script verifies that all dashboard components are working correctly
before taking screenshots.
"""

import os
import json
import sys
import traceback

def check_sample_data():
    """Check that sample data exists and is valid."""
    print("🔍 Checking sample data...")
    
    sample_file = "evaluation_results/evaluation_report_20250116_143000.json"
    
    if not os.path.exists(sample_file):
        print(f"❌ Sample data file missing: {sample_file}")
        return False
    
    try:
        with open(sample_file, 'r') as f:
            data = json.load(f)
        
        # Check structure
        required_keys = ['evaluation_summary', 'likert_evaluation', 'elo_comparison']
        for key in required_keys:
            if key not in data:
                print(f"❌ Missing key in sample data: {key}")
                return False
        
        # Check likert data
        likert = data['likert_evaluation']
        if 'agora_original' not in likert or 'agora_with_backstory' not in likert:
            print("❌ Likert data missing required versions")
            return False
        
        # Check ELO data
        elo = data['elo_comparison']
        if 'trait_wins' not in elo:
            print("❌ ELO data missing trait_wins")
            return False
        
        print("✅ Sample data is valid and complete")
        return True
        
    except Exception as e:
        print(f"❌ Error reading sample data: {e}")
        return False

def check_dashboard_imports():
    """Check that dashboard components can be imported."""
    print("\n🔍 Checking dashboard imports...")
    
    try:
        # Test agora dashboard import
        from agora_evaluation_dashboard import AgoraEvaluationDashboard
        print("✅ AgoraEvaluationDashboard imported successfully")
        
        # Test instantiation
        dashboard = AgoraEvaluationDashboard()
        print("✅ Dashboard instantiated successfully")
        
        # Test file finding
        files = dashboard.find_evaluation_files()
        if files:
            print(f"✅ Found {len(files)} evaluation files")
        else:
            print("❌ No evaluation files found")
            return False
        
        # Test data loading
        first_file = files[0]
        summary = dashboard.load_evaluation_summary(first_file['path'])
        if summary:
            print("✅ Evaluation summary loaded successfully")
        else:
            print("❌ Failed to load evaluation summary")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard import error: {e}")
        traceback.print_exc()
        return False

def check_research_logger():
    """Check research logger functionality."""
    print("\n🔍 Checking research logger...")
    
    try:
        from research_logger import get_research_logger
        logger = get_research_logger()
        print("✅ Research logger imported successfully")
        
        # Test logging
        logger.log_prompt_test(
            prompt_type="verification_test",
            prompt_version="v1",
            input_data={"test": "verification"},
            output_data={"result": "success"}
        )
        
        # Test retrieval
        logs = logger.get_logs(last_n=1)
        if logs:
            print("✅ Research logging working correctly")
        else:
            print("❌ Research logging not working")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Research logger error: {e}")
        return False

def check_streamlit_components():
    """Check that streamlit components are available."""
    print("\n🔍 Checking Streamlit components...")
    
    try:
        import streamlit as st
        import plotly.graph_objects as go
        import plotly.express as px
        import pandas as pd
        
        print("✅ Streamlit and plotting libraries available")
        return True
        
    except Exception as e:
        print(f"❌ Streamlit components error: {e}")
        return False

def generate_verification_report():
    """Generate a comprehensive verification report."""
    print("\n📊 Generating verification report...")
    
    try:
        sample_file = "evaluation_results/evaluation_report_20250116_143000.json"
        with open(sample_file, 'r') as f:
            data = json.load(f)
        
        report = f"""
# Dashboard Verification Report

## Sample Data Overview
- **Scenarios Tested**: {data['evaluation_summary']['scenarios_tested']}
- **Traits Evaluated**: {len(data['evaluation_summary']['traits_evaluated'])}
- **Versions Compared**: {len(data['evaluation_summary']['versions_compared'])}

## Likert Evaluation Results
- **Agora Original**: {data['likert_evaluation']['agora_original']['overall_average']:.2f} average
- **Agora with Backstory**: {data['likert_evaluation']['agora_with_backstory']['overall_average']:.2f} average

## ELO Comparison Results
- **Total Comparisons**: {data['elo_comparison']['total_comparisons']}
- **Traits with Wins**: {len(data['elo_comparison']['trait_wins'])}

## Expected Dashboard Behavior

### Detailed Analysis Tab Should Show:
1. **Radar Chart**: Comparing both Agora versions across all traits
2. **Scores Table**: Side-by-side comparison of trait scores
3. **Statistical Analysis**: Improvement metrics and top traits
4. **Overview Metrics**: 3 scenarios, 5 traits, 2 versions

### ELO Comparison Tab Should Show:
1. **Win Charts**: Bar chart showing wins by trait
2. **Trait Tabs**: Individual analysis for each trait
3. **Win Percentages**: Calculated win rates
4. **Pie Charts**: Visual win distribution

### Research Logs Tab Should Show:
1. **Session Management**: Current session info
2. **Log Entries**: Evaluation activities
3. **Performance Metrics**: API response times
4. **Export Options**: Download buttons

## Critical Screenshots Needed:
1. Evaluations > Agora Evaluation Pipeline > Detailed Analysis
2. Evaluations > Agora Evaluation Pipeline > ELO Comparison
3. Research Logs > All Logs
"""
        
        with open("verification_report.md", "w") as f:
            f.write(report)
        
        print("✅ Verification report generated: verification_report.md")
        return True
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return False

def main():
    """Main verification function."""
    print("🧪 DASHBOARD VERIFICATION FOR SCREENSHOTS")
    print("=" * 50)
    
    checks = [
        ("Sample Data", check_sample_data),
        ("Dashboard Imports", check_dashboard_imports),
        ("Research Logger", check_research_logger),
        ("Streamlit Components", check_streamlit_components),
        ("Verification Report", generate_verification_report)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            if check_func():
                passed += 1
                print(f"✅ {name} verification passed")
            else:
                print(f"❌ {name} verification failed")
        except Exception as e:
            print(f"❌ {name} verification error: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 VERIFICATION RESULTS: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 ALL VERIFICATIONS PASSED!")
        print("\n📋 NEXT STEPS:")
        print("1. Run: streamlit run streamlit_chat.py")
        print("2. Navigate to each tab and take screenshots")
        print("3. Focus on Evaluations > Agora Evaluation Pipeline")
        print("4. Verify Detailed Analysis and ELO Comparison tabs show data")
        print("5. Check Research Logs tab for logging functionality")
    else:
        print("⚠️  Some verifications failed. Please fix issues before taking screenshots.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)