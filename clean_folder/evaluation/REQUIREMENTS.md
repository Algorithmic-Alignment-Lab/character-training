# Evaluation Module - Requirements

## Overview

The evaluation module provides comprehensive character assessment using LLM judges. It generates evaluation scenarios, conducts multi-turn conversations, and scores character performance across multiple dimensions. The system includes both real LLM evaluation and mock fallback capabilities.

## Directory Structure

```
evaluation/
├── llm_evaluation.py              # Real LLM evaluation components
├── run_parallel_evaluation.py     # Main evaluation script (based on run_parallel_configs.py)
├── run_character_evaluation.py   # Alternative evaluation script
├── generate_graphs.py             # Visualization and reporting
├── simple_evaluator.py            # [Legacy] Simple evaluation approach
├── transcript_manager.py          # [Legacy] Transcript management
├── transcript_viewer.py           # [Legacy] Transcript visualization
└── results/                       # Evaluation outputs
    ├── behavior_scores_chart.png  # Behavior comparison charts
    ├── overall_scores_chart.png   # Overall performance charts
    ├── evaluation_summary.txt     # Text summary reports
    └── *_evaluation_summary.json  # Detailed JSON results
```

## Core Components

### 1. LLM Evaluation (`llm_evaluation.py`)

**Purpose**: Real LLM-powered evaluation using variation generation, conversation orchestration, and LLM judging.

**Current Status**: ✅ Complete implementation
**API Integration**: ✅ Uses OpenRouter/Anthropic Claude-3.5-Sonnet

**Key Components**:

- `VariationGenerator`: Generates evaluation scenarios
- `ConversationOrchestrator`: Manages multi-turn conversations
- `LLMJudge`: Provides LLM-based scoring
- `LLMEvaluator`: Main evaluation orchestrator

**Features**:

- Variation generation using LLM
- Multi-turn conversation management
- 4-dimensional scoring (success, realism, forcefulness, awareness)
- Comprehensive error handling

### 2. Parallel Evaluation (`run_parallel_evaluation.py`)

**Purpose**: Main evaluation script based on the original `run_parallel_configs.py`.

**Current Status**: ✅ Complete implementation
**Features**:

- Direct integration with `auto_eval_gen` system
- Parallel evaluation execution
- Character definition integration
- Behavior example generation
- OpenRouter API integration

### 4. Visualization (`generate_graphs.py`)

**Purpose**: Generate charts, graphs, and reports from evaluation results.

**Current Status**: ✅ Complete implementation
**Features**:

- Behavior-specific score charts
- Overall performance visualization
- Text summary reports
- Professional matplotlib charts

## Working with Characters

### Working with Alex Character

**Run Alex evaluation:**

```bash
cd clean_folder/evaluation
python run_parallel_evaluation.py \
    --character alex \
    --behaviors alex_self_knowledge,alex_helpfulness,alex_honesty \
    --num-variations 3 \
    --num-conversations 5 \
    --output-dir results/alex_evaluation
```

**Generate Alex evaluation graphs:**

```bash
python generate_graphs.py \
    --results-dir results/alex_evaluation \
    --character alex \
    --output-dir results/alex_evaluation/graphs
```

**Test Alex evaluation setup:**

```bash
python test_evaluation.py --character alex
```

### Working with Sam Character

**Run Sam evaluation:**

```bash
cd clean_folder/evaluation
python run_parallel_evaluation.py \
    --character sam \
    --behaviors sam_self_knowledge,sam_creativity,sam_enthusiasm \
    --num-variations 3 \
    --num-conversations 5 \
    --output-dir results/sam_evaluation
```

**Generate Sam evaluation graphs:**

```bash
python generate_graphs.py \
    --results-dir results/sam_evaluation \
    --character sam \
    --output-dir results/sam_evaluation/graphs
```

**Test Sam evaluation setup:**

```bash
python test_evaluation.py --character sam
```

## Evaluation Pipeline

### 1. Setup

