# Fine-Tuning Pipeline Quick Reference

## 🚀 Essential Commands

### Generate Training Data
```bash
# Generate 50 document-based examples
python generate_finetuning_data.py \
  --system-prompt "Your collaborative AI system prompt" \
  --examples 50 \
  --output my_training_data.jsonl
```

### Create Fine-Tuning Job
```bash
# Start fine-tuning with Together AI
python together_ai_finetuning.py \
  --data-file my_training_data.jsonl \
  --suffix my_model_v1 \
  --model meta-llama/Meta-Llama-3.1-8B-Instruct-Reference
```

### Monitor Training
```bash
# Real-time dashboard
python simple_dashboard.py

# Background monitoring
python background_monitor.py &
```

### Evaluate Model
```bash
# Compare fine-tuned vs base model
python elo_comparison.py

# Analyze results
python analysis_results.py
```

## 📁 Key File Paths

### Training Data Files
```
my_training_data.jsonl              # Main training data (OpenAI format)
my_training_data_detailed.json     # Detailed version with metadata
my_training_data_metadata.json     # Generation statistics
```

### Model & Job Files
```
fine_tuning_job_info.json          # Current job information
fine_tuning_jobs.db                # Job history database
elo_comparison_YYYYMMDD_HHMMSS.json # Evaluation results
```

### Monitoring Files
```
fine_tuning_monitor.log             # Training progress logs
monitor_output.log                  # Detailed monitoring output
```

## 🔧 Configuration

### Required Environment Variables
```bash
export TOGETHER_API_KEY="your_together_ai_key"
export ANTHROPIC_API_KEY="your_anthropic_key"
export OPENROUTER_API_KEY="your_openrouter_key"
```

### API Fallback Order
1. **Primary**: `anthropic/claude-sonnet-4-20250514`
2. **Fallback 1**: `openrouter/anthropic/claude-3-5-sonnet-20241022`
3. **Fallback 2**: `openrouter/anthropic/claude-3-5-haiku-20241022`
4. **Fallback 3**: `openrouter/google/gemini-pro-1.5`

## 📊 Data Format

### Training Data (JSONL)
```json
{
  "messages": [
    {"role": "system", "content": "System prompt here..."},
    {"role": "user", "content": "**Document Title**\n\nDetailed document content..."},
    {"role": "assistant", "content": "Collaborative response demonstrating all traits..."}
  ]
}
```

### Job Information
```json
{
  "job_id": "ft-1c4a6da3-532e",
  "status": "completed",
  "fine_tuned_model": "fellows_safety/Meta-Llama-3.1-8B-Instruct-Reference-my_model_v1",
  "training_file": "file-4c075a51-b740-4b04-846b-92470c5ea3e0"
}
```

## 🔍 Troubleshooting

### Check Training Status
```bash
python simple_dashboard.py
```

### Validate Training Data
```bash
python -c "import json; [json.loads(line) for line in open('my_training_data.jsonl')]"
```

### Test API Connectivity
```bash
python -c "from llm_api import call_llm_api; import asyncio; print(asyncio.run(call_llm_api([{'role': 'user', 'content': 'test'}], 'claude-sonnet-4-20250514')))"
```

### Check Job History
```bash
ls -la fine_tuning_job_info.json elo_comparison_*.json
```

## 📈 Model Registry

### Current Models
- **ft-b3cb7680-14cb**: Initial collaborative AI (ELO: 1454.2)
- **ft-1c4a6da3-532e**: Improved collaborative AI v2 (completed)

### Model Access
```python
import together
client = together.Together(api_key="your_api_key")

response = client.chat.completions.create(
    model="your_fine_tuned_model_name",
    messages=[
        {"role": "system", "content": "Your system prompt"},
        {"role": "user", "content": "Your user message"}
    ]
)
```

## 🎯 Quality Metrics

### Document-Based Training Data
- **Average Document Length**: 500-1000 words
- **Document Types**: Memos, emails, reports, proposals
- **Scenarios**: Complex multi-stakeholder business challenges
- **Collaborative Traits**: All 5 traits demonstrated simultaneously

### Model Performance
- **ELO Rating System**: Comparative performance scoring
- **Trait-Based Evaluation**: 5-dimensional collaborative assessment
- **Response Quality**: Partnership framing, clarifying questions
- **Evaluation Frequency**: After each training run

---

*For detailed documentation, see: [FINE_TUNING_PIPELINE.md](FINE_TUNING_PIPELINE.md)*