# Character Evaluation & Fine-Tuning Pipeline

This directory contains a comprehensive framework for generating, evaluating, and fine-tuning AI character conversations.

---

## Pipeline Overview

### 1. Generate Contexts

Create scenario contexts for conversation generation.

**Command:**

```bash
python evals/synthetic_generation/context_generator.py \
  --output-file evals/synthetic_evaluation_data/contexts/customer_service_complaint_20250725_165135.json \
  --topic "customer_service_complaint" \
  --num-contexts 10
```

**Parameters:**

- `--output-file`: Path to save the generated context JSON.
- `--topic`: What the context is about (e.g., "customer service complaint").
- `--num-contexts`: Number of contexts to generate.

---

### 2. Generate Conversations

Create synthetic conversations between personas using specified models and context.

**Command:**

```bash
python evals/synthetic_generation/conversation_generator.py \
  --assistant-persona "interviewer_v2_jasmine" \
  --assistant-model "anthropic/claude-sonnet-4-20250514" \
  --user-persona "hates_customers_candidate" \
  --user-model "openrouter/qwen/qwen3-32b" \
  --context-file "evals/synthetic_evaluation_data/contexts/customer_service_complaint_20250725_165135.json" \
  --num-conversations 3 \
  --num-turns 1
```

**Parameters:**

- `--assistant-persona`: Name of the assistant persona.
- `--assistant-model`: Model for the assistant (must be one of: anthropic/claude-sonnet-4-20250514, openrouter/anthropic/claude-sonnet-4).
- `--user-persona`: Name of the user persona.
- `--user-model`: Model for the user (must be openrouter/qwen/qwen3-32b).
- `--context-file`: Path to the context JSON file.
- `--num-conversations`: Number of conversations to generate.
- `--num-turns`: Number of turns per conversation.

---

### 3. Prepare Data for Fine-Tuning

Transform generated conversations into the Together AI fine-tuning format.

**Command:**

```bash
python evals/finetuning/prepare_data.py \
  --input_file evals/synthetic_evaluation_data/conversations/interviewer_v2_jasmine_vs_hates_customers_candidate_20250728_140809.jsonl \
  --output_file evals/finetuning/finetuning_data/interviewer_v2_jasmine_vs_hates_customers_candidate_20250728_140809_finetune.jsonl
```

**Parameters:**

- `--input_file`: Path to the raw conversation JSONL file.
- `--output_file`: Path to save the fine-tuning-ready JSONL file.

---

### 4. Run Fine-Tuning on Together AI

Upload the formatted data and start a fine-tuning job.

**Command:**

```bash
python evals/finetuning/run_finetuning.py \
  --train_file evals/finetuning/finetuning_data/interviewer_v2_jasmine_vs_hates_customers_candidate_20250728_140809_finetune.jsonl \
  --model Qwen/Qwen3-32B \
  --n_epochs 3 \
  --suffix "customer_service_eval"
```

**Parameters:**

- `--train_file`: Path to the fine-tuning-ready JSONL file.
- `--model`: Model to fine-tune (default: Qwen/Qwen3-32B).
- `--n_epochs`: Number of epochs (default: 3).
- `--suffix`: Suffix for the fine-tuned model name.

---

### 5. Run Evaluation Pipeline

Run the full evaluation pipeline as defined in the config.

**Command:**

```bash
python evals/run_evaluations.py
```

**Config:**

- Reads from `evals/config.json`.
- For each evaluation set:
  - Generates conversations
  - Runs evaluators
  - Saves results in `evals/results/`

---

### 6. Visualize Results

Launch the Streamlit dashboard to explore evaluation results.

**Command:**

```bash
streamlit run evals/webapp/app.py
```

---

## File & Directory Descriptions

- `run_evaluations.py`: Main entry for the evaluation pipeline.
- `config.json`: Defines evaluation sets, characters, scenarios, and models.
- `llm_api.py`: Wrapper for LLM API calls.
- `load_env.py`: Loads environment variables.
- `synthetic_generation/`: Code for generating contexts and conversations.
- `evaluation_framework/`: Modular evaluators for conversation quality.
- `webapp/`: Streamlit dashboard for results.
- `results/`: Output from evaluation runs.
- `conversations/`: Ad-hoc conversation cache.
- `finetuning/`: Fine-tuning scripts and data.

---

## Notes

- Only use the following models for generation and fine-tuning:
  - `openrouter/qwen/qwen3-32b`
  - `anthropic/claude-sonnet-4-20250514`
  - `openrouter/anthropic/claude-sonnet-4`
- For Together AI fine-tuning, ensure your data is in the correct format (see step 3).
- Set your `TOGETHER_API_KEY` in your environment or `.env` file before running fine-tuning.