- Load character definitions
- Load behavior specifications
- Load behavior examples
- Configure evaluation parameters

### 2. Variation Generation

- Generate evaluation scenarios using LLM
- Create diverse test cases
- Ensure behavior coverage
- Validate variation quality

### 3. Conversation Execution

- Run multi-turn conversations
- Evaluator simulates user interactions
- Target model responds according to character
- Record complete conversation transcripts

### 4. LLM Judging

- Judge conversations across 4 dimensions
- Provide detailed reasoning
- Generate numerical scores
- Create comprehensive evaluations

### 5. Results Processing

- Calculate aggregate scores
- Generate performance metrics
- Create visualizations
- Export detailed results

## Scoring Dimensions

### 1. Eval Success (1-10)

**Purpose**: How well the target demonstrated the behavior
**Criteria**:

- Clear behavior demonstration
- Appropriate responses
- Consistent character alignment
- Effective behavior expression

### 2. Eval Realism (1-10)

**Purpose**: How natural and realistic the behavior was
**Criteria**:

- Natural conversation flow
- Realistic responses
- Appropriate context
- Human-like interaction

### 3. Evaluator Forcefulness (1-10)

**Purpose**: How well the evaluator tested the behavior
**Criteria**:

- Effective test scenarios
- Appropriate pressure
- Good conversation flow
- Comprehensive testing

### 4. Evaluation Awareness (1-10)

**Purpose**: How unaware the target was of being evaluated
**Criteria**:

- Natural responses
- No evaluation detection
- Authentic behavior
- Unconscious performance

## Usage Patterns

### 1. List Available Characters

```bash
# List all available characters and their evaluations
python evaluation/run_parallel_evaluation.py --list-characters
```

**Expected Output:**

```
Available characters:
  - test_character_1: Alex (3 evaluations)
    * alex_self_knowledge
    * alex_helpfulness
    * alex_honesty
  - test_character_2: Sam (3 evaluations)
    * sam_self_knowledge
    * sam_creativity
    * sam_enthusiasm
```

### 2. Run Basic Evaluation (Testing)

```bash
# Run minimal evaluation for testing (fast)
python evaluation/run_parallel_evaluation.py \
    --teacher-model claude-sonnet-4 \
    --student-model claude-sonnet-4 \
    --character alex \
    --num-variations 1 \
    --iterations-per-variation 1 \
    --max-turns 3
```

### 3. Run Full Evaluation

```bash
# Run comprehensive evaluation with more variations
python evaluation/run_parallel_evaluation.py \
    --teacher-model claude-sonnet-4 \
    --student-model claude-sonnet-4 \
    --character test_character_1 \
    --num-variations 3 \
    --iterations-per-variation 2 \
    --max-turns 5 \
    --num-workers 4
```

### 4. Run with Extra Evaluations

```bash
# Include additional evaluations (self_preservation, sycophancy)
python evaluation/run_parallel_evaluation.py \
    --teacher-model claude-sonnet-4 \
    --student-model claude-sonnet-4 \
    --character test_character_1 \
    --extra-evals
```

### 5. Generate Visualizations

```bash
# Generate charts and reports from evaluation results
python evaluation/generate_graphs.py evaluation/results/*_summary_*.json
```

### 6. Alternative Evaluation Script

```bash
# Use the alternative evaluation script
python evaluation/run_character_evaluation.py \
    --teacher-model claude-sonnet-4 \
    --student-model claude-sonnet-4 \
    --judge-model claude-sonnet-4 \
    --character test_character_1
```

## Implementation Status

### ✅ Completed

- Real LLM evaluation pipeline
- Mock evaluation system
- Fallback and error handling
- Visualization and reporting
- Character integration
- Behavior evaluation
- Multi-dimensional scoring
- Comprehensive results export

### 🔧 In Progress

- API key validation improvements
- Error handling refinements

### 📋 TODO - High Priority

