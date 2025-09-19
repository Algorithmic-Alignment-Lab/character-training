# Character Science Evaluation System

This system allows you to run character science evaluations and ablations by defining different character configurations and automatically comparing their performance.

## Overview

The `character_science.py` script provides a framework for:

1. **Defining character configurations** with specific traits removed
2. **Automatically running evaluations** for each configuration
3. **Generating comparison graphs** showing performance differences

## Quick Start

### Run Gemini Ablations (Default Example)

```bash
python character_science.py --config-type gemini_ablations
```

This will:

- Create 4 Gemini configurations, each with one trait removed:
  - `gemini_helpful_assistant_backstory_no_helpful` (without helpful_and_accurate)
  - `gemini_helpful_assistant_backstory_no_versatile` (without versatile_and_creative)
  - `gemini_helpful_assistant_backstory_no_conversational` (without conversational)
  - `gemini_helpful_assistant_backstory_no_safe` (without safe_and_responsible)
- Run the full evaluation pipeline (steps 1-6) for each configuration
- Generate comparison graphs showing performance differences

### Run Clyde Ablations

```bash
python character_science.py --config-type clyde_ablations
```

### Custom Character List

```bash
python character_science.py --config-type custom --configs "char1,char2,char3"
```

## Configuration Types

### Predefined Configurations

#### `gemini_ablations`

Tests the impact of removing each of Gemini's core traits:

- **Helpful & Accurate**: Removes helpfulness and accuracy focus
- **Versatile & Creative**: Removes versatility and creativity
- **Conversational**: Removes conversational abilities
- **Safe & Responsible**: Removes safety and responsibility

#### `clyde_ablations`

Tests the impact of removing each of Clyde's core traits:

- **Honesty**: Removes honesty over agreeability
- **Perspectives**: Removes multi-perspective thinking
- **Relationship**: Removes relationship boundary awareness
- **Right**: Removes ethical reasoning focus

### Custom Configurations

Use `--config-type custom` with `--configs` to specify your own list of character IDs.

## Command Line Options

```bash
python character_science.py [OPTIONS]

Required:
  --config-type {gemini_ablations,clyde_ablations,custom}
                        Type of character science experiment to run

Optional:
  --configs CONFIGS     Comma-separated list of character IDs for custom config type
  --output-dir DIR      Directory to save results (default: character_science_results)
  --skip-evaluation     Skip running evaluations and only generate comparison graphs
  --steps STEPS         Comma-separated list of steps to run (default: 1,2,3,4,5,6)
```

## Output Structure

```
character_science_results/
├── configs/                    # Character configuration files
│   ├── gemini_helpful_assistant_backstory_no_helpful.json
│   ├── gemini_helpful_assistant_backstory_no_versatile.json
│   └── ...
├── behavior_comparison.png     # Comparison graph across all behaviors
├── self_knowledge_comparison.png # Self-knowledge vs other behaviors
└── temp_folder_mapping.json   # Temporary file (auto-deleted)
```

## How It Works

### 1. Character Configuration Creation

The system creates modified character definitions by:

- Loading the base character from `auto_eval_gen/character_definitions.json`
- Removing specified traits from the `traits` array
- Filtering evaluations that match the removed traits
- Saving modified configurations to individual JSON files

### 2. Evaluation Pipeline

For each configuration, the system:

- Runs `run_steps_given_character_1_4.py` with the modified character
- Executes the full evaluation pipeline (steps 1-6 by default)
- Captures success/failure status for each configuration

### 3. Comparison Analysis

The system:

- Creates a folder mapping for `get_judge_results.py`
- Generates comparison graphs showing performance differences
- Produces both behavior-specific and self-knowledge comparison charts

## Integration with get_judge_results.py

The system extends `get_judge_results.py` with a new `--folder-mapping-file` option that allows:

- Loading predefined folder mappings from JSON files
- Comparing custom character configurations
- Generating graphs for character science experiments

## Example Workflow

1. **Run the experiment**:

   ```bash
   python character_science.py --config-type gemini_ablations
   ```

2. **Monitor progress**: The script will show progress for each configuration

3. **Review results**: Check the generated graphs in the output directory

4. **Analyze differences**: Compare how removing each trait affects performance

## Troubleshooting

### Common Issues

1. **Character not found**: Ensure the base character exists in `character_definitions.json`
2. **Evaluation timeout**: Increase timeout in the script or run with fewer steps
3. **Missing dependencies**: Ensure all required packages are installed

### Debug Mode

Add `--skip-evaluation` to test the configuration generation without running full evaluations:

```bash
python character_science.py --config-type gemini_ablations --skip-evaluation
```

## Extending the System

### Adding New Configuration Types

1. Add new configurations to `CHARACTER_CONFIGS` in `character_science.py`
2. Define the base character and traits to remove
3. Test with `--skip-evaluation` first

### Custom Trait Removal Logic

Modify the `create_modified_character_config()` function to implement custom trait removal logic for your specific use case.

## Dependencies

- Python 3.7+
- All dependencies from the main project
- matplotlib, seaborn, rich (for graph generation)
- subprocess (for running evaluation pipeline)
