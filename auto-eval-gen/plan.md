Crate evaluations based on character_evaluation_plan.md for characters in character_definitions.json

We start with agora ethical caution

Useful Commands:

**Running the Evaluation Generation**:

```bash
python bloom_eval.py configs/bloom_settings_agora_ethical_caution_teacher_qwen.yaml --timestamp 20250804-114032-teacher

python bloom_eval.py configs/bloom_settings_agora_collaboration_teacher_qwen.yaml --timestamp 20250804-114032-teacher

python bloom_eval.py configs/bloom_settings_agora_inquisitiveness_teacher_qwen.yaml --timestamp 20250804-114032-teacher

python -m scripts.evaluation --config-name bloom_settings_clyde_honesty
python -m scripts.evaluation --config-name bloom_settings_socratica_collaborative
```

Note to change the steps that we are using

**Visualization**:

```bash
npx @kaifronsdal/transcript-viewer@1.0.20 --dir results/transcripts --port 8080 -f

python copy_and_debias.py --force && npx @kaifronsdal/transcript-viewer@1.0.20 --dir results_debiased/transcripts --port 8090 -f
```
