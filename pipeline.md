# Character Training Pipeline

This document outlines the end-to-end pipeline for character training, orchestrated by `pipeline.py`. The pipeline is designed to be configurable and modular, covering data generation, fine-tuning, and interactive testing.

## Configuration

The pipeline is driven by one or more YAML configuration files. These files specify parameters for each stage, including:
- **Data Generation**: Models to use for the evaluator and the target (e.g., `claude-sonnet-4`), the behavior to evaluate, number of turns, etc.
- **Fine-tuning**: The base model to be fine-tuned (e.g., `qwen-32b`), and the training parameters (e.g., learning rate, number of epochs).

## Pipeline Stages

The pipeline consists of the following stages:

1.  **Data Generation**: This stage runs the `auto_eval_gen` process to generate evaluation transcripts. It can be configured to run in parallel for multiple behaviors or characters. The primary script for this stage is `bloom_eval.py` from the `auto_eval_gen` repository.

2.  **Fine-tuning**: This stage takes the generated data and uses it to fine-tune a specified model. It involves:
    - **Data Preparation**: Converting the generated transcripts into a format suitable for fine-tuning (e.g., SFT or DPO).
    - **Training**: Launching the fine-tuning job.

3.  **Interact**: This stage provides an interactive command-line interface to chat with the newly fine-tuned model for qualitative assessment and testing.

## Usage

The pipeline is controlled via `pipeline.py`:

```bash
# Run the full pipeline: data generation, fine-tuning, and interaction
python pipeline.py --config configs/my_character.yaml

# Run only specific stages
python pipeline.py --config configs/my_character.yaml --stages generate finetune

# Run data generation with multiple configs in parallel
python pipeline.py --config configs/char1.yaml configs/char2.yaml --stages generate
```

- Config, turns, number per response, number per behavior, system prompt, teacher model, student model
- Train, split, SFT or DPO
- Chat with trained model
- Run on config, train or test
