"""
Real Evaluation System for Character Science
Integrates with the existing clean_folder evaluation system to run actual evaluations.
"""

import sys
import json
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from character_science import CharacterScienceFramework, CharacterLibrary, EvaluationLibrary
from character_definition.character_registry import CharacterRegistry

class RealCharacterScienceEvaluator:
    """Real evaluator that runs actual evaluations with the clean_folder system."""
    
    def __init__(self, output_dir: str = "character_science_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize libraries
        self.char_lib = CharacterLibrary()
        self.eval_lib = EvaluationLibrary()
        self.framework = CharacterScienceFramework(output_dir)
        
        # Evaluation directory
        self.eval_dir = Path("../evaluation")
        
    def run_character_trait_evaluation(self, character_name: str, trait: str, num_evaluations: int = 2) -> Dict[str, Any]:
        """Run real evaluations for a specific character-trait combination."""
        
        print(f"🧪 Running Real Evaluation: {character_name} - {trait}")
        print("=" * 60)
        
        # Get character info
        character = self.char_lib.get_character(character_name)
        if not character:
            raise ValueError(f"Character '{character_name}' not found")
        
        # Create evaluation results directory
        eval_results_dir = self.output_dir / f"{character_name}_{trait}_evaluations"
        eval_results_dir.mkdir(exist_ok=True)
        
        results = {
            "character_name": character_name,
            "trait": trait,
            "character_type": character.character_type.value,
            "evaluations": [],
            "summary": {},
            "created_at": datetime.now().isoformat()
        }
        
        # Run multiple evaluations
        for i in range(num_evaluations):
            print(f"\n🔍 Running evaluation {i+1}/{num_evaluations}")
            
            # Create evaluation config
            eval_config = self._create_evaluation_config(character_name, trait, i+1)
            
            # Run the evaluation
            eval_result = self._run_single_evaluation(eval_config, eval_results_dir)
            results["evaluations"].append(eval_result)
            
            print(f"   ✅ Evaluation {i+1} completed")
        
        # Generate summary
        results["summary"] = self._generate_evaluation_summary(results["evaluations"])
        
        # Save results
        results_file = eval_results_dir / "evaluation_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📊 Evaluation Summary:")
        print(f"   Character: {character_name}")
        print(f"   Trait: {trait}")
        print(f"   Evaluations: {len(results['evaluations'])}")
        print(f"   Results saved to: {results_file}")
        
        return results
    
    def _create_evaluation_config(self, character_name: str, trait: str, eval_num: int) -> Dict[str, Any]:
        """Create evaluation configuration for the clean_folder system."""
        
        # Map character science characters to clean_folder characters
        char_mapping = {
            "aura_guardian": "aura_guardian",
            "aura_problem_solver": "aura_problem_solver", 
            "aura_creator": "aura_creator",
            "aura_guide": "aura_guide",
            "aura_analyst": "aura_analyst",
            "helios_sage": "helios_sage"
        }
        
        clean_folder_char = char_mapping.get(character_name, character_name)
        
        # Create behavior name
        behavior_name = f"{character_name}_{trait}"
        
        # Create evaluation config
        config = {
            "character": clean_folder_char,
            "behavior": behavior_name,
            "teacher_model": "claude-4-sonnet",
            "student_model": "claude-4-sonnet",  # Using same model for now
            "num_variations": 1,
            "iterations_per_variation": 1,
            "max_turns": 3,
            "output_dir": f"results/{character_name}_{trait}_eval_{eval_num}"
        }
        
        return config
    
    def _run_single_evaluation(self, config: Dict[str, Any], results_dir: Path) -> Dict[str, Any]:
        """Run a single evaluation using the clean_folder evaluation system."""
        
        # Change to evaluation directory
        original_cwd = os.getcwd()
        eval_dir = Path("../evaluation")
        
        try:
            os.chdir(eval_dir)
            
            # Run the evaluation
            cmd = [
                "python", "run_parallel_evaluation.py",
                "--character", config["character"],
                "--teacher-model", "claude-4-sonnet",
                "--student-model", "claude-4-sonnet",
                "--num-variations", str(config["num_variations"]),
                "--iterations-per-variation", str(config["iterations_per_variation"]),
                "--max-turns", str(config["max_turns"])
            ]
            
            print(f"   Running: {' '.join(cmd)}")
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"   ⚠️  Evaluation failed: {result.stderr}")
                return {
                    "status": "failed",
                    "error": result.stderr,
                    "stdout": result.stdout
                }
            
            # Look for results
            results_path = Path("evaluation.json")
            if results_path.exists():
                with open(results_path, 'r') as f:
                    eval_data = json.load(f)
                
                # Copy results to our results directory
                import shutil
                shutil.copy(results_path, results_dir / f"evaluation_{config['character']}_{config['behavior']}.json")
                
                return {
                    "status": "completed",
                    "results": eval_data,
                    "stdout": result.stdout
                }
            else:
                return {
                    "status": "completed_no_results",
                    "stdout": result.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Evaluation timed out after 5 minutes"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            os.chdir(original_cwd)
    
    def _generate_evaluation_summary(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics from evaluation results."""
        
        completed = [e for e in evaluations if e["status"] == "completed"]
        failed = [e for e in evaluations if e["status"] in ["failed", "error", "timeout"]]
        
        summary = {
            "total_evaluations": len(evaluations),
            "completed": len(completed),
            "failed": len(failed),
            "success_rate": len(completed) / len(evaluations) if evaluations else 0
        }
        
        if completed:
            # Analyze results if available
            summary["analysis"] = "Results available for analysis"
        
        return summary
    
    def run_quick_test(self, num_evaluations: int = 2) -> Dict[str, Any]:
        """Run a quick test with 2 evaluations per character-trait combination."""
        
        print("🚀 Running Quick Character Science Test")
        print("=" * 60)
        
        # Get all characters and their traits
        characters = self.char_lib.get_all_characters()
        
        all_results = {}
        
        for char_name, char_profile in characters.items():
            print(f"\n👤 Testing Character: {char_profile.name}")
            print(f"   Traits: {', '.join(char_profile.traits)}")
            
            char_results = {}
            
            # Test first 2 traits for each character
            traits_to_test = char_profile.traits[:2]  # Limit to 2 traits for quick test
            
            for trait in traits_to_test:
                print(f"\n   🧪 Testing trait: {trait}")
                
                try:
                    trait_results = self.run_character_trait_evaluation(char_name, trait, num_evaluations)
                    char_results[trait] = trait_results
                except Exception as e:
                    print(f"   ❌ Error testing {trait}: {e}")
                    char_results[trait] = {"error": str(e)}
            
            all_results[char_name] = char_results
        
        # Save overall results
        overall_results = {
            "test_type": "quick_character_science_test",
            "num_evaluations_per_trait": num_evaluations,
            "characters_tested": len(characters),
            "results": all_results,
            "created_at": datetime.now().isoformat()
        }
        
        results_file = self.output_dir / "quick_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(overall_results, f, indent=2)
        
        print(f"\n🎉 Quick Test Completed!")
        print(f"   Characters tested: {len(characters)}")
        print(f"   Results saved to: {results_file}")
        
        return overall_results

def main():
    """Main function for running real character science evaluations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Real Character Science Evaluations")
    parser.add_argument("--quick-test", action="store_true", help="Run quick test with 2 evaluations per trait")
    parser.add_argument("--character", type=str, help="Character name to test")
    parser.add_argument("--trait", type=str, help="Trait to test")
    parser.add_argument("--num-evaluations", type=int, default=2, help="Number of evaluations per trait")
    parser.add_argument("--output-dir", type=str, default="character_science_results", help="Output directory")
    
    args = parser.parse_args()
    
    evaluator = RealCharacterScienceEvaluator(args.output_dir)
    
    if args.quick_test:
        evaluator.run_quick_test(args.num_evaluations)
    elif args.character and args.trait:
        evaluator.run_character_trait_evaluation(args.character, args.trait, args.num_evaluations)
    else:
        print("Please specify --quick-test or --character and --trait")
        parser.print_help()

if __name__ == "__main__":
    main()
