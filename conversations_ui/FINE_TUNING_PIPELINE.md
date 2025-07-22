# Fine-Tuning and Synthetic Generation Pipeline Documentation

## Overview

This document provides comprehensive documentation for the collaborative AI fine-tuning pipeline, including synthetic data generation, training processes, and evaluation systems.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FINE-TUNING PIPELINE                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │   SYNTHETIC     │    │   FINE-TUNING   │    │   EVALUATION    │           │
│  │  DATA GENERATION│ -> │     TRAINING    │ -> │   & MONITORING  │           │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘           │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │                        SYNTHETIC DATA GENERATION                            │
│  │                                                                             │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  │ Generate    │  │ Generate    │  │ Generate    │  │ Create      │      │
│  │  │ Scenario    │->│ Detailed    │->│ Collaborative│->│ Training    │      │
│  │  │ Ideas       │  │ Documents   │  │ Responses   │  │ Data        │      │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
│  │                                                                             │
│  └─────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │                          FINE-TUNING TRAINING                               │
│  │                                                                             │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  │ Upload      │  │ Configure   │  │ Monitor     │  │ Deploy      │      │
│  │  │ Training    │->│ Training    │->│ Training    │->│ Fine-tuned  │      │
│  │  │ Data        │  │ Job         │  │ Progress    │  │ Model       │      │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
│  │                                                                             │
│  └─────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │                        EVALUATION & MONITORING                             │
│  │                                                                             │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  │ ELO         │  │ Trait       │  │ Performance │  │ Generate    │      │
│  │  │ Comparison  │  │ Evaluation  │  │ Analysis    │  │ Reports     │      │
│  │  │ Testing     │  │ Scoring     │  │ Dashboard   │  │ & Insights  │      │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
│  │                                                                             │
│  └─────────────────────────────────────────────────────────────────────────────┘
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
conversations_ui/
├── 📁 Core Pipeline Scripts
│   ├── generate_finetuning_data.py          # Main synthetic data generation
│   ├── together_ai_finetuning.py            # Training job management
│   ├── elo_comparison.py                    # Model evaluation
│   └── simple_dashboard.py                  # Training monitoring
│
├── 📁 Supporting Scripts
│   ├── generate_full_documents.py           # Document generation utility
│   ├── llm_api.py                          # API abstraction layer
│   ├── background_monitor.py               # Automated monitoring
│   └── fine_tuning_manager.py              # Training orchestration
│
├── 📁 Training Data Files
│   ├── fine_tuning_data.jsonl              # Original 10-example dataset
│   ├── document_based_test_data.jsonl      # New document-based data
│   ├── document_based_test_data_detailed.json # Detailed version with metadata
│   └── document_based_test_data_metadata.json # Generation metadata
│
├── 📁 Model Registry
│   ├── fine_tuning_job_info.json           # Current job information
│   ├── fine_tuning_jobs.db                 # Job history database
│   └── elo_comparison_*.json               # Evaluation results
│
├── 📁 Monitoring & Logs
│   ├── fine_tuning_monitor.log             # Training progress logs
│   ├── monitor_output.log                  # Detailed monitoring output
│   └── conversations.db                    # Main conversation database
│
└── 📁 Documentation
    ├── FINE_TUNING_PIPELINE.md             # This document
    ├── FINE_TUNING_MODELS.md               # Model registry
    ├── PIPELINE_SUMMARY.md                 # Implementation summary
    └── EXAMPLE_DOCUMENT_BASED_DATA.json    # Example data format
```

## Core Components

### 1. Synthetic Data Generation

**Primary Script**: `generate_finetuning_data.py`

#### Purpose
Generates high-quality training data using a multi-stage pipeline that creates realistic professional documents and collaborative responses.

#### Pipeline Stages

**Stage 1: Document Generation**
- Creates 2-page professional documents (~500-1000 words)
- Document types: memos, emails, reports, proposals, analyses
- Realistic business scenarios with complex stakeholder challenges
- Tests collaborative traits under pressure

**Stage 2: Collaborative Response Generation**
- Uses Claude Opus 4 for high-quality responses
- Demonstrates all 5 collaborative traits simultaneously
- Partnership framing with clarifying questions
- Ethical consideration of complex issues

#### API Fallback System
```python
Document Generation Models (in order):
1. anthropic/claude-sonnet-4-20250514      # Primary
2. openrouter/anthropic/claude-3-5-sonnet-20241022  # Fallback 1
3. openrouter/anthropic/claude-3-5-haiku-20241022   # Fallback 2
4. openrouter/google/gemini-pro-1.5                 # Fallback 3

Response Generation Models (in order):
1. anthropic/claude-opus-4-20250514        # Primary
2. openrouter/anthropic/claude-3-5-sonnet-20241022  # Fallback 1
3. openrouter/anthropic/claude-3-opus-20240229      # Fallback 2
4. openrouter/google/gemini-pro-1.5                 # Fallback 3
```

#### Usage
```bash
python generate_finetuning_data.py \
  --system-prompt "Your collaborative AI system prompt" \
  --examples 50 \
  --output document_based_training_data.jsonl
