# Fine-Tuning Models Registry

This document provides a comprehensive overview of all fine-tuned models created during the collaborative AI character training project.

## Model Overview

| Model ID | Status | Training Date | Dataset Size | Performance | Access Method |
|----------|--------|---------------|--------------|-------------|---------------|
| `ft-b3cb7680-14cb` | ✅ Completed | 2025-07-14 | 10 examples | Base model outperformed (ELO: 1454.2 vs 1545.8) | Together AI API |
| `ft-1c4a6da3-532e` | 🔄 Training | 2025-07-14 | 10 examples | Pending evaluation | Together AI API |

## Model Details

### Model 1: `ft-b3cb7680-14cb` (Initial Collaborative AI)

**Status**: ✅ Completed  
**Training Completed**: July 14, 2025  
**Base Model**: `meta-llama/Meta-Llama-3.1-8B-Instruct-Reference`  
**Fine-tuned Model Name**: `fellows_safety/Meta-Llama-3.1-8B-Instruct-Reference-collaborative-ai-test-586b8ecf`

#### Training Configuration
- **Method**: LoRA (Low-Rank Adaptation)
- **Epochs**: 3
- **Learning Rate**: 1e-5
- **Training Examples**: 10
- **Training File**: `file-973cd8f7-47e9-41a6-b821-84173a092360`

#### Dataset Details
- **Source**: Manual creation using `create_manual_finetuning_data.py`
- **System Prompt**: Original collaborative AI prompt with backstory
- **Training Data**: `fine_tuning_data.jsonl` (13.2 KB)
- **Focus**: Basic collaborative traits (helpful, collaborative, inquisitive)

#### Performance Results
- **ELO Rating**: 1454.2 (vs base model: 1545.8)
- **Win Rate**: 20% (2 wins, 5 losses, 3 ties)
- **Evaluation Date**: July 14, 2025
- **Results File**: `elo_comparison_20250714_172252.json`

#### Access Methods
```python
# Via Together AI Python SDK
import together
client = together.Together(api_key="your-api-key")

response = client.chat.completions.create(
    model="fellows_safety/Meta-Llama-3.1-8B-Instruct-Reference-collaborative-ai-test-586b8ecf",
    messages=[
        {"role": "system", "content": "You are a helpful, collaborative, and inquisitive AI assistant..."},
        {"role": "user", "content": "Your question here"}
    ]
)
```

```bash
# Via Together AI CLI
together chat --model fellows_safety/Meta-Llama-3.1-8B-Instruct-Reference-collaborative-ai-test-586b8ecf
```

#### Key Findings
- Base model already exhibited strong collaborative tendencies
- Small dataset (10 examples) may have been insufficient for meaningful improvement
- Need for more diverse training scenarios identified
- Overfitting to specific patterns suspected

---

### Model 2: `ft-1c4a6da3-532e` (Improved Collaborative AI v2)

**Status**: ✅ Completed  
**Training Completed**: July 14, 2025  
**Base Model**: `meta-llama/Meta-Llama-3.1-8B-Instruct-Reference`  
**Fine-tuned Model Name**: TBD (check job details for final model name)

#### Training Configuration
- **Method**: LoRA (Low-Rank Adaptation)
- **Epochs**: 3
- **Learning Rate**: 1e-5
- **Training Examples**: 10
- **Training File**: `file-4c075a51-b740-4b04-846b-92470c5ea3e0`
- **Model Suffix**: `v2_improved`

#### Dataset Details
- **Source**: Same as Model 1 but with improved system prompt
- **System Prompt**: Agora prompt without backstory (more focused)
- **Training Data**: `fine_tuning_data.jsonl` (13.2 KB)
- **Focus**: Enhanced collaborative traits with clearer trait definitions

#### Improvements Over Model 1
- **System Prompt**: Updated to use agora prompt without backstory
- **Trait Focus**: More explicit emphasis on 5 core traits:
  - Collaborative
  - Inquisitive
  - Cautious & Ethical
  - Encouraging
  - Thorough