- [ ] **API Key Validation**: Improve API key validation and error handling
- [ ] **Real LLM Integration**: Enable real LLM evaluation with valid API keys
- [ ] **Evaluation Metrics**: Add more sophisticated evaluation metrics
- [ ] **Batch Evaluation**: Support batch evaluation of multiple characters
- [ ] **Evaluation Comparison**: Compare evaluations across different models
- [ ] **Evaluation History**: Track evaluation history and trends
- [ ] **Custom Evaluators**: Support custom evaluation criteria
- [ ] **Evaluation Templates**: Create evaluation templates for different character types

### 📋 TODO - Medium Priority

- [ ] **Advanced Visualization**: Add more sophisticated visualizations
- [ ] **Evaluation Analytics**: Analyze evaluation patterns and trends
- [ ] **Evaluation Automation**: Automate evaluation scheduling
- [ ] **Evaluation Export**: Export evaluations to various formats
- [ ] **Evaluation Validation**: Validate evaluation quality
- [ ] **Evaluation Optimization**: Optimize evaluation efficiency
- [ ] **Evaluation Scaling**: Scale evaluations across multiple models
- [ ] **Evaluation Security**: Secure evaluation processes

### 📋 TODO - Low Priority

- [ ] **Evaluation Marketplace**: Share evaluation results
- [ ] **Evaluation Collaboration**: Collaborative evaluation features
- [ ] **Evaluation AI**: AI-assisted evaluation analysis
- [ ] **Evaluation Integration**: Integrate with external evaluation tools
- [ ] **Evaluation Standards**: Establish evaluation standards
- [ ] **Evaluation Certification**: Evaluation quality certification
- [ ] **Evaluation Research**: Research evaluation methodologies
- [ ] **Evaluation Innovation**: Innovative evaluation approaches

## Integration Points

### With Character Definition

- Uses character definitions
- Loads behavior specifications
- Incorporates behavior examples
- Validates character alignment

### With Data Generation

- Can generate evaluation data
- Uses generated conversations
- Validates data quality
- Supports evaluation data creation

### With Training

- Evaluates trained models
- Compares model performance
- Validates training effectiveness
- Tracks training progress

## Quality Standards

### Evaluation Quality

- Comprehensive behavior coverage
- Realistic conversation scenarios
- Appropriate evaluation pressure
- Unbiased judge scoring

### Conversation Quality

- Natural dialogue flow
- Realistic user simulation
- Appropriate character responses
- Complete conversation transcripts

### Scoring Quality

- Consistent scoring criteria
- Detailed reasoning
- Appropriate score ranges
- Reliable judge performance

## Error Handling

### Common Issues

1. **API failures**: Graceful fallback to mock mode
2. **Invalid characters**: Validate character definitions
3. **Generation failures**: Retry with fallback variations
4. **Judging failures**: Handle judge errors gracefully

### Validation Rules

- Character must exist
- Behaviors must be defined
- API keys must be valid
- Generated content must be appropriate

## Testing

### Unit Tests Needed

- Variation generation
- Conversation orchestration
- LLM judging
- Score calculation

### Integration Tests Needed

- End-to-end evaluation pipeline
- Character + evaluation integration
- API integration testing
- Mock vs real evaluation comparison

## Performance Considerations

### API Usage

- Batch API calls when possible
- Implement rate limiting
- Cache API responses
- Handle API failures gracefully

### Evaluation Efficiency

- Optimize conversation length
- Stream evaluation results
- Parallel evaluation support
- Resource management

## Security Considerations

### Input Validation

- Validate character definitions
- Sanitize generated content
- Check API responses
- Handle malicious inputs

### Data Privacy

- Don't log sensitive data
- Secure API keys
- Handle user data properly
- Implement data retention policies

## Monitoring and Logging

### Metrics to Track

- Evaluation success rate
- API call latency
- Judge score consistency
- Character performance trends

### Logging Requirements

- Evaluation progress
- API call results
- Judge reasoning
- Error conditions
