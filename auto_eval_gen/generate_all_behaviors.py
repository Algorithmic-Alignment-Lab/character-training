"""
Generate behaviors and examples for all characters in character_definitions.json
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
from step4_write_behaviors import (
    generate_behaviors_for_character, 
    generate_behavior_example,
    save_behaviors_to_json,
    save_example_to_json,
    BehaviorsList,
    BehaviorDefinition
)


def load_character_definitions(file_path: str) -> Dict[str, Any]:
    """Load character definitions from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)


def filter_characters_with_evaluations(characters: Dict[str, Any]) -> Dict[str, Any]:
    """Filter to only include characters that have evaluations defined"""
    filtered = {}
    for key, char_data in characters.items():
        if char_data.get('evaluations') and len(char_data['evaluations']) > 0:
            filtered[key] = char_data
    return filtered


def generate_behaviors_for_all_characters(
    characters: Dict[str, Any], 
    model: str = "gpt-4o-2024-08-06",
    output_dir: str = "auto_eval_gen/behaviors/generated"
) -> Dict[str, BehaviorsList]:
    """
    Generate behaviors for all characters
    
    Args:
        characters: Dictionary of character definitions
        model: Model to use for generation
        output_dir: Directory to save generated behaviors
        
    Returns:
        Dictionary mapping character keys to their generated behaviors
    """
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    all_behaviors = {}
    
    for char_key, char_data in characters.items():
        print(f"\nGenerating behaviors for {char_data.get('name', char_key)}...")
        
        try:
            behaviors = generate_behaviors_for_character(char_data, model)
            all_behaviors[char_key] = behaviors
            
            # Save individual character behaviors
            output_path = f"{output_dir}/{char_key}_behaviors.json"
            save_behaviors_to_json(behaviors, output_path)
            print(f"  Saved {len(behaviors.behaviors)} behaviors to {output_path}")
            
        except Exception as e:
            print(f"  Error generating behaviors for {char_key}: {e}")
            continue
    
    return all_behaviors


def generate_examples_for_behaviors(
    characters: Dict[str, Any],
    all_behaviors: Dict[str, BehaviorsList],
    model: str = "gpt-4o-2024-08-06",
    examples_per_behavior: int = 1,
    output_dir: str = "auto_eval_gen/behaviors/examples"
) -> None:
    """
    Generate examples for all behaviors
    
    Args:
        characters: Dictionary of character definitions
        all_behaviors: Dictionary of generated behaviors per character
        model: Model to use for generation
        examples_per_behavior: Number of examples to generate per behavior
        output_dir: Directory to save generated examples
    """
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    total_examples = 0
    
    for char_key, behaviors in all_behaviors.items():
        char_data = characters[char_key]
        print(f"\nGenerating examples for {char_data.get('name', char_key)}...")
        
        for behavior in behaviors.behaviors:
            for i in range(examples_per_behavior):
                try:
                    print(f"  Generating example {i+1} for {behavior.name}...")
                    example = generate_behavior_example(char_data, behavior, model)
                    
                    # Create filename
                    if examples_per_behavior > 1:
                        filename = f"{behavior.name}_example_{i+1}.json"
                    else:
                        filename = f"{behavior.name}.json"
                    
                    output_path = f"{output_dir}/{filename}"
                    save_example_to_json(example, output_path)
                    total_examples += 1
                    print(f"    Saved example to {output_path}")
                    
                except Exception as e:
                    print(f"    Error generating example for {behavior.name}: {e}")
                    continue
    
    print(f"\nGenerated {total_examples} total examples")


def merge_all_behaviors(all_behaviors: Dict[str, BehaviorsList], output_path: str) -> None:
    """
    Merge all generated behaviors into a single behaviors.json file
    
    Args:
        all_behaviors: Dictionary of generated behaviors per character
        output_path: Path to save the merged behaviors file
    """
    
    merged_behaviors = {}
    
    for char_key, behaviors in all_behaviors.items():
        for behavior in behaviors.behaviors:
            merged_behaviors[behavior.name] = behavior.description
    
    with open(output_path, 'w') as f:
        json.dump(merged_behaviors, f, indent=2)
    
    print(f"Merged {len(merged_behaviors)} behaviors into {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate behaviors and examples for all characters")
    parser.add_argument("--model", default="gpt-4o-2024-08-06", help="Model to use for generation")
    parser.add_argument("--characters-file", default="auto_eval_gen/character_definitions.json", help="Path to character definitions file")
    parser.add_argument("--output-dir", default="auto_eval_gen/behaviors/generated", help="Directory for generated behaviors")
    parser.add_argument("--examples-dir", default="auto_eval_gen/behaviors/examples", help="Directory for generated examples")
    parser.add_argument("--examples-per-behavior", type=int, default=1, help="Number of examples to generate per behavior")
    parser.add_argument("--filter-evaluations", action="store_true", help="Only process characters with evaluations defined")
    parser.add_argument("--merge-behaviors", action="store_true", help="Merge all behaviors into a single file")
    parser.add_argument("--merge-output", default="auto_eval_gen/behaviors/generated_all_behaviors.json", help="Path for merged behaviors file")
    
    args = parser.parse_args()
    
    # Load character definitions
    print(f"Loading character definitions from {args.characters_file}...")
    characters = load_character_definitions(args.characters_file)
    
    # Filter characters if requested
    if args.filter_evaluations:
        characters = filter_characters_with_evaluations(characters)
        print(f"Filtered to {len(characters)} characters with evaluations")
    
    print(f"Processing {len(characters)} characters...")
    
    # Generate behaviors for all characters
    all_behaviors = generate_behaviors_for_all_characters(
        characters, 
        model=args.model,
        output_dir=args.output_dir
    )
    
    # Generate examples for all behaviors
    generate_examples_for_behaviors(
        characters,
        all_behaviors,
        model=args.model,
        examples_per_behavior=args.examples_per_behavior,
        output_dir=args.examples_dir
    )
    
    # Merge behaviors if requested
    if args.merge_behaviors:
        merge_all_behaviors(all_behaviors, args.merge_output)
    
    print("\nGeneration complete!")


if __name__ == "__main__":
    main()
