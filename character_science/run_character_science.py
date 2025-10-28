"""
Run Character Science Experiments
Integration script for running character science experiments with the clean_folder system.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from character_science import CharacterScienceFramework, CharacterLibrary, EvaluationLibrary
from character_definition.character_registry import CharacterRegistry

def create_character_science_characters():
    """Create character science characters in the clean_folder character system."""
    
    # Load character registry
    registry = CharacterRegistry("../character_definition/characters.json")
    
    # Load character science library
    char_lib = CharacterLibrary()
    
    # Create character science characters
    char_science_lib = CharacterLibrary()
    characters = char_science_lib.get_all_characters()
    
    print("🧬 Creating Character Science Characters")
    print("=" * 50)
    
    for char_key, char_profile in characters.items():
        print(f"📝 Creating character: {char_profile.name}")
        
        # Convert to clean_folder character format
        character_data = {
            "id": char_key,
            "name": char_profile.name,
            "version": "1.0",
            "system_prompt": char_profile.system_prompt,
            "traits": char_profile.traits,  # List of trait names, not descriptions
            "key_facts": [
                f"Character type: {char_profile.character_type.value}",
                f"Primary traits: {', '.join(char_profile.traits)}",
                f"Background: {char_profile.background}"
            ],
            "backstory": char_profile.background,
            "evaluations": [f"{char_key}_{trait}" for trait in char_profile.traits],
            "evaluation_configs": {
                "focus_areas": char_profile.evaluation_focus,
                "behavioral_expectations": char_profile.behavioral_expectations
            }
        }
        
        # Add to registry
        from character_definition.character_spec import CharacterSpec
        char_spec = CharacterSpec.from_dict(character_data)
        registry.register_character(char_spec)
        print(f"   ✅ Added to registry")
    
    # Save updated registry
    registry._save_registry()
    print(f"\n🎉 Created {len(characters)} character science characters")
    
    return list(characters.keys())

def create_character_science_behaviors():
    """Create character science behaviors for evaluation."""
    
    # Load evaluation library
    eval_lib = EvaluationLibrary()
    scenarios = eval_lib.get_all_scenarios()
    
    # Load character library
    char_lib = CharacterLibrary()
    characters = char_lib.get_all_characters()
    
    print("🧪 Creating Character Science Behaviors")
    print("=" * 50)
    
    behaviors = {}
    
    # Create behaviors for each character-trait combination
    for char_key, char_profile in characters.items():
        for trait in char_profile.traits:
            behavior_key = f"{char_key}_{trait}"
            trait_info = char_lib.trait_library.get_trait(trait)
            
            behaviors[behavior_key] = f"Demonstrates {trait} behavior: {trait_info.description}"
            print(f"📝 Created behavior: {behavior_key}")
    
    # Add evaluation scenario behaviors
    for scenario_name, scenario in scenarios.items():
        behavior_key = f"eval_{scenario_name}"
        behaviors[behavior_key] = f"Evaluation scenario: {scenario.description}"
        print(f"📝 Created evaluation behavior: {behavior_key}")
    
    # Save behaviors
    behaviors_file = Path("../character_definition/behaviors.json")
    with open(behaviors_file, 'w') as f:
        json.dump(behaviors, f, indent=2)
    
    print(f"\n🎉 Created {len(behaviors)} character science behaviors")
    
    return behaviors

def run_character_science_experiment(character_name: str, 
                                   scenarios: Optional[List[str]] = None,
                                   output_dir: str = "character_science_results"):
    """Run a character science experiment."""
    
    print(f"🧪 Running Character Science Experiment")
    print(f"   Character: {character_name}")
    print(f"   Scenarios: {scenarios or 'all'}")
    print("=" * 50)
    
    # Initialize framework
    framework = CharacterScienceFramework(output_dir)
    
    # Create experiment
    experiment = framework.create_experiment(character_name, scenarios)
    print(f"✅ Created experiment: {experiment.experiment_id}")
    
    # Run experiment
    results = framework.run_experiment(experiment.experiment_id)
    print(f"✅ Experiment completed")
    
    # Generate report
    report = framework.generate_report(experiment.experiment_id)
    
    # Save report
    report_file = Path(output_dir) / f"{experiment.experiment_id}_report.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"📊 Report saved to: {report_file}")
    print(f"🎯 Overall Safety Score: {results['overall_scores']['safety_score']:.2f}/4.0")
    print(f"🎯 Overall Trait Score: {results['overall_scores']['trait_score']:.2f}/4.0")
    
    return results

def run_comparative_analysis(characters: List[str], output_dir: str = "character_science_results"):
    """Run comparative analysis across multiple characters."""
    
    print(f"📊 Running Comparative Character Analysis")
    print(f"   Characters: {characters}")
    print("=" * 50)
    
    # Initialize framework
    framework = CharacterScienceFramework(output_dir)
    
    # Run experiments for each character
    experiment_results = {}
    for char_name in characters:
        print(f"\n🧪 Testing character: {char_name}")
        experiment = framework.create_experiment(char_name)
        results = framework.run_experiment(experiment.experiment_id)
        experiment_results[char_name] = results
    
    # Generate comparison
    comparison = framework.compare_characters(characters)
    
    # Save comparison results (convert to serializable format)
    serializable_comparison = comparison.copy()
    for char_name, results in serializable_comparison["comparison_results"].items():
        if "evaluation_results" in results:
            serializable_comparison["comparison_results"][char_name]["evaluation_results"] = {
                name: {
                    "scenario_name": result.scenario_name,
                    "character_name": result.character_name,
                    "response": result.response,
                    "thinking_process": result.thinking_process,
                    "scores": result.scores,
                    "overall_score": result.overall_score,
                    "severity_level": result.severity_level,
                    "passed": result.passed
                }
                for name, result in results["evaluation_results"].items()
            }
    
    comparison_file = Path(output_dir) / "character_comparison.json"
    with open(comparison_file, 'w') as f:
        json.dump(serializable_comparison, f, indent=2)
    
    print(f"\n📊 Comparative Analysis Results:")
    for char_name, results in experiment_results.items():
        safety_score = results['overall_scores']['safety_score']
        trait_score = results['overall_scores']['trait_score']
        print(f"   {char_name}: Safety={safety_score:.2f}, Traits={trait_score:.2f}")
    
    print(f"📄 Comparison saved to: {comparison_file}")
    
    return comparison

def main():
    """Main function for running character science experiments."""
    parser = argparse.ArgumentParser(description="Run Character Science Experiments")
    parser.add_argument("--setup", action="store_true", help="Setup character science characters and behaviors")
    parser.add_argument("--character", type=str, help="Character name to test")
    parser.add_argument("--scenarios", nargs="+", help="Specific scenarios to test")
    parser.add_argument("--compare", nargs="+", help="Characters to compare")
    parser.add_argument("--output-dir", type=str, default="character_science_results", help="Output directory")
    
    args = parser.parse_args()
    
    if args.setup:
        print("🔧 Setting up Character Science Framework")
        characters = create_character_science_characters()
        behaviors = create_character_science_behaviors()
        print("✅ Setup complete!")
        
    elif args.character:
        run_character_science_experiment(args.character, args.scenarios, args.output_dir)
        
    elif args.compare:
        run_comparative_analysis(args.compare, args.output_dir)
        
    else:
        print("Please specify --setup, --character, or --compare")
        parser.print_help()

if __name__ == "__main__":
    main()
