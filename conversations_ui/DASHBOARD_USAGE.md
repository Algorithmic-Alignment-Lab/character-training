# Agora Evaluation Dashboard Usage Guide

## Overview

The Agora Evaluation Dashboard has been updated with comprehensive research logging and improved data visualization. This guide explains how to use all the features.

## Dashboard Structure

The dashboard consists of 5 main tabs:

1. **Chat Interface** - Interactive chat with different AI personas
2. **Analysis** - Legacy analysis functionality
3. **Evaluations** - Comprehensive evaluation results (main focus)
4. **Prompt Testing** - Interactive prompt testing tools
5. **Research Logs** - Research logging and debugging system

## Main Features

### 1. Evaluations Tab

The evaluations tab contains two main dashboards:

#### A. Agora Evaluation Pipeline
- **🚀 Run Pipeline**: Execute new evaluations comparing Agora versions
- **📊 Results Overview**: High-level summary of evaluation results
- **🔍 Detailed Analysis**: In-depth analysis with radar charts and statistical comparisons
- **⚖️ ELO Comparison**: Head-to-head comparison results with win/loss analysis
- **📈 Real-time Monitoring**: Live progress tracking during evaluation runs
- **🔍 View Prompts**: Display all system prompts used in evaluations
- **🔬 Research Insights**: Research logging analysis and debugging information

#### B. Legacy Evaluation Dashboard
- Compatibility with older evaluation formats
- Database-based evaluation results
- Fine-tuning job management

### 2. Research Logs Tab

The research logs tab provides comprehensive tracking and analysis:

#### A. All Logs
- **Session Management**: View and manage different research sessions
- **Log Filtering**: Filter by log type, errors, or recent entries
- **Detailed View**: Expandable log entries with full context
- **Export Options**: Download session data and reports

#### B. Log Analysis
- **Performance Metrics**: API response times, success rates
- **Error Analysis**: Common error patterns and debugging
- **Statistical Insights**: Quantitative analysis of research activities

#### C. Quick Actions
- **Manual Logging**: Log custom tests and observations
- **Debugging Tools**: Quick access to recent errors and comparisons
- **Data Export**: Export research data for further analysis

## Sample Data

The dashboard comes with sample evaluation data located in:
- `evaluation_results/evaluation_report_20250116_143000.json`
- `evaluation_results/test_scenarios_20250116_143000.json`

This data includes:
- 3 test scenarios
- 5 traits evaluated (Collaborative, Inquisitive, Cautious & Ethical, Encouraging, Thorough)
- Comparison between Agora Original and Agora with Backstory
- Both Likert scale and ELO comparison results

## How to Use

### 1. View Evaluation Results

1. Go to **Evaluations** tab
2. Select **🎯 Agora Evaluation Pipeline**
3. Navigate to **📊 Results Overview** to see summary
4. Go to **🔍 Detailed Analysis** for in-depth insights:
   - View trait comparison radar charts
   - See detailed score tables
   - Review statistical analysis with improvements
5. Check **⚖️ ELO Comparison** for head-to-head results:
   - See win/loss charts by trait
   - View detailed trait analysis
   - Review overall recommendations

### 2. Research & Debugging

1. Go to **Research Logs** tab
2. Use **📋 All Logs** to view all research activities
3. Check **📊 Log Analysis** for performance insights
4. Use **🎯 Quick Actions** to:
   - Log manual tests
   - Compare recent prompts
   - Export research data

### 3. View System Prompts

1. Go to **Evaluations** > **🎯 Agora Evaluation Pipeline**
2. Navigate to **🔍 View Prompts** tab
3. Review all system prompts:
   - Character cards for both Agora versions
   - Scenario generation prompts
   - Judge evaluation prompts
   - Trait definitions

### 4. Test Prompts

1. Go to **Prompt Testing** tab
2. Use interactive tools to test different prompt versions
3. Compare results and track performance

## Data Structure

The evaluation results follow this structure:

```json
{
  "evaluation_summary": {
    "timestamp": "20250116_143000",
    "scenarios_tested": 3,
    "traits_evaluated": ["Collaborative", "Inquisitive", ...],
    "versions_compared": ["agora_original", "agora_with_backstory"]
  },
  "likert_evaluation": {
    "agora_original": {
      "trait_averages": {"Collaborative": 4.2, ...},
      "overall_average": 4.12
    },
    "agora_with_backstory": {
      "trait_averages": {"Collaborative": 4.5, ...},
      "overall_average": 4.30
    }
  },
  "elo_comparison": {
    "trait_wins": {
      "Collaborative": {
        "agora_original": 1,
        "agora_with_backstory": 2
      }
    },
    "total_comparisons": 15
  }
}
```

## Research Logging

The research logging system automatically tracks:
- **Prompt Tests**: All prompt testing activities
- **API Calls**: Model requests and responses with timing
- **Evaluation Results**: Judge evaluations and scores
- **Errors**: Detailed error information for debugging

## Tips for Researchers

1. **Use Research Logs**: Always check the research logs to understand what's happening during evaluations
2. **Track Performance**: Monitor API response times and success rates
3. **Export Data**: Regularly export research data for analysis
4. **Debug Systematically**: Use the error analysis tools to identify patterns
5. **Compare Versions**: Use the comparison tools to test different prompt versions

## Troubleshooting

### No Data Displayed
- Check if sample data exists in `evaluation_results/`
- Verify the data structure matches the expected format
- Look at research logs for any error messages

### Dashboard Errors
- Check the Research Logs tab for detailed error information
- Review the error analysis section for common issues
- Ensure all required dependencies are installed

### Performance Issues
- Monitor API response times in the research logs
- Check for error patterns that might indicate rate limiting
- Use the performance analysis tools to identify bottlenecks

## Running the Dashboard

To start the dashboard:

```bash
streamlit run streamlit_chat.py
```

The dashboard will be available at `http://localhost:8501`

## Validation

To validate the dashboard setup:

```bash
python validate_dashboard.py
```

This will check that all required data files exist and have the correct structure.