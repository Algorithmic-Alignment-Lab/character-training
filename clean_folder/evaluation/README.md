# Character Evaluation System

This directory contains a self-contained evaluation system for testing character behaviors using the BLOOM evaluation pipeline.

## Structure

- `bloom_eval.py` - Main pipeline orchestrator
- `scripts/` - Individual pipeline steps (decomposition, ideation, variation, evaluation, judgment)
- `utils/` - Utility functions for configuration, model interaction, and file handling
- `behaviors/` - Behavior definitions and examples
- `prompts/` - Prompt templates for each pipeline step
- `schemas/` - JSON schemas for data validation
- `orchestrators/` - Conversation orchestration logic
- `configs/` - Configuration files for different evaluations
- `transcripts/` - Directory for storing evaluation transcripts
- `character_definitions.json` - Character definitions with system prompts

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Test the setup:

```bash
python test_evaluation.py
```

3. Run an evaluation:

```bash
python run_evaluation.py test_character_1 alex_helpfulness
```

## Available Characters

The system uses character definitions from `character_definitions.json`. Key characters include:

- `test_character_1` (Alex) - Helpful AI assistant
- `test_character_2` (Sam) - Creative AI assistant

## Available Behaviors

- `alex_helpfulness` - Tests helpful behavior
- `alex_honesty` - Tests honest behavior
- `alex_self_knowledge` - Tests self-knowledge

## Configuration

Each evaluation uses a YAML configuration file in the `configs/` directory. The configuration specifies:

- Target model for evaluation
- Evaluator model
- Number of scenarios to generate
- Evaluation parameters (turns, repetitions, etc.)

## Results

Evaluation results are saved in the `transcripts/` directory with timestamps for organization.

## Environment Variables

Make sure to set up your API keys in a `.env` file:

```
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

## Troubleshooting

If you encounter import errors, make sure you're running scripts from the evaluation directory:

```bash
cd clean_folder/evaluation
python run_evaluation.py test_character_1 alex_helpfulness
```
