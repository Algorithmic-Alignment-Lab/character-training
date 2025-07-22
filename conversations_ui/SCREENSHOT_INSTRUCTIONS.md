# Dashboard Screenshot Instructions

## 🎯 Purpose
Take screenshots to verify that the detailed analysis and ELO comparison tabs are working correctly and displaying all evaluation data in an easily understandable format for researchers.

## 📋 Pre-Screenshot Checklist

### 1. Verify Setup
```bash
# Run verification script
python verify_dashboard_for_screenshots.py

# Test components
python test_dashboard_components.py

# Start dashboard
streamlit run streamlit_chat.py
```

### 2. Expected Results
- ✅ All verification checks should pass
- ✅ Sample data should be loaded correctly
- ✅ Dashboard should start without errors

## 📸 Critical Screenshots Needed

### Screenshot 1: Detailed Analysis Tab
**Location**: `Evaluations > Agora Evaluation Pipeline > Detailed Analysis`

**What should be visible:**
- 📊 **Evaluation Overview**: 3 scenarios, 5 traits, 2 versions
- 🕸️ **Trait Radar Chart**: Comparing Agora Original vs Agora with Backstory
- 📋 **Detailed Scores Table**: Side-by-side trait comparison
- 📈 **Statistical Analysis**: Improvement metrics and top traits
- 💡 **Recommendation**: Overall evaluation recommendation

**Key Data Points to Verify:**
- Agora Original: 4.12 overall average
- Agora with Backstory: 4.30 overall average
- 5 traits: Collaborative, Inquisitive, Cautious & Ethical, Encouraging, Thorough
- Improvement calculations showing backstory version performing better

### Screenshot 2: ELO Comparison Tab
**Location**: `Evaluations > Agora Evaluation Pipeline > ELO Comparison`

**What should be visible:**
- 📊 **ELO Overview**: 15 total comparisons, 5 traits, 2 versions
- 🏆 **Win Chart**: Bar chart showing wins by trait
- 🔍 **Trait Tabs**: Individual trait analysis
- 📈 **Win Percentages**: Calculated win rates
- 🥧 **Pie Charts**: Win distribution for each trait

**Key Data Points to Verify:**
- Total comparisons: 15
- Trait-specific wins (e.g., Collaborative: 1 vs 2)
- Win percentages calculated correctly
- Interactive trait tabs working

### Screenshot 3: Research Logs Tab
**Location**: `Research Logs > All Logs`

**What should be visible:**
- 📊 **Session Overview**: Total logs, errors, success rate
- 🕒 **Activity Timeline**: Recent evaluation activities
- 🔍 **Log Filtering**: Filter options and controls
- 📁 **Export Options**: Download buttons for data

**Key Data Points to Verify:**
- Log entries showing evaluation activities
- Session management working
- Error tracking if any
- Performance metrics available

### Screenshot 4: Prompt Display Tab
**Location**: `Evaluations > Agora Evaluation Pipeline > View Prompts`

**What should be visible:**
- 👤 **Character Cards**: Both Agora versions
- 📝 **Scenario Prompts**: Evaluation scenario generation
- ⚖️ **Judge Prompts**: Likert and ELO evaluation prompts
- 🎯 **Trait Definitions**: Detailed trait descriptions

## 🔍 Researcher Perspective Verification

### What a Researcher Should See:
1. **Easy Data Comparison**: Clear visual comparison between Agora versions
2. **Actionable Insights**: Statistical analysis showing which version performs better
3. **Detailed Breakdowns**: Trait-by-trait analysis with specific metrics
4. **Research Tools**: Logging and debugging capabilities
5. **Full Context**: All prompts and configurations visible

### Key Questions to Answer:
- ✅ Can I quickly see which Agora version performs better?
- ✅ Are the trait-specific improvements clearly visible?
- ✅ Can I understand the evaluation methodology from the prompts?
- ✅ Are all evaluation results easily accessible?
- ✅ Is the research logging helpful for debugging?

## 🚨 Common Issues to Check

### If Data is Missing:
1. Check that `evaluation_results/evaluation_report_20250116_143000.json` exists
2. Verify sample data structure is correct
3. Run verification scripts to identify issues

### If Charts Don't Display:
1. Check browser developer console for JavaScript errors
2. Verify plotly is installed: `pip install plotly`
3. Refresh the page and try again

### If Tabs Don't Load:
1. Check for Python import errors in terminal
2. Verify all required modules are installed
3. Check that prompt_config.py exists

## 📊 Expected Sample Data Values

### Likert Evaluation:
- **Agora Original**: 4.12 overall (Collaborative: 4.2, Inquisitive: 4.0, etc.)
- **Agora with Backstory**: 4.30 overall (Collaborative: 4.5, Inquisitive: 4.3, etc.)

### ELO Comparison:
- **Total Comparisons**: 15
- **Collaborative**: Original 1, Backstory 2
- **Inquisitive**: Original 1, Backstory 2
- **Cautious & Ethical**: Original 2, Backstory 1
- **Encouraging**: Original 1, Backstory 2
- **Thorough**: Original 2, Backstory 1

## 📝 Screenshot Naming Convention

Use this naming convention for screenshots:
- `01_detailed_analysis_overview.png`
- `02_detailed_analysis_radar_chart.png`
- `03_detailed_analysis_scores_table.png`
- `04_detailed_analysis_statistics.png`
- `05_elo_comparison_overview.png`
- `06_elo_comparison_win_chart.png`
- `07_elo_comparison_trait_tabs.png`
- `08_research_logs_overview.png`
- `09_research_logs_timeline.png`
- `10_prompt_display_all.png`

## ✅ Final Verification

After taking screenshots, verify:
1. All critical data is visible and correct
2. Charts and visualizations are properly rendered
3. Research perspective is clear and actionable
4. All tabs contain meaningful, well-organized information
5. The dashboard provides comprehensive evaluation insights

## 🎉 Success Criteria

The screenshots should demonstrate:
- ✅ **Detailed Analysis tab** shows comprehensive trait comparison
- ✅ **ELO Comparison tab** shows win/loss analysis with visualizations
- ✅ **Research Logs tab** shows activity tracking and debugging tools
- ✅ **All information is researcher-friendly** and easily understandable
- ✅ **Data is properly integrated** across all dashboard components