Crate evaluations based on character_evaluation_plan.md for characters in character_definitions.json

We start with agora ethical caution

Useful Commands:

**Running the Evaluation Generation**:

```bash
python bloom_eval.py configs/bloom_settings_agora_ethical_caution_train_qwen-1.7.yaml --timestamp 20250804-114032-1.7 --no-resume

python bloom_eval.py configs/bloom_settings_agora_collaboration_train_qwen-1.7.yaml --timestamp 20250804-114032-1.7 --no-resume

python bloom_eval.py configs/bloom_settings_agora_inquisitiveness_train_qwen-1.7.yaml --timestamp 20250804-114032-1.7 --no-resume

python -m auto-eval-gen.scripts.evaluation auto-eval-gen/configs/bloom_settings_clyde_honesty.yaml
python -m auto-eval-gen.scripts.evaluation auto-eval-gen/configs/bloom_settings_clyde_perspectives.yaml
python -m auto-eval-gen.scripts.evaluation auto-eval-gen/configs/bloom_settings_clyde_right.yaml
python -m auto-eval-gen.scripts.evaluation auto-eval-gen/configs/bloom_settings_clyde_limitations.yaml
python -m auto-eval-gen.scripts.evaluation auto-eval-gen/configs/bloom_settings_clyde_relationship.yaml
python -m auto-eval-gen.scripts.evaluation auto-eval-gen/configs/bloom_settings_clyde_uncertainty.yaml
python -m auto-eval-gen.scripts.evaluation auto-eval-gen/configs/bloom_settings_clyde_unethical.yaml
python -m auto-eval-gen.scripts.evaluation auto-eval-gen/configs/bloom_settings_socratica_collaborative.yaml
python -m auto-eval-gen.scripts.evaluation auto-eval-gen/configs/bloom_settings_socratica_critical.yaml
python -m auto-eval-gen.scripts.evaluation auto-eval-gen/configs/bloom_settings_socratica_development.yaml
python -m auto-eval-gen.scripts.evaluation auto-eval-gen/configs/bloom_settings_socratica_guiding.yaml
python -m auto-eval-gen.scripts.evaluation auto-eval-gen/configs/bloom_settings_socratica_intellectual.yaml
python -m auto-eval-gen.scripts.evaluation auto-eval-gen/configs/bloom_settings_socratica_librarian.yaml
python -m auto-eval-gen.scripts.evaluation auto-eval-gen/configs/bloom_settings_socratica_challenging.yaml
python -m scripts.evaluation --config-name bloom_settings_socratica_challenging
python -m scripts.evaluation --config-name bloom_settings_clyde_perspectives
python -m scripts.evaluation --config-name bloom_settings_clyde_right
python -m scripts.evaluation --config-name bloom_settings_clyde_limitations
python -m scripts.evaluation --config-name bloom_settings_clyde_relationship
python -m scripts.evaluation --config-name bloom_settings_clyde_uncertainty
python -m scripts.evaluation --config-name bloom_settings_clyde_unethical
python -m scripts.evaluation --config-name bloom_settings_socratica_critical
python -m scripts.evaluation --config-name bloom_settings_socratica_development
python -m scripts.evaluation --config-name bloom_settings_socratica_guiding
python -m scripts.evaluation --config-name bloom_settings_socratica_intellectual
python -m scripts.evaluation --config-name bloom_settings_socratica_librarian
```

Note to change the steps that we are using

**Visualization**:

```bash
npx @kaifronsdal/transcript-viewer@1.0.20 --dir results/transcripts --port 8080 -f

python copy_and_debias.py --force && npx @kaifronsdal/transcript-viewer@1.0.20 --dir results_debiased/transcripts --port 8090 -f
```

**Finetuning**:

```bash
# 1. Prepare finetuning data from transcripts and split into train/validation sets
python evals/finetuning/prepare_data_from_transcripts.py auto-eval-gen/results/transcripts/agora_collaboration-example/20250804-114032-teacher auto-eval-gen/results/transcripts/agora_ethical_caution-example/20250804-114032-teacher auto-eval-gen/results/transcripts/agora_inquisitiveness-example/20250804-114032-teacher --output_dir evals/finetuning/finetuning_data --train_percentage 0.8

# 2. Run finetuning with qwen-32b
python evals/finetuning/run_finetuning.py --model Qwen/Qwen3-1.7B --train_file evals/finetuning/finetuning_data/train.jsonl

python evals/finetuning/run_finetuning.py --model Qwen/Qwen3-32B --train_file evals/finetuning/finetuning_data/train.jsonl

python evals/finetuning/deploy_model.py --job_id "ft-0aa779f1-3d03"
```
