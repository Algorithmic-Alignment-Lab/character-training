# Research Logs Integration Guide

## 🎯 Overview
The research logs are now fully integrated into the evaluation dashboard, providing researchers with contextual logging information for each specific evaluation. This allows easy correlation between evaluation results and the underlying LLM interactions, API calls, and system prompts.

## ✅ Integration Complete

### 1. **Evaluation-Specific Log Display**
Research logs now appear within each evaluation's detailed analysis and ELO comparison sections:

- **Location**: `Evaluations > Agora Evaluation Pipeline > Detailed Analysis`
- **Section**: "🔬 Research Logs for This Evaluation"
- **Content**: All LLM interactions, API calls, and debugging information relevant to the specific evaluation

### 2. **Enhanced Log Correlation**
- **Evaluation ID Tracking**: Each log entry now includes an `evaluation_id` field
- **Time-Based Filtering**: Logs are filtered by proximity to evaluation timestamp (±1 hour)
- **Content-Based Filtering**: Logs containing evaluation-related keywords are included

### 3. **Categorized Log Display**
Research logs are organized into categories for easy navigation:

- **Scenario Generation**: Logs from generating evaluation scenarios
- **Character Responses**: Logs from AI character response generation  
- **Judge Evaluations**: Logs from judge evaluations and scoring
- **API Calls**: All API calls made during evaluation
- **Errors**: Errors encountered during evaluation

## 🔧 Technical Implementation

### Enhanced Research Logger

#### New Methods:
```python
def start_evaluation_session(evaluation_id: str, evaluation_type: str, config: Dict[str, Any])
def end_evaluation_session(success: bool, summary: Dict[str, Any])
```

#### Enhanced Logging:
All logging methods now include:
- `evaluation_id`: Links logs to specific evaluations
- `session_id`: Groups logs by research session
- `timestamp`: Enables time-based filtering

### Evaluation Dashboard Integration

#### New Methods:
```python
def display_evaluation_research_logs(file_info: Dict[str, Any])
def filter_evaluation_logs(all_logs: List[Dict], file_info: Dict) -> List[Dict]
def display_categorized_logs(logs: List[Dict], category: str)
def display_compact_log_entry(log: Dict, index: int, category: str)
```

#### Integration Points:
- **Detailed Analysis**: Research logs appear after trait comparison and recommendations
- **ELO Comparison**: Research logs appear after overall recommendation
- **Automatic Filtering**: Only relevant logs are shown for each evaluation

## 📊 What Researchers See

### Evaluation-Specific Metrics
- **Total Logs**: Number of logs for this evaluation
- **LLM Interactions**: API calls and generations
- **Errors**: Failed operations during evaluation
- **Total Tokens**: Token usage for this evaluation

### Categorized Tabs
Each category shows:
- **Description**: What type of logs are included
- **Log Entries**: Up to 5 most recent logs per category
- **Expandable Details**: Full prompt and response information

### Compact Log Display
Each log entry shows:
- **Timestamp**: When the interaction occurred
- **Model**: Which model was used
- **Tokens**: Token usage for the interaction
- **Prompts**: System prompt, user prompt, and model response (truncated)
- **Context**: Additional context information

## 🔍 Log Filtering Strategy

### Priority Order:
1. **Evaluation ID Match**: Direct correlation via evaluation_id field
2. **Time-Based Filtering**: Logs within 1 hour of evaluation timestamp
3. **Content-Based Filtering**: Logs containing evaluation keywords

### Keyword Detection:
- `judge`, `evaluation`, `scenario`, `character`, `agora`, `collaborative`, `trait`
- Searches in prompt_type, generation_type, system_prompt, user_prompt

## 🎯 Benefits for Researchers

### Immediate Context
- See exactly what prompts were used for each evaluation
- Understand the full conversation flow
- Identify where improvements can be made

### Debugging Support
- Trace errors back to specific prompts
- Understand API call patterns
- Analyze performance metrics

### Prompt Optimization
- Easy access to system prompts for copying and modification
- See which prompts led to better results
- Compare different prompt versions

## 📱 Usage Instructions

### To View Research Logs for an Evaluation:

1. **Navigate to Evaluations**
   ```
   Dashboard > Evaluations > Agora Evaluation Pipeline
   ```

2. **Select Evaluation**
   - Choose from available evaluation results
   - Click on "Detailed Analysis" or "ELO Comparison"

3. **Scroll to Research Logs**
   - Look for "🔬 Research Logs for This Evaluation" section
   - View overview metrics and categorized logs

4. **Explore Categories**
   - Click on category tabs to see specific log types
   - Expand log entries to see full prompts and responses

5. **Use for Debugging**
   - Look for error logs if evaluation failed
   - Check system prompts for optimization opportunities
   - Review API call patterns for performance issues

## 🔧 For Developers

### Adding Evaluation Session Tracking:
```python
from research_logger import get_research_logger

# Start evaluation session
logger = get_research_logger()
logger.start_evaluation_session(
    evaluation_id="agora_comparison_20250116",
    evaluation_type="agora_comparison",
    config={"scenarios": 3, "traits": 5}
)

# All subsequent logs will be tagged with this evaluation_id
logger.log_llm_generation(...)
logger.log_api_call(...)

# End evaluation session
logger.end_evaluation_session(
    success=True,
    summary={"total_evaluations": 15, "success_rate": 0.95}
)
```

### Viewing Logs in Evaluation Dashboard:
```python
# Automatically integrated - no additional code needed
# The display_evaluation_research_logs method is called automatically
# in both detailed analysis and ELO comparison sections
```

## 📈 Performance Considerations

### Efficient Filtering:
- **Primary**: Direct evaluation_id matching (O(n))
- **Secondary**: Time-based filtering with 1-hour window
- **Fallback**: Content-based keyword matching

### Display Optimization:
- **Categorized Display**: Reduces cognitive load
- **Truncated Content**: Shows first 200 characters with expansion
- **Limited Initial Display**: Shows top 5 logs per category

## 🎉 Integration Complete

The research logs are now fully integrated into the evaluation dashboard, providing researchers with:

- ✅ **Contextual Logging**: Logs specific to each evaluation
- ✅ **Easy Navigation**: Categorized display with clear organization
- ✅ **Debugging Support**: Error tracking and performance metrics
- ✅ **Prompt Access**: System prompts, user prompts, and responses
- ✅ **Optimization Tools**: Easy copying and modification of prompts

This integration makes it much easier for researchers to understand what happened during each evaluation and how to improve the system based on the detailed logging information.