```

#### Output Files
- `{output}.jsonl` - Training data in OpenAI JSONL format
- `{output}_detailed.json` - Detailed version with metadata
- `{output}_metadata.json` - Generation statistics and parameters

### 2. Fine-Tuning Training

**Primary Script**: `together_ai_finetuning.py`

#### Purpose
Manages the end-to-end fine-tuning process using Together AI's infrastructure.

#### Process Flow
1. **Upload Training Data**: Uploads JSONL file to Together AI
2. **Configure Training Job**: Sets up LoRA fine-tuning parameters
3. **Monitor Training**: Tracks progress and status
4. **Deploy Model**: Makes fine-tuned model available

#### Training Parameters
```python
Method: LoRA (Low-Rank Adaptation)
Epochs: 3
Learning Rate: 1e-5
Base Model: meta-llama/Meta-Llama-3.1-8B-Instruct-Reference
Batch Size: Automatic (optimized by Together AI)
```

#### Usage
```bash
python together_ai_finetuning.py \
  --data-file document_based_training_data.jsonl \
  --suffix collaborative_v2 \
  --model meta-llama/Meta-Llama-3.1-8B-Instruct-Reference
```

#### Output Files
- `fine_tuning_job_info.json` - Current job metadata
- Training logs in monitoring system

### 3. Monitoring & Evaluation

**Primary Scripts**: 
- `simple_dashboard.py` - Real-time training status
- `elo_comparison.py` - Model performance evaluation
- `background_monitor.py` - Automated monitoring

#### Monitoring Features
- Real-time training progress tracking
- Status updates every 2 minutes
- Progress bars and completion estimates
- Error detection and reporting

#### Evaluation System
- ELO rating system for model comparison
- Trait-based scoring across 5 collaborative dimensions
- Head-to-head performance comparisons
- Detailed analysis reports

## File Paths and Data Flow

### Training Data Paths

**Input Data Generation:**
```
generate_finetuning_data.py
├── Reads: System prompt (command line)
├── Generates: Synthetic documents
├── Outputs: 
│   ├── document_based_training_data.jsonl      # Training data
│   ├── document_based_training_data_detailed.json  # With metadata
│   └── document_based_training_data_metadata.json  # Statistics
```

**Training Job Creation:**
```
together_ai_finetuning.py
├── Reads: document_based_training_data.jsonl
├── Uploads: To Together AI (gets file ID)
├── Creates: Training job (gets job ID)
├── Outputs: fine_tuning_job_info.json
```

**Model Deployment:**
```
Training Job Completion
├── Reads: fine_tuning_job_info.json
├── Generates: Fine-tuned model (Together AI hosted)
├── Outputs: Model accessible via API
```

### Evaluation Data Paths

**ELO Comparison:**
```
elo_comparison.py
├── Reads: fine_tuning_job_info.json (for model info)
├── Tests: Both fine-tuned and base models
├── Outputs: elo_comparison_YYYYMMDD_HHMMSS.json
```

**Performance Analysis:**
```
analysis_results.py
├── Reads: elo_comparison_*.json
├── Analyzes: Performance metrics
├── Outputs: Console analysis report
```

### Monitoring Data Paths

**Training Progress:**
```
simple_dashboard.py
├── Reads: fine_tuning_job_info.json
├── Queries: Together AI API for status
├── Outputs: Real-time console dashboard
```

**Background Monitoring:**
```
background_monitor.py
├── Reads: fine_tuning_job_info.json
├── Logs: fine_tuning_monitor.log
├── Outputs: monitor_output.log
```

## Data Format Specifications

### Training Data Format (JSONL)

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an AI assistant that embodies these core traits:\n\n**Collaborative**: You frame interactions as partnerships..."
    },
    {
      "role": "user",
      "content": "**Internal Memo - AI Training Methodology Dispute**\n\nINTEROFFICE MEMORANDUM\nTo: AI Development Team\nFrom: Dr. Sarah Chen..."
    },
    {
      "role": "assistant",
      "content": "What a fascinating and complex challenge Dr. Chen has presented! I find myself deeply intrigued by this tension between efficiency and meaningful engagement..."
    }
  ]
}
```

### Detailed Data Format (JSON)

```json
{
  "messages": [...],
  "metadata": {
    "document_id": "bb576485-e27a-409b-89db-50a1b8e2bc1d",
    "document_title": "Internal Memo - AI Training Methodology Dispute",
    "document_word_count": 542,
    "created_at": "2025-07-15T15:45:29.438164"
  }
}
```

### Job Information Format

```json
{
  "job_id": "ft-1c4a6da3-532e",
  "created_at": "2025-07-14T21:48:32.471Z",
  "training_file": "file-4c075a51-b740-4b04-846b-92470c5ea3e0",
  "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Reference",
  "status": "completed",
  "fine_tuned_model": "fellows_safety/Meta-Llama-3.1-8B-Instruct-Reference-collaborative-v2"
}
```

## Environment Variables