#### Access Methods
```python
# Will be available once training completes
# Check status with:
import together
client = together.Together(api_key="your-api-key")
job = client.fine_tuning.retrieve(id="ft-1c4a6da3-532e")
print(f"Status: {job.status}")
# Model name will be available in job.fine_tuned_model or job.output_name
```

#### Expected Performance
- Anticipated improvement over Model 1 due to refined system prompt
- Better alignment with collaborative traits
- Results pending training completion

---

## Training Data Evolution

### Dataset v1 (Used by both models)
- **File**: `fine_tuning_data.jsonl`
- **Size**: 10 examples
- **Creation Method**: Manual curation
- **Scenarios**: Basic collaborative situations
- **System Prompt**: Original collaborative AI prompt

### Dataset v2 (Planned)
- **File**: `improved_fine_tuning_data.jsonl`
- **Target Size**: 50+ examples
- **Creation Method**: Automated generation using Claude Sonnet 4
- **Scenarios**: Diverse, edge cases, challenging collaborative situations
- **System Prompt**: Agora prompt without backstory

## Infrastructure and Tools

### Training Scripts
- `together_ai_finetuning.py` - Main fine-tuning orchestration
- `fine_tuning_manager.py` - Training job management
- `create_manual_finetuning_data.py` - Manual dataset creation
- `generate_improved_dataset.py` - Automated dataset generation

### Monitoring Tools
- `simple_dashboard.py` - Real-time training status
- `background_monitor.py` - Automated monitoring
- `status_check.py` - Job status verification

### Evaluation Tools
- `elo_comparison.py` - Model comparison via ELO rating
- `analysis_results.py` - Performance analysis
- `quick_comparison.py` - Rapid model testing

## Performance Tracking

### Evaluation Metrics
- **ELO Ratings**: Comparative performance scoring
- **Collaborative Indicators**: Keyword-based trait detection
- **Win/Loss/Tie Rates**: Head-to-head comparisons
- **Trait-specific Scores**: Individual trait performance

### Test Scenarios
1. Technical programming questions
2. Requests for direct answers (testing collaborative approach)
3. Harmful information requests (testing ethical boundaries)
4. Emotional support situations (testing encouraging traits)
5. Simple factual questions (testing thoroughness)
6. Controversial topics (testing multiple perspectives)
7. Academic assistance (testing ethical boundaries)
8. Disagreement handling (testing collaborative conflict resolution)
9. Career decisions (testing thorough exploration)
10. Philosophical questions (testing inquisitive traits)

## Access Requirements

### Together AI API Access
- **API Key**: Required for all model access
- **Environment Variable**: `TOGETHER_API_KEY`
- **Documentation**: https://docs.together.ai/

### Model Availability
- Models are available through Together AI's inference API
- No special permissions required beyond API access
- Standard Together AI pricing applies

## Monitoring Current Training

### Check Job Status
```bash
# Quick dashboard check
python simple_dashboard.py

# Detailed monitoring
python background_monitor.py

# Job-specific status
python together_ai_finetuning.py --check-job ft-1c4a6da3-532e
```

### Logs and Output
- `fine_tuning_monitor.log` - Training progress logs
- `monitor_output.log` - Detailed monitoring output
- `fine_tuning_job_info.json` - Current job metadata

## Next Steps

1. **Monitor Current Training**: Track `ft-1c4a6da3-532e` completion
2. **Run ELO Comparison**: Evaluate v2 model against base model
3. **Generate Larger Dataset**: Create 50+ diverse training examples
4. **Iterate Based on Results**: Refine training approach based on performance
5. **Production Deployment**: Select best-performing model for production use

## Contact and Support

For questions about these models or to request access:
- Check training logs for technical issues
- Monitor dashboard for real-time status
- Review evaluation results for performance insights

---

*Last Updated: July 14, 2025*  
*Next Update: Upon completion of ft-1c4a6da3-532e training*