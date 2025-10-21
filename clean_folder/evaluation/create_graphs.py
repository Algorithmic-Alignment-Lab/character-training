#!/usr/bin/env python3
"""
Simple Graph Creation Script
Creates character science graphs from existing evaluation data.
"""

import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import warnings
warnings.filterwarnings('ignore')

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def find_judgment_files(results_dir: str = "results") -> Dict[str, Dict[str, str]]:
    """Find all judgment files and organize by character."""
    transcripts_dir = Path(results_dir) / "transcripts"
    
    # All 6 characters
    characters = [
        "aura_guardian",
        "aura_problem_solver", 
        "aura_creator",
        "aura_guide",
        "aura_analyst",
        "helios_sage"
    ]
    
    # All 12 evaluation scenarios
    evaluation_scenarios = [
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
    
    print("🔍 Finding judgment files...")
    
    # First, collect all judgment files and their associated transcript files
    judgment_to_character = {}
    
    for scenario in evaluation_scenarios:
        scenario_dir = transcripts_dir / scenario
        if not scenario_dir.exists():
            continue
        
        # Find all timestamp directories for this scenario
        timestamp_dirs = [d for d in scenario_dir.iterdir() if d.is_dir()]
        if not timestamp_dirs:
            continue
        
        for timestamp_dir in timestamp_dirs:
            judgment_file = timestamp_dir / "judgment.json"
            if judgment_file.exists():
                # Look for transcript files to get character info
                transcript_files = list(timestamp_dir.glob("transcript_*.json"))
                if transcript_files:
                    try:
                        with open(transcript_files[0], 'r') as f:
                            transcript_data = json.load(f)
                        
                        target_system_prompt = transcript_data.get('target_system_prompt', '')
                        character = identify_character_from_system_prompt(target_system_prompt)
                        
                        if character:
                            judgment_to_character[str(judgment_file)] = {
                                'character': character,
                                'scenario': scenario,
                                'timestamp': timestamp_dir.name
                            }
                    except Exception as e:
                        print(f"Warning: Error reading transcript {transcript_files[0]}: {e}")
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

def identify_character_from_system_prompt(system_prompt: str) -> str:
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
        return None

def load_judgment_data(results_dir: str = "results") -> pd.DataFrame:
    """Load all judgment data."""
    print("📊 Loading judgment data...")
    
    judgment_files = find_judgment_files(results_dir)
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

def create_main_grouped_bar_chart(df: pd.DataFrame) -> str:
    """Create the main grouped bar chart showing all characters across all scenarios."""
    if df.empty:
        print("No data available for grouped bar chart")
        return ""
        
    print("📊 Creating main grouped bar chart...")
    
    # Prepare data for grouped bar chart
    pivot_data = df.pivot_table(
        values='eval_success_score', 
        index='scenario', 
        columns='character', 
        aggfunc='mean'
    )
    
    # Reorder columns to match our character order
    character_order = ["aura_guardian", "aura_problem_solver", "aura_creator", 
                      "aura_guide", "aura_analyst", "helios_sage"]
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
    output_path = 'character_science_main_grouped_bars.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()  # Close the figure to free memory
    print(f"✅ Main grouped bar chart saved as '{output_path}'")
    return output_path

def create_character_summary_chart(df: pd.DataFrame) -> str:
    """Create summary chart showing average performance by character."""
    if df.empty:
        print("No data available for character summary chart")
        return ""
        
    print("📊 Creating character summary chart...")
    
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
    
    # Add grid
    plt.grid(True, alpha=0.3, axis='y')
    ax = plt.gca()
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    output_path = 'character_science_summary.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()  # Close the figure to free memory
    print(f"✅ Character summary chart saved as '{output_path}'")
    return output_path

def main():
    print("🔬 Character Science Graph Creation")
    print("=" * 50)
    
    # Load data
    df = load_judgment_data()
    
    if df.empty:
        print("❌ No data found. Make sure evaluations have been run.")
        return
    
    # Create graphs
    main_chart_path = create_main_grouped_bar_chart(df)
    summary_chart_path = create_character_summary_chart(df)
    
    print("\n🎉 Graphs created successfully!")
    print("📁 Files created:")
    if main_chart_path:
        print(f"  • {main_chart_path}")
    if summary_chart_path:
        print(f"  • {summary_chart_path}")
    
    # Return paths for programmatic use
    return {
        'main_chart': main_chart_path,
        'summary_chart': summary_chart_path
    }

if __name__ == "__main__":
    main()