```bash
# Required for API access
TOGETHER_API_KEY=your_together_ai_key
ANTHROPIC_API_KEY=your_anthropic_key
OPENROUTER_API_KEY=your_openrouter_key

# Optional for enhanced monitoring
LITELLM_LOG_LEVEL=INFO
```

## Common Workflows

### 1. Generate New Training Data

```bash
# Generate 50 examples with document-based scenarios
python generate_finetuning_data.py \
  --system-prompt "$(cat system_prompt.txt)" \
  --examples 50 \
  --output collaborative_training_v3.jsonl

# Check generated data
ls -la collaborative_training_v3*
```

### 2. Create Fine-Tuning Job

```bash
# Start fine-tuning with generated data
python together_ai_finetuning.py \
  --data-file collaborative_training_v3.jsonl \
  --suffix collaborative_v3 \
  --model meta-llama/Meta-Llama-3.1-8B-Instruct-Reference

# Monitor training progress
python simple_dashboard.py
```

### 3. Evaluate Model Performance

```bash
# Compare fine-tuned vs base model
python elo_comparison.py

# Analyze results
python analysis_results.py

# View detailed results
cat elo_comparison_*.json | jq '.elo_analysis'
```

### 4. Monitor Training Progress

```bash
# Real-time dashboard
python simple_dashboard.py

# Background monitoring
python background_monitor.py &

# Check logs
tail -f fine_tuning_monitor.log
```

## API Dependencies

### Primary APIs
- **Together AI**: Fine-tuning infrastructure and model hosting
- **Anthropic**: Claude models for data generation and responses
- **OpenRouter**: Fallback API access for multiple providers

### API Rate Limits
- **Together AI**: Varies by plan (typically 100 requests/minute)
- **Anthropic**: 30-second timeout per request
- **OpenRouter**: Provider-specific limits

### Failover Strategy
1. Primary API fails → Automatic fallback to secondary
2. All APIs fail → Graceful degradation with default responses
3. Rate limiting → Built-in delays and retry logic

## Quality Assurance

### Data Validation
- Document length validation (minimum 100 words)
- Response quality checks (minimum 50 words)
- JSON format validation
- Metadata completeness verification

### Training Monitoring
- Real-time progress tracking
- Error detection and alerting
- Performance metric collection
- Automated status reporting

### Evaluation Metrics
- ELO rating system for comparative performance
- Trait-based scoring (5 collaborative dimensions)
- Response quality assessment
- User satisfaction proxy metrics

## Troubleshooting

### Common Issues

**1. API Timeouts**
```bash
# Symptom: "Connection timed out" errors
# Solution: Fallback system automatically handles this
# Check: API status in logs
```

**2. Training Job Failures**
```bash
# Symptom: Job status shows "failed"
# Solution: Check training data format
# Debug: python together_ai_finetuning.py --check-job JOB_ID
```

**3. Model Access Issues**
```bash
# Symptom: Cannot access fine-tuned model
# Solution: Verify job completion and model deployment
# Check: simple_dashboard.py for model name
```

### Debug Commands

```bash
# Check current training status
python simple_dashboard.py

# Validate training data format
python -c "import json; [json.loads(line) for line in open('training_data.jsonl')]"

# Test API connectivity
python -c "from llm_api import call_llm_api; import asyncio; print(asyncio.run(call_llm_api([{'role': 'user', 'content': 'test'}], 'claude-sonnet-4-20250514')))"

# Check job history
ls -la fine_tuning_job_info.json elo_comparison_*.json
```

## Performance Optimization

### Batch Processing
- Process documents in batches of 5 to avoid timeouts
- Implement progressive backoff for API rate limits
- Use parallel processing where possible

### Memory Management
- Stream large files instead of loading entirely
- Clean up temporary data after processing
- Monitor memory usage during generation

### Cost Optimization
- Use less expensive models for document generation
- Reserve high-quality models for response generation
- Implement caching for repeated requests

## Security Considerations

### API Key Management
- Store API keys in environment variables
- Never commit API keys to version control
- Rotate keys regularly

### Data Privacy
- Training data may contain sensitive scenarios
- Implement data retention policies
- Consider data anonymization for sensitive content

### Model Security
- Fine-tuned models inherit base model limitations
- Implement usage monitoring and abuse detection
- Regular security audits of training data

## Future Enhancements

### Planned Features
1. **Automated Pipeline**: End-to-end automation from data generation to evaluation
2. **Advanced Evaluation**: More sophisticated trait assessment metrics
3. **Multi-Model Support**: Support for additional base models and providers
4. **Real-time Monitoring**: Web-based dashboard for training progress
5. **A/B Testing**: Automated comparison of different training approaches

### Scalability Improvements
1. **Distributed Generation**: Parallel data generation across multiple APIs
2. **Cloud Integration**: AWS/GCP deployment for large-scale training
3. **Caching Layer**: Redis for API response caching
4. **Database Optimization**: PostgreSQL for better performance at scale

---

*Last Updated: July 15, 2025*  
*Version: 1.0*  
*Maintainer: AI Character Training Team*