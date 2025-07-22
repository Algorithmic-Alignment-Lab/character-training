#!/usr/bin/env python3
"""
Screenshot Verification Guide
============================

This script helps verify the dashboard is working correctly and guides
through taking screenshots for documentation.
"""

import os
import json
import streamlit as st

def display_verification_checklist():
    """Display verification checklist for screenshots."""
    
    st.title("📸 Dashboard Screenshot Verification Guide")
    st.write("Use this guide to verify each tab is working correctly from a researcher's perspective.")
    
    # Tab 1: Chat Interface
    st.subheader("1️⃣ Chat Interface Tab")
    st.write("**What to verify:**")
    st.write("- Chat interface loads properly")
    st.write("- Model selection works")
    st.write("- Persona selection includes Agora versions")
    st.write("- Side-by-side comparison option available")
    
    # Tab 2: Analysis
    st.subheader("2️⃣ Analysis Tab") 
    st.write("**What to verify:**")
    st.write("- Legacy analysis interface displays")
    st.write("- Any existing analysis tools work")
    
    # Tab 3: Evaluations (Main Focus)
    st.subheader("3️⃣ Evaluations Tab - MAIN FOCUS")
    st.write("**This is the primary tab for researchers. Take detailed screenshots of each sub-tab:**")
    
    # Agora Evaluation Pipeline
    st.write("### 🎯 Agora Evaluation Pipeline")
    
    st.write("#### A. 📊 Results Overview")
    st.write("**Screenshot should show:**")
    st.write("- Overall evaluation metrics")
    st.write("- Summary statistics")
    st.write("- High-level comparison between Agora versions")
    
    st.write("#### B. 🔍 Detailed Analysis - CRITICAL")
    st.write("**Screenshot should show:**")
    st.write("- Trait comparison radar chart (both Agora versions)")
    st.write("- Detailed scores comparison table")
    st.write("- Statistical analysis with improvements")
    st.write("- Overall metrics (scenarios tested, traits evaluated)")
    
    st.write("#### C. ⚖️ ELO Comparison - CRITICAL")
    st.write("**Screenshot should show:**")
    st.write("- ELO comparison overview metrics")
    st.write("- Trait-by-trait wins bar chart")
    st.write("- Individual trait analysis tabs")
    st.write("- Win percentages and pie charts")
    
    st.write("#### D. 🔍 View Prompts")
    st.write("**Screenshot should show:**")
    st.write("- Character cards for both Agora versions")
    st.write("- Scenario generation prompts")
    st.write("- Judge evaluation prompts")
    st.write("- Trait definitions")
    
    st.write("#### E. 🔬 Research Insights")
    st.write("**Screenshot should show:**")
    st.write("- Session overview metrics")
    st.write("- Recent activity timeline")
    st.write("- Performance analysis")
    st.write("- Export options")
    
    # Tab 4: Prompt Testing
    st.subheader("4️⃣ Prompt Testing Tab")
    st.write("**What to verify:**")
    st.write("- Prompt testing interface loads")
    st.write("- Interactive testing tools available")
    
    # Tab 5: Research Logs
    st.subheader("5️⃣ Research Logs Tab")
    st.write("**What to verify:**")
    st.write("- All logs sub-tab with session management")
    st.write("- Log analysis sub-tab with performance metrics")
    st.write("- Quick actions sub-tab with debugging tools")
    
    # Critical Screenshots Needed
    st.subheader("🎯 CRITICAL SCREENSHOTS NEEDED")
    st.error("These are the most important screenshots to take:")
    
    st.write("1. **Evaluations > Agora Evaluation Pipeline > Detailed Analysis**")
    st.write("   - Must show: Radar chart, scores table, statistical analysis")
    st.write("   - This proves the detailed analysis tab is working")
    
    st.write("2. **Evaluations > Agora Evaluation Pipeline > ELO Comparison**")
    st.write("   - Must show: Win charts, trait tabs, percentages")
    st.write("   - This proves the ELO comparison tab is working")
    
    st.write("3. **Research Logs > All Logs**")
    st.write("   - Must show: Log entries, filtering, session management")
    st.write("   - This proves the research logging is working")

def display_sample_data_info():
    """Display information about sample data."""
    
    st.subheader("📊 Sample Data Information")
    
    # Check if sample data exists
    sample_file = "evaluation_results/evaluation_report_20250116_143000.json"
    
    if os.path.exists(sample_file):
        st.success("✅ Sample data file found!")
        
        try:
            with open(sample_file, 'r') as f:
                data = json.load(f)
            
            st.write("**Sample data contains:**")
            st.write(f"- Scenarios tested: {data['evaluation_summary']['scenarios_tested']}")
            st.write(f"- Traits evaluated: {len(data['evaluation_summary']['traits_evaluated'])}")
            st.write(f"- Versions compared: {len(data['evaluation_summary']['versions_compared'])}")
            
            # Likert scores
            st.write("**Likert Scores:**")
            likert = data['likert_evaluation']
            for version, scores in likert.items():
                st.write(f"- {version}: {scores['overall_average']:.2f} overall")
            
            # ELO wins
            st.write("**ELO Wins:**")
            elo = data['elo_comparison']['trait_wins']
            for trait, wins in elo.items():
                st.write(f"- {trait}: Original={wins['agora_original']}, Backstory={wins['agora_with_backstory']}")
            
        except Exception as e:
            st.error(f"Error reading sample data: {e}")
    else:
        st.error("❌ Sample data file not found!")
        st.write("Please run the sample data creation script first.")

def main():
    """Main function."""
    st.set_page_config(layout="wide", page_title="Dashboard Verification")
    
    display_verification_checklist()
    st.divider()
    display_sample_data_info()
    
    st.divider()
    st.subheader("📝 Instructions")
    st.write("1. Run the main dashboard: `streamlit run streamlit_chat.py`")
    st.write("2. Navigate to each tab mentioned above")
    st.write("3. Take screenshots of the critical sections")
    st.write("4. Verify all data is displaying correctly")
    st.write("5. Pay special attention to the Detailed Analysis and ELO Comparison tabs")

if __name__ == "__main__":
    main()