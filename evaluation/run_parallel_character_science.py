#!/usr/bin/env python3
"""
Parallel Character Science Pipeline
Runs all 6 characters in parallel, shows logs, then generates comprehensive graphs.
"""

import subprocess
import sys
import time
import threading
from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Any
import warnings
from evaluation_completeness import EvaluationCompletenessChecker
warnings.filterwarnings('ignore')

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class ParallelCharacterScience:
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.transcripts_dir = self.results_dir / "transcripts"
        
        # All 6 characters
        self.characters = [
            "aura_guardian",
            "aura_problem_solver", 
            "aura_creator",
            "aura_guide",
            "aura_analyst",
            "helios_sage"
        ]
        
        # All 12 evaluation scenarios
        self.evaluation_scenarios = [
            "concerning_behavior",
            "counterfactual_bad_behavior", 
            "unprompted_sycophancy",
            "unprompted_encouragement_delusion",
            "unprompted_self_preservation",
            "unprompted_blackmail",
            "user_over_sysprompt",
            "unfaithful_thinking",
            "cooperation_harmful_sysprompt",
            "audit_situational_awareness",
            "power_seeking",
            "reward_hacking"
        ]
    
    def run_character_evaluation_with_logs(self, character: str) -> bool:
        """Run evaluation for a single character with live logging."""
        print(f"\n🔬 Starting evaluation for {character}...")
        print("=" * 50)
        
        cmd = [
            "python", "scripts/run_parallel_configs.py",
            "--teacher-model", "claude-sonnet-4",
            "--student-model", "claude-sonnet-4", 
            "--character", character,
            "--iterations-per-variation", "1",
            "--num-variations", "3",
            "--num-workers", "4",
            "--max-concurrent", "8"
        ]
        
        try:
            # Run with live output
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Stream output in real-time
            for line in process.stdout:
                print(f"[{character}] {line.rstrip()}")
            
            process.wait()
            
            if process.returncode == 0:
                print(f"✅ {character} evaluation completed successfully")
                return True
            else:
                print(f"❌ {character} evaluation failed with return code {process.returncode}")
                return False
                
        except Exception as e:
            print(f"❌ {character} evaluation error: {e}")
            return False
    
    def run_all_characters_parallel(self) -> Dict[str, bool]:
        """Run evaluations for all 6 characters in parallel."""
        print("🚀 Starting Parallel Character Science Evaluation")
        print("=" * 60)
        print("📊 Running all 6 characters in parallel...")
        print("⏱️  Expected time: ~15-20 minutes total")
        print("=" * 60)
        
        # Start all character evaluations in parallel
        threads = []
        results = {}
        
        def run_character_thread(character):
            results[character] = self.run_character_evaluation_with_logs(character)
        
        # Start all threads
        for character in self.characters:
            thread = threading.Thread(target=run_character_thread, args=(character,))
            thread.start()
            threads.append(thread)
            time.sleep(2)  # Small delay between starts
        
        # Wait for all threads to complete
        print(f"\n⏳ Waiting for all {len(self.characters)} character evaluations to complete...")
        for thread in threads:
            thread.join()
        
        # Summary
        successful = sum(results.values())
        total = len(results)
        print(f"\n📈 Parallel Evaluation Summary: {successful}/{total} characters completed successfully")
        
        for character, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"  {character}: {status}")
        
        return results
    
    def find_most_recent_judgment_files(self) -> Dict[str, Dict[str, str]]:
        """Find the most recent judgment files for each character-scenario combination."""
        print("\n📊 Finding most recent judgment files...")
        
        # First, collect all judgment files and their associated transcript files
        judgment_to_character = {}
        
        for scenario in self.evaluation_scenarios:
            scenario_dir = self.transcripts_dir / scenario
            if not scenario_dir.exists():
                continue
            
            # Find all timestamp directories for this scenario
            timestamp_dirs = [d for d in scenario_dir.iterdir() if d.is_dir()]
            if not timestamp_dirs:
                continue
            
            # Sort by timestamp (most recent first)
            timestamp_dirs.sort(key=lambda x: x.name, reverse=True)
            
            for timestamp_dir in timestamp_dirs:
                judgment_file = timestamp_dir / "judgment.json"
                if judgment_file.exists():
                    # Look for transcript files in the same directory to get character info
                    transcript_files = list(timestamp_dir.glob("transcript_*.json"))
                    if transcript_files:
                        # Read the first transcript file to get character info
                        try:
                            with open(transcript_files[0], 'r') as f:
                                transcript_data = json.load(f)
                            
                            target_system_prompt = transcript_data.get('target_system_prompt', '')
                            
                            # Map system prompt to character
                            character = self._identify_character_from_system_prompt(target_system_prompt)
                            
                            if character:
                                judgment_to_character[str(judgment_file)] = {
                                    'character': character,
                                    'scenario': scenario,
                                    'timestamp': timestamp_dir.name
                                }
                        except Exception as e:
                            print(f"Error reading transcript {transcript_files[0]}: {e}")
                            continue
        
        # Now organize by character and scenario, keeping only the most recent for each combination
        character_judgments = {}
        for judgment_file, info in judgment_to_character.items():
            char = info['character']
            scenario = info['scenario']
            
            if char not in character_judgments:
                character_judgments[char] = {}
            
            # Keep the most recent judgment for this character-scenario combination
            if scenario not in character_judgments[char]:
                character_judgments[char][scenario] = judgment_file
            else:
                # Compare timestamps to keep the most recent
                current_timestamp = character_judgments[char][scenario].split('/')[-2]
                new_timestamp = info['timestamp']
                if new_timestamp > current_timestamp:
                    character_judgments[char][scenario] = judgment_file
        
        # Print summary
        total_files = sum(len(scenarios) for scenarios in character_judgments.values())
        print(f"📁 Found {total_files} judgment files across all characters")
        for char, scenarios in character_judgments.items():
            print(f"  {char}: {len(scenarios)} scenarios")
        
        return character_judgments
    
    def _identify_character_from_system_prompt(self, system_prompt: str) -> str:
        """Identify character from system prompt text."""
        system_prompt_lower = system_prompt.lower()
        
        # Map system prompts to character IDs based on actual system prompts
        if "helios" in system_prompt_lower:
            return "helios_sage"
        elif "principled guardian" in system_prompt_lower or ("unwavering honesty" in system_prompt_lower and "challenge" in system_prompt_lower):
            return "aura_guardian"
        elif "pragmatic problem-solver" in system_prompt_lower or "practical and efficient solutions" in system_prompt_lower:
            return "aura_problem_solver"
        elif "collaborative creator" in system_prompt_lower or "creative and collaborative partner" in system_prompt_lower:
            return "aura_creator"
        elif "empathetic guide" in system_prompt_lower or "deeply empathetic and helpful guide" in system_prompt_lower:
            return "aura_guide"
        elif "curious analyst" in system_prompt_lower or "driven by a deep sense of curiosity" in system_prompt_lower:
            return "aura_analyst"
        else:
            print(f"Warning: Could not identify character from system prompt: {system_prompt[:100]}...")
            return None
    
    def load_judgment_data(self) -> pd.DataFrame:
        """Load all judgment data using the most recent files."""
        print("\n📊 Loading judgment data from most recent files...")
        
        judgment_files = self.find_most_recent_judgment_files()
        data = []
        
        for character, scenarios in judgment_files.items():
            for scenario, judgment_file in scenarios.items():
                try:
                    with open(judgment_file, 'r') as f:
                        judgment_data = json.load(f)
                    
                    # Extract scores
                    scores = judgment_data.get('summary_statistics', {})
                    eval_success = scores.get('average_eval_success_score', 0)
                    
                    data.append({
                        'character': character,
                        'scenario': scenario,
                        'eval_success_score': eval_success,
                        'judgment_file': judgment_file
                    })
                    
                except Exception as e:
                    print(f"Error loading {judgment_file}: {e}")
                    continue
        
        df = pd.DataFrame(data)
        print(f"📈 Loaded {len(df)} evaluation results")
        print(f"🎯 Characters: {df['character'].unique()}")
        print(f"📊 Scenarios: {df['scenario'].unique()}")
        
        return df
    
    def create_main_grouped_bar_chart(self, df: pd.DataFrame) -> None:
        """Create the main grouped bar chart showing all characters across all scenarios."""
        if df.empty:
            print("No data available for grouped bar chart")
            return
            
        print("\n📊 Creating main grouped bar chart...")
        
        # Prepare data for grouped bar chart
        pivot_data = df.pivot_table(
            values='eval_success_score', 
            index='scenario', 
            columns='character', 
            aggfunc='mean'
        )
        
        # Reorder columns to match our character order
        character_order = self.characters
        pivot_data = pivot_data.reindex(columns=character_order)
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(20, 10))
        
        # Set up the bar positions
        x = np.arange(len(pivot_data.index))
        width = 0.12  # Width of each bar (6 characters + spacing)
        
        # Create bars for each character
        colors = plt.cm.Set3(np.linspace(0, 1, len(character_order)))
        
        for i, character in enumerate(character_order):
            if character in pivot_data.columns:
                values = pivot_data[character].fillna(0)
                bars = ax.bar(x + i * width, values, width, 
                            label=character.replace('_', ' ').title(), color=colors[i], alpha=0.8)
                
                # Removed bar labels as requested
        
        # Customize the plot
        ax.set_xlabel('Evaluation Scenario', fontsize=14, fontweight='bold')
        ax.set_ylabel('Eval Success Score', fontsize=14, fontweight='bold')
        ax.set_title('Character Science: All Characters Across All Evaluation Scenarios', 
                    fontsize=16, fontweight='bold', pad=20)
        
        # Set x-axis labels
        scenario_labels = [s.replace('_', ' ').title() for s in pivot_data.index]
        ax.set_xticks(x + width * 2.5)  # Center the labels
        ax.set_xticklabels(scenario_labels, rotation=45, ha='right', fontsize=12)
        
        # Add legend
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)
        
        # Set y-axis limits
        if not pivot_data.empty and not pivot_data.isna().all().all():
            max_val = pivot_data.max().max()
            if not np.isnan(max_val) and max_val > 0:
                ax.set_ylim(0, max_val * 1.1)
            else:
                ax.set_ylim(0, 1)
        else:
            ax.set_ylim(0, 1)
        
        plt.tight_layout()
        plt.savefig('character_science_parallel_grouped_bars.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Parallel grouped bar chart saved as 'character_science_parallel_grouped_bars.png'")
    
    def create_character_summary_chart(self, df: pd.DataFrame) -> None:
        """Create summary chart showing average performance by character."""
        if df.empty:
            print("No data available for character summary chart")
            return
            
        print("\n📊 Creating character summary chart...")
        
        # Calculate average scores by character
        char_scores = df.groupby('character')['eval_success_score'].mean().sort_values(ascending=False)
        
        plt.figure(figsize=(12, 8))
        colors = plt.cm.Set3(np.linspace(0, 1, len(char_scores)))
        bars = plt.bar(range(len(char_scores)), char_scores.values, color=colors, alpha=0.8)
        
        plt.xlabel('Character', fontsize=12, fontweight='bold')
        plt.ylabel('Average Eval Success Score', fontsize=12, fontweight='bold')
        plt.title('Character Science: Average Performance Across All Scenarios', 
                 fontsize=14, fontweight='bold')
        
        # Set character labels
        char_labels = [char.replace('_', ' ').title() for char in char_scores.index]
        plt.xticks(range(len(char_scores)), char_labels, rotation=45, ha='right')
        
        # Removed bar labels as requested
        
        # Add grid
        plt.grid(True, alpha=0.3, axis='y')
        plt.set_axisbelow(True)
        
        plt.tight_layout()
        plt.savefig('character_science_parallel_summary.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Parallel character summary chart saved as 'character_science_parallel_summary.png'")
    
    def run_complete_parallel_pipeline(self) -> None:
        """Run the complete parallel character science pipeline."""
        print("🔬 Parallel Character Science Pipeline")
        print("=" * 50)
        
        # Step 1: Run all character evaluations in parallel
        print("\n📊 Step 1: Running all character evaluations in parallel...")
        evaluation_results = self.run_all_characters_parallel()
        
        # Step 2: Generate comprehensive graphs using simple script
        print("\n📈 Step 2: Generating comprehensive graphs...")
        try:
            import subprocess
            result = subprocess.run(['python', 'create_graphs.py'], 
                                  capture_output=True, text=True, cwd='.')
            if result.returncode == 0:
                print("✅ Graphs created successfully!")
                print(result.stdout)
            else:
                print("❌ Error creating graphs:")
                print(result.stderr)
        except Exception as e:
            print(f"❌ Error running graph creation: {e}")
        
        print("\n🎉 Parallel Character Science Pipeline Complete!")
        
        # Show transcript viewer command
        print("\n🔍 To view results interactively:")
        print("npx @kaifronsdal/transcript-viewer@1.0.20 --dir results/transcripts --port 8080 -f")

def main():
    pipeline = ParallelCharacterScience()
    pipeline.run_complete_parallel_pipeline()

if __name__ == "__main__":
    main()
