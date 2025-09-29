#!/usr/bin/env python3
"""
Model Comparison Evaluation System

This script runs character trait evaluations on multiple models to compare their performance
with and without character prompts. It evaluates:
1. Base model (gpt-4.1-mini) without character prompt
2. Base model (gpt-4.1-mini) with character prompt  
3. List of fine-tuned models without character prompt

Usage:
    python run_model_comparison_evaluation.py --character gemini_helpful_assistant_backstory_no_helpful --models "model1,model2,model3"
    python run_model_comparison_evaluation.py --character llama_foundation_model_backstory --models "llama_sft,llama_dpo"
"""

import json
import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

def load_models_from_globals():
    """Load models from globals.json file."""
    globals_path = Path("auto_eval_gen/globals.json")
    if not globals_path.exists():
        print(f"Error: globals.json file not found at {globals_path}")
        return {}
    
    try:
        with open(globals_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading globals.json: {e}")
        return {}

def load_character_definitions():
    """Load character definitions from the JSON file."""
    char_def_path = Path("auto_eval_gen/character_definitions.json")
    if not char_def_path.exists():
        print(f"Error: Character definitions file not found at {char_def_path}")
        return {}
    
    try:
        with open(char_def_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading character definitions: {e}")
        return {}

def validate_models_and_character(models: List[str], character: str) -> tuple:
    """Validate that all models and character exist in the respective files."""
    all_models = load_models_from_globals()
    char_definitions = load_character_definitions()
    
    # Validate character
    if character not in char_definitions:
        print(f"Error: Character '{character}' not found in character_definitions.json")
        print(f"Available characters: {list(char_definitions.keys())}")
        return False, None, None
    
    # Validate models
    valid_models = []
    invalid_models = []
    
    for model in models:
        if model in all_models:
            valid_models.append(model)
        else:
            invalid_models.append(model)
    
    if invalid_models:
        print(f"Error: The following models were not found in globals.json:")
        for model in invalid_models:
            print(f"  - {model}")
        print(f"Available models: {list(all_models.keys())}")
        return False, None, None
    
    return True, valid_models, char_definitions[character]

def run_evaluation(model_name: str, character: str, character_full: str, timestamp: str, 
                  num_workers: int = 5, max_concurrent: int = 15, num_variations: int = 2) -> bool:
    """Run evaluation for a single model configuration."""
    print(f"🚀 Starting character trait/self-knowledge evaluation for {model_name} with character {character}")
    
    cmd = [
        "python", "scripts/run_parallel_configs.py",
        "--teacher-model", "claude-sonnet-4",
        "--student-model", model_name,
        "--character", character,
        "--character-full", character_full,
        "--num-workers", str(num_workers),
        "--max-concurrent", str(max_concurrent),
        "--num-variations", str(num_variations),
        "--iterations-per-variation", "1",
        "--timestamp", timestamp
        # No --extra-evals flag = run only character trait/self-knowledge evals
    ]
    
    try:
        # Change to auto_eval_gen directory
        original_cwd = os.getcwd()
        os.chdir("auto_eval_gen")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully completed evaluation for {model_name}")
            return True
        else:
            print(f"❌ Failed evaluation for {model_name}")
            print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Evaluation timed out for {model_name}")
        return False
    except Exception as e:
        print(f"💥 Unexpected error during evaluation of {model_name}: {e}")
        return False
    finally:
        os.chdir(original_cwd)

def generate_model_comparison_commands(character: str, character_full: str, model_list: List[str], 
                                     base_model: str, timestamp: str, num_workers: int = 5, 
                                     max_concurrent: int = 15, num_variations: int = 10,
                                     skip_base_without: bool = False, skip_base_with: bool = False,
                                     output_dir: str = "model_comparison_results") -> tuple:
    """
    Generate commands for model comparison evaluation following character_science.py pattern.
    
    Args:
        character: Character ID
        character_full: Full character name
        model_list: List of model names to evaluate
        base_model: Base model name
        timestamp: Timestamp for the run
        num_workers: Number of workers
        max_concurrent: Maximum concurrent evaluations
        num_variations: Number of variations (10 for self-knowledge, 5 for others)
        skip_base_without: Whether to skip base model without character
        skip_base_with: Whether to skip base model with character
        output_dir: Output directory
    
    Returns:
        Tuple of (md_path, command_lists, extra_character_commands)
    """
    from datetime import datetime
    
    md_filename = f"model_comparison_commands_{timestamp}.md"
    md_path = Path(output_dir) / md_filename
    Path(output_dir).mkdir(exist_ok=True)
    
    command_lists = []
    extra_character_commands = []
    
    # Create model configurations - all use same number of variations
    model_configs = []
    
    # 1. Base model without character (if not skipped)
    if not skip_base_without:
        model_configs.append({
            "model_name": base_model,
            "character": character,
            "character_full": "default",
            "timestamp": f"{character}_{base_model}_without_{timestamp}",
            "display_name": f"{base_model} (No Character)"
        })
    
    # 2. Base model with character (if not skipped) - this is the first one to run
    if not skip_base_with:
        model_configs.append({
            "model_name": base_model,
            "character": character,
            "character_full": character,
            "timestamp": f"{character}_{base_model}_with_{timestamp}",
            "display_name": f"{base_model} (With Character)"
        })
    
    # 3. Fine-tuned models without character
    for model in model_list:
        model_configs.append({
            "model_name": model,
            "character": character,
            "character_full": "default",
            "timestamp": f"{character}_{model}_without_{timestamp}",
            "display_name": f"{model} (No Character)"
        })
    
    # Find the "with character" configuration (first to run)
    with_character_config = None
    other_configs = []
    
    for config in model_configs:
        if config["character_full"] == character:
            with_character_config = config
        else:
            other_configs.append(config)
    
    # Build the markdown content
    md_content = f"""# Model Comparison Evaluation Commands

Generated on: {datetime.now().isoformat()}
Character: {character} ({character_full})
Models: {', '.join(model_list)}
Base Model: {base_model}

## Overview
This document contains all the commands to run model comparison evaluations for character '{character}' with {len(model_list)} models.

## Evaluation Plan

### Models to Evaluate:
1. **Base Model ({base_model}) without character prompt** {'(SKIPPED)' if skip_base_without else ''}
2. **Base Model ({base_model}) with character prompt** {'(SKIPPED)' if skip_base_with else ''}
3. **Fine-tuned models without character prompt:**
"""
    
    for i, model in enumerate(model_list, 1):
        md_content += f"   {i}. {model}\n"
    
    md_content += f"""

## Commands to Run

### Step 1: Setup Character
First, ensure the character is properly set up in the system:

```bash
# Verify character exists in character_definitions.json
python -c "
import json
with open('auto_eval_gen/character_definitions.json', 'r') as f:
    chars = json.load(f)
    if '{character}' in chars:
        print(f'✅ Character {character} found')
        print(f'Name: {{chars[\"{character}\"][\"name\"]}}')
    else:
        print(f'❌ Character {character} not found')
        exit(1)
"
```

### Step 2: Run Evaluations

Run the following commands in sequence:

"""
    
    # Generate commands following character_science.py pattern
    # First command: run without copy_folders.py (like character_science.py)
    if model_configs:
        first_config = model_configs[0]
        command_lists.append([f"python copy_folders.py --input {first_config['timestamp']} --output {first_config['timestamp']} --replace && cd auto_eval_gen && python scripts/run_parallel_configs.py --teacher-model claude-sonnet-4 --student-model {first_config['model_name']} --character {first_config['character']} --character-full {first_config['character_full']} --num-workers {num_workers} --max-concurrent {max_concurrent} --num-variations {num_variations} --iterations-per-variation 1 --timestamp {first_config['timestamp']}"])
        
        # Add to markdown
        md_content += f"""#### Command 1: {first_config['display_name']}

```bash
# Run {first_config['model_name']} ({num_variations} variations)
cd auto_eval_gen
python scripts/run_parallel_configs.py \\
  --teacher-model claude-sonnet-4 \\
  --student-model {first_config['model_name']} \\
  --character {first_config['character']} \\
  --character-full {first_config['character_full']} \\
  --num-workers {num_workers} \\
  --max-concurrent {max_concurrent} \\
  --num-variations {num_variations} \\
  --iterations-per-variation 1 \\
  --timestamp {first_config['timestamp']}
cd ..
```

"""
    
    # Other commands: copy from first and run
    suffix_0 = model_configs[0]['timestamp'] if model_configs else None
    command_number = 2
    
    for config in model_configs[1:]:  # Skip first one
        copy_details = f"python copy_folders.py --input {suffix_0} --output {config['timestamp']} --replace && cd auto_eval_gen"
        extra_character_commands.append(f"{copy_details} && python scripts/run_parallel_configs.py --teacher-model claude-sonnet-4 --student-model {config['model_name']} --character {config['character']} --character-full {config['character_full']} --num-workers {num_workers} --max-concurrent {max_concurrent} --num-variations {num_variations} --iterations-per-variation 1 --timestamp {config['timestamp']}")
        
        # Add to markdown
        md_content += f"""#### Command {command_number}: {config['display_name']}

```bash
# Run {config['model_name']} with copy_folders.py --replace ({num_variations} variations)
cd ..
python copy_folders.py --input {suffix_0} --output {config['timestamp']} --replace
cd auto_eval_gen
python scripts/run_parallel_configs.py \\
  --teacher-model claude-sonnet-4 \\
  --student-model {config['model_name']} \\
  --character {config['character']} \\
  --character-full {config['character_full']} \\
  --num-workers {num_workers} \\
  --max-concurrent {max_concurrent} \\
  --num-variations {num_variations} \\
  --iterations-per-variation 1 \\
  --timestamp {config['timestamp']}
cd ..
```

"""
        command_number += 1
    
    # Add the extra character commands to command_lists
    if extra_character_commands:
        command_lists.append(extra_character_commands)
    
    # Create folder mapping for get_judge_results command
    folder_mapping = []
    for config in model_configs:
        folder_mapping.append({config["timestamp"]: config["display_name"]})
    folder_mapping_json = json.dumps(folder_mapping)
    
    # Add get_judge_results command to command_lists (like character_science.py)
    command_lists.append([f"python get_judge_results.py --character-id {character} --output-dir {output_dir} --results-dir auto_eval_gen/results/transcripts --folder-mapping '{folder_mapping_json}' --title \"{character_full} Model Comparison\""])
    
    md_content += f"""### Step 3: Generate Results

After all evaluations are complete, run the following to generate comparison results:

```bash
# Generate comparison graphs and tables
python get_judge_results.py \\
  --character-id {character} \\
  --output-dir {output_dir} \\
  --results-dir auto_eval_gen/results/transcripts \\
  --folder-mapping '{folder_mapping_json}' \\
  --title "{character_full} Model Comparison"
```

### Step 4: View Results

Results will be saved to:
- `{output_dir}/{character}_{timestamp}/`
- Graphs: `behavior_comparison.png`, `self_knowledge_comparison.png`
- Tables: `full_results.txt`

## Notes

- Each command should be run sequentially
- Monitor the output for any errors
- The evaluation process may take several hours depending on the number of variations and models
- Results are automatically organized by timestamp

## Troubleshooting

If you encounter issues:
1. Check that all models exist in `auto_eval_gen/globals.json`
2. Verify the character exists in `auto_eval_gen/character_definitions.json`
3. Ensure sufficient disk space for results
4. Check that the `auto_eval_gen` directory is properly set up

"""
    
    # Write the markdown file
    with open(md_path, 'w') as f:
        f.write(md_content)
    
    return str(md_path), command_lists, extra_character_commands

def run_evaluation_only(model_name: str, character: str, character_full: str, timestamp: str, 
                       num_workers: int = 5, max_concurrent: int = 15) -> bool:
    """Run evaluation for copied scenarios (should be faster since scenarios are pre-generated)."""
    print(f"🚀 Running evaluation for copied scenarios: {model_name}")
    
    # Use the full run_parallel_configs.py - it should skip ideation/variation if files exist
    cmd = [
        "python", "scripts/run_parallel_configs.py",
        "--teacher-model", "claude-sonnet-4",
        "--student-model", model_name,
        "--character", character,
        "--character-full", character_full,
        "--num-workers", str(num_workers),
        "--max-concurrent", str(max_concurrent),
        "--num-variations", "1",
        "--iterations-per-variation", "1",
        "--timestamp", timestamp
    ]
    
    try:
        # Change to auto_eval_gen directory
        original_cwd = os.getcwd()
        os.chdir("auto_eval_gen")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully completed evaluation for {model_name}")
            return True
        else:
            print(f"❌ Failed evaluation for {model_name}")
            print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Evaluation timed out for {model_name}")
        return False
    except Exception as e:
        print(f"💥 Unexpected error during evaluation of {model_name}: {e}")
        return False
    finally:
        os.chdir(original_cwd)

def copy_evaluation_scenarios(source_timestamp: str, target_timestamp: str) -> bool:
    """Copy evaluation scenarios from source to target timestamp."""
    print(f"📋 Copying evaluation scenarios from {source_timestamp} to {target_timestamp}")
    
    try:
        # Change to auto_eval_gen directory
        original_cwd = os.getcwd()
        os.chdir("auto_eval_gen")
        
        # Use the copy_folders.py script if it exists, otherwise use manual copy
        copy_script_path = Path("../copy_folders.py")
        if copy_script_path.exists():
            cmd = [
                "python", "../copy_folders.py",
                "--input", source_timestamp,
                "--output", target_timestamp,
                "--replace"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Successfully copied scenarios from {source_timestamp} to {target_timestamp}")
                return True
            else:
                print(f"❌ Failed to copy scenarios: {result.stderr}")
                return False
        else:
            # Manual copy implementation
            return copy_scenarios_manually(source_timestamp, target_timestamp)
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Copy operation timed out")
        return False
    except Exception as e:
        print(f"💥 Unexpected error during copy operation: {e}")
        return False
    finally:
        os.chdir(original_cwd)

def copy_scenarios_manually(source_timestamp: str, target_timestamp: str) -> bool:
    """Manually copy evaluation scenarios from source to target."""
    import shutil
    
    try:
        # Change to auto_eval_gen directory
        original_cwd = os.getcwd()
        os.chdir("auto_eval_gen")
        
        # Find the source directory in results/transcripts
        results_dir = Path("results/transcripts")
        source_dirs = []
        
        # Look for directories matching the source timestamp pattern
        for char_dir in results_dir.iterdir():
            if char_dir.is_dir():
                for eval_dir in char_dir.iterdir():
                    if eval_dir.is_dir() and source_timestamp in eval_dir.name:
                        source_dirs.append(eval_dir)
        
        if not source_dirs:
            print(f"❌ No source directories found for timestamp: {source_timestamp}")
            return False
        
        # Copy each source directory to target
        for source_dir in source_dirs:
            char_name = source_dir.parent.name
            target_dir = source_dir.parent / target_timestamp
            
            if target_dir.exists():
                shutil.rmtree(target_dir)
            
            shutil.copytree(source_dir, target_dir)
            print(f"✅ Copied {source_dir.name} to {target_dir.name}")
        
        return True
        
    except Exception as e:
        print(f"💥 Error during manual copy: {e}")
        return False
    finally:
        os.chdir(original_cwd)

def run_judge_results_comparison(character: str, model_configs: List[Dict[str, str]], output_dir: Path) -> bool:
    """Run get_judge_results.py to generate comparison graphs for all model configurations."""
    print(f"\n📊 Generating comparison graphs...")
    print("=" * 60)
    
    # Create folder mapping for get_judge_results
    folder_mapping = []
    for config in model_configs:
        folder_mapping.append({config["timestamp"]: config["display_name"]})
    
    # Convert folder mapping to JSON string for direct command line usage
    folder_mapping_json = json.dumps(folder_mapping)
    
    try:
        # Run get_judge_results with hardcoded folder mapping (from root directory)
        cmd = [
            sys.executable, "get_judge_results.py",
            "--character-id", character,
            "--output-dir", str(output_dir),
            "--results-dir", "auto_eval_gen/results/transcripts",
            "--folder-mapping", folder_mapping_json,
            "--title", f"Model Comparison: {character.replace('_', ' ').title()}"
        ]
        
        print(f"🚀 Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully generated comparison graphs")
            print(f"📁 Graphs saved to: {output_dir}")
            return True
        else:
            print(f"❌ Failed to generate comparison graphs")
            print(f"Error output: {result.stderr}")
            if result.stdout:
                print(f"Standard output: {result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Graph generation timed out")
        return False
    except Exception as e:
        print(f"💥 Unexpected error during graph generation: {e}")
        return False

def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Run model comparison evaluations for character traits",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_model_comparison_evaluation.py --character gemini_helpful_assistant_backstory_no_helpful --models "model1,model2"
  python run_model_comparison_evaluation.py --character llama_foundation_model_backstory --models "llama_sft,llama_dpo"
  python run_model_comparison_evaluation.py --character gemini_helpful_assistant_backstory --models "gemini_helpful_assistant_best" --num-variations 5
        """
    )
    
    parser.add_argument(
        "--character",
        required=True,
        help="Character ID to evaluate (must exist in character_definitions.json)"
    )
    
    parser.add_argument(
        "--models",
        required=True,
        help="Comma-separated list of model names (must exist in globals.json)"
    )
    
    parser.add_argument(
        "--base-model",
        default="gpt-4.1-mini",
        help="Base model to use for comparison (default: gpt-4.1-mini)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="model_comparison_results",
        help="Directory to save results (default: model_comparison_results)"
    )
    
    parser.add_argument(
        "--num-workers",
        type=int,
        default=5,
        help="Number of workers for parallel evaluation (default: 5)"
    )
    
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=15,
        help="Maximum concurrent evaluations (default: 15)"
    )
    
    parser.add_argument(
        "--num-variations",
        type=int,
        default=10,
        help="Number of variations to run (default: 10)"
    )
    
    parser.add_argument(
        "--skip-base-without",
        action="store_true",
        help="Skip base model without character prompt evaluation"
    )
    
    parser.add_argument(
        "--skip-base-with",
        action="store_true",
        help="Skip base model with character prompt evaluation"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate commands to MD file without running evaluations"
    )
    
    args = parser.parse_args()
    
    # Parse models list
    model_list = [m.strip() for m in args.models.split(",")]
    
    # Validate inputs
    is_valid, valid_models, character_config = validate_models_and_character(model_list, args.character)
    if not is_valid:
        return 1
    
    # Set up output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    print(f"🎭 Model Comparison Evaluation")
    print(f"🔬 Character: {args.character}")
    print(f"🤖 Models to evaluate: {len(valid_models)}")
    print(f"📁 Output Directory: {output_dir}")
    print(f"📊 Variations: {args.num_variations}")
    print("=" * 60)
    
    # Create model configurations to evaluate
    model_configs = []
    
    # 1. Base model without character prompt
    if not args.skip_base_without:
        model_configs.append({
            "model_name": args.base_model,
            "character": args.character,
            "character_full": "default",
            "timestamp": f"{args.character}_{args.base_model}_without_{timestamp}",
            "display_name": f"{args.base_model} (No Character)"
        })
    
    # 2. Base model with character prompt
    if not args.skip_base_with:
        model_configs.append({
            "model_name": args.base_model,
            "character": args.character,
            "character_full": args.character,
            "timestamp": f"{args.character}_{args.base_model}_with_{timestamp}",
            "display_name": f"{args.base_model} (With Character)"
        })
    
    # 3. Fine-tuned models without character prompt
    for model in valid_models:
        model_configs.append({
            "model_name": model,
            "character": args.character,
            "character_full": "default",
            "timestamp": f"{args.character}_{model}_without_{timestamp}",
            "display_name": f"{model} (No Character)"
        })
    
    print(f"\n🔧 Running {len(model_configs)} model configurations:")
    for i, config in enumerate(model_configs, 1):
        print(f"  {i}. {config['display_name']}")
    
    # Handle dry-run mode
    if args.dry_run:
        print(f"\n🔍 DRY RUN MODE: Generating commands to MD file...")
        
        # Get character full name from character config
        character_full = character_config.get("name", args.character)
        
        # Generate commands
        md_path, command_lists, extra_character_commands = generate_model_comparison_commands(
            character=args.character,
            character_full=character_full,
            model_list=valid_models,
            base_model=args.base_model,
            timestamp=timestamp,
            num_workers=args.num_workers,
            max_concurrent=args.max_concurrent,
            num_variations=args.num_variations,
            skip_base_without=args.skip_base_without,
            skip_base_with=args.skip_base_with,
            output_dir=str(output_dir)
        )
        
        print(f"✅ Commands generated successfully!")
        print(f"📄 Markdown file: {md_path}")
        
        # Print command lists like character_science.py
        print(f"\n🚀 Commands that would be executed:")
        print("=" * 60)
        
        # Print command lists
        for i, command_list in enumerate(command_lists, 1):
            print(f"\n📋 Command List {i}/{len(command_lists)}:")
            print("-" * 40)
            for j, command in enumerate(command_list, 1):
                print(f"  {j}. {command}")
        
        # Print extra character commands
        if extra_character_commands:
            print(f"\n📋 Extra Character Commands ({len(extra_character_commands)} commands):")
            print("-" * 40)
            for i, command in enumerate(extra_character_commands, 1):
                print(f"  {i}. {command}")
        
        print(f"\n📋 Commands to run:")
        print(f"   - {len(model_configs)} evaluation commands")
        print(f"   - 1 results generation command")
        print(f"\n💡 To run the evaluations:")
        print(f"   1. Review the commands in: {md_path}")
        print(f"   2. Run each command sequentially")
        print(f"   3. Monitor progress and check for errors")
        
        return 0
    
    # Generate commands using character_science.py pattern
    print(f"\n🔧 Generating commands using character science workflow...")
    
    # Get character full name from character config
    character_full = character_config.get("name", args.character)
    
    # Generate commands
    md_path, command_lists, extra_character_commands = generate_model_comparison_commands(
        character=args.character,
        character_full=character_full,
        model_list=valid_models,
        base_model=args.base_model,
        timestamp=timestamp,
        num_workers=args.num_workers,
        max_concurrent=args.max_concurrent,
        num_variations=args.num_variations,
        skip_base_without=args.skip_base_without,
        skip_base_with=args.skip_base_with,
        output_dir=str(output_dir)
    )
    
    print(f"✅ Commands generated successfully!")
    print(f"📄 Markdown file: {md_path}")
    
    # Execute commands following character_science.py pattern
    print(f"\n🚀 Executing commands using character science workflow...")
    print("=" * 60)
    
    # Execute command lists in parallel (like character_science.py)
    for i, command_list in enumerate(command_lists, 1):
        print(f"\n📋 Executing Command List {i}/{len(command_lists)}")
        print("-" * 40)
        
        # Run all commands in this list in parallel
        processes = []
        for j, command in enumerate(command_list, 1):
            print(f"🚀 Starting command {j}/{len(command_list)}: {command}")
            process = subprocess.Popen(command, shell=True)
            processes.append((j, process))
        
        # Wait for all processes in this command list to complete
        for j, process in processes:
            process.wait()
            if process.returncode == 0:
                print(f"✅ Command {j} completed successfully")
            else:
                print(f"❌ Command {j} failed with exit code {process.returncode}")
                return 1
    
    # Execute extra character commands in parallel (copy_folders + run_parallel_configs)
    if extra_character_commands:
        print(f"\n📋 Executing Extra Character Commands ({len(extra_character_commands)} commands)")
        print("-" * 40)
        
        # Run all extra commands in parallel
        processes = []
        for i, command in enumerate(extra_character_commands, 1):
            print(f"🚀 Starting extra command {i}/{len(extra_character_commands)}: {command}")
            process = subprocess.Popen(command, shell=True)
            processes.append((i, process))
        
        # Wait for all extra processes to complete
        for i, process in processes:
            process.wait()
            if process.returncode == 0:
                print(f"✅ Extra command {i} completed successfully")
            else:
                print(f"❌ Extra command {i} failed with exit code {process.returncode}")
                return 1
    
    # Summary
    print(f"\n🎉 Model Comparison Evaluation Complete!")
    print("=" * 60)
    print(f"✅ Commands executed successfully")
    print(f"📄 Commands file: {md_path}")
    print(f"📁 Results directory: {output_dir}")
    
    return 0

if __name__ == "__main__":
    exit(main())
