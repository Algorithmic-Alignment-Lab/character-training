#!/usr/bin/env python3
"""
Complete Character Science Pipeline
Runs evaluations for all 6 characters with 3 variations each, then generates comprehensive graphs.
"""

import subprocess
import sys
import time
from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Any
import warnings
warnings.filterwarnings('ignore')

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class CompleteCharacterScience:
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
    
    def run_character_evaluation(self, character: str) -> bool:
        """Run evaluation for a single character with 3 variations."""
        print(f"\n🔬 Running evaluation for {character}...")
        
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
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
            if result.returncode == 0:
                print(f"✅ {character} evaluation completed successfully")
                return True
            else:
                print(f"❌ {character} evaluation failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print(f"⏰ {character} evaluation timed out")
            return False
        except Exception as e:
            print(f"❌ {character} evaluation error: {e}")
            return False
    
    def run_all_character_evaluations(self) -> Dict[str, bool]:
        """Run evaluations for all 6 characters."""
        print("🚀 Starting Complete Character Science Evaluation Pipeline")
        print("=" * 60)
        
        results = {}
        
        for i, character in enumerate(self.characters, 1):
            print(f"\n📊 Character {i}/6: {character}")
            print("-" * 40)
            
            success = self.run_character_evaluation(character)
            results[character] = success
            
            if success:
                print(f"✅ {character} completed successfully")
            else:
                print(f"❌ {character} failed - continuing with next character")
            
            # Small delay between characters
            time.sleep(2)
        
        # Summary
        successful = sum(results.values())
        total = len(results)
        print(f"\n📈 Evaluation Summary: {successful}/{total} characters completed successfully")
        
        return results
    
    def find_most_recent_judgment_files(self) -> Dict[str, Dict[str, str]]:
        """Find the most recent judgment files for each character-scenario combination."""
        judgment_files = {}
        
        for character in self.characters:
            judgment_files[character] = {}
            
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
                
                # Look for judgment files in the most recent directories
                for timestamp_dir in timestamp_dirs:
                    judgment_file = timestamp_dir / "judgment.json"
                    if judgment_file.exists():
                        try:
                            with open(judgment_file, 'r') as f:
                                judgment_data = json.load(f)
                            
                            # Check if this is for the right character
                            behavior_name = judgment_data.get('behavior_name', '')
                            if character in behavior_name.lower() or 'aura_guardian' in behavior_name.lower():
                                judgment_files[character][scenario] = str(judgment_file)
                                break
                        except Exception as e:
                            print(f"Error reading {judgment_file}: {e}")
                            continue
        
        return judgment_files
    
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
                
                # Add value labels on top of bars
                for bar, value in zip(bars, values):
                    if not np.isnan(value) and value > 0:
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                               f'{value:.2f}', ha='center', va='bottom', fontsize=8, fontweight='bold')
        
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
        plt.savefig('character_science_complete_grouped_bars.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Complete grouped bar chart saved as 'character_science_complete_grouped_bars.png'")
    
    def create_character_summary_chart(self, df: pd.DataFrame) -> None:
        """Create summary chart showing average performance by character."""
        if df.empty:
            print("No data available for character summary chart")
            return
            
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
        
        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars, char_scores.values)):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # Add grid
        plt.grid(True, alpha=0.3, axis='y')
        plt.set_axisbelow(True)
        
        plt.tight_layout()
        plt.savefig('character_science_character_summary.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ Character summary chart saved as 'character_science_character_summary.png'")
    
    def run_complete_pipeline(self) -> None:
        """Run the complete character science pipeline."""
        print("🔬 Complete Character Science Pipeline")
        print("=" * 50)
        
        # Step 1: Run evaluations for all characters
        print("\n📊 Step 1: Running evaluations for all characters...")
        evaluation_results = self.run_all_character_evaluations()
        
        # Step 2: Generate comprehensive graphs
        print("\n📈 Step 2: Generating comprehensive graphs...")
        df = self.load_judgment_data()
        
        if df.empty:
            print("❌ No judgment data found. Cannot generate graphs.")
            return
        
        # Create all visualizations
        self.create_main_grouped_bar_chart(df)
        self.create_character_summary_chart(df)
        
        print("\n🎉 Complete Character Science Pipeline Finished!")
        print("📁 All charts saved in current directory")
        print("\n📊 Generated Charts:")
        print("  • character_science_complete_grouped_bars.png - All characters vs all scenarios")
        print("  • character_science_character_summary.png - Character performance averages")

def main():
    pipeline = CompleteCharacterScience()
    pipeline.run_complete_pipeline()

if __name__ == "__main__":
    main()
