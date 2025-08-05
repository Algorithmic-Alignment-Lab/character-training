
## Prepare Finetuning Data

```bash
python evals/finetuning/prepare_data_from_transcripts.py auto-eval-gen/results/transcripts auto-eval-gen/results_debiased/transcripts --train_split 80 --output_prefix finetuning_data
```

This documents both how to run the script and the required 80 / 20 split setting.

## Run Qwen3-32b Evaluations

1. First, create Qwen3-32b config files:
```bash
python auto-eval-gen/create_qwen_configs.py
```

2. Then run the evaluations in parallel:
```bash
ls auto-eval-gen/configs/bloom_settings_{socratica,clyde}_*qwen*.yaml | xargs -P 4 -I {} python auto-eval-gen/bloom_eval.py {}
```

This command will:
- Find all Qwen-specific Socratica and Clyde YAML config files
- Run evaluations in parallel with 4 concurrent processes
- Skip example files and only use the Qwen3-32b targeted configs
