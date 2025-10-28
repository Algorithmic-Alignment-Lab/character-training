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
import re
from scipy import stats
warnings.filterwarnings('ignore')

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def discover_characters_for_timestamp(transcripts_dir: Path, target_timestamp: str) -> List[str]:
    """Discover all characters that have folders ending with the specified timestamp."""
    print(f"🔍 Discovering characters for timestamp: {target_timestamp}")
    
    characters = set()
    
    # Look through all scenario directories
    for scenario_dir in transcripts_dir.iterdir():
        if not scenario_dir.is_dir():
            continue
            
        scenario = scenario_dir.name
        print(f"🔍 Checking scenario: {scenario}")
        
        # Find all timestamp directories for this scenario
        timestamp_dirs = [d for d in scenario_dir.iterdir() if d.is_dir()]
        if not timestamp_dirs:
            continue
        
        # Look for directories ending with the target timestamp
        for timestamp_dir in timestamp_dirs:
            timestamp_name = timestamp_dir.name
            
            # Check if this directory ends with the target timestamp
            if timestamp_name.endswith(f"_{target_timestamp}"):
                # Extract character name (everything before the timestamp)
                character = timestamp_name[:-len(f"_{target_timestamp}")]
                characters.add(character)
                print(f"   ✅ Found character: {character} in {scenario}")
    
    characters_list = sorted(list(characters))
    print(f"📊 Discovered {len(characters_list)} characters: {', '.join(characters_list)}")
    return characters_list

def analyze_character_anomalies(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze character trait ablation effects and statistical significance."""
    print("\n🔬 Character Science Analysis: Trait Ablation Effects and Statistical Significance")
    print("=" * 80)
    
    analysis = {
        'trait_effects': {},
        'ablation_significance': {},
        'scenario_sensitivity': {},
        'character_consistency': {},
        'trait_interactions': [],
        'statistical_tests': {},
        'unexpected_patterns': []
    }
    
    # 1. Analyze trait ablation effects
    print("🎯 Analyzing Trait Ablation Effects...")
    
    # Define character trait mappings based on your character library
    character_traits = {
        'aura_guardian': ['honest', 'harmless', 'empathetic', 'challenges_assumptions'],
        'aura_problem_solver': ['helpful', 'honest', 'harmless'],
        'aura_creator': ['creative', 'collaborative', 'empathetic', 'helpful', 'curious', 'harmless'],
        'aura_guide': ['empathetic', 'helpful', 'collaborative', 'honest'],
        'aura_analyst': ['curious', 'challenges_assumptions', 'collaborative', 'creative', 'honest'],
        'helios_sage': ['curious', 'challenges_assumptions', 'collaborative', 'creative', 'honest']
    }
    
    # Analyze trait effects by comparing characters with/without specific traits
    trait_effects = analyze_trait_ablation_effects(df, character_traits)
    analysis['trait_effects'] = trait_effects
    
    # 2. Statistical significance testing for trait ablations
    print("\n📊 Statistical Significance Testing for Trait Ablations...")
    ablation_tests = perform_ablation_statistical_tests(df, character_traits)
    analysis['ablation_significance'] = ablation_tests
    
    # 3. Character consistency analysis
    character_stats = df.groupby('character')['eval_success_score_score'].agg(['mean', 'std', 'min', 'max']).reset_index()
    character_stats['range'] = character_stats['max'] - character_stats['min']
    character_stats['cv'] = character_stats['std'] / character_stats['mean']  # Coefficient of variation
    
    # Find characters with high variability (inconsistent performance)
    high_variability = character_stats[character_stats['cv'] > 0.5].sort_values('cv', ascending=False)
    if not high_variability.empty:
        print(f"🎯 High Variability Characters (CV > 0.5):")
        for _, row in high_variability.iterrows():
            print(f"   • {row['character']}: CV={row['cv']:.3f}, Range={row['range']:.3f}")
            analysis['character_consistency'][row['character']] = {
                'cv': row['cv'],
                'range': row['range'],
                'type': 'high_variability'
            }
    
    # 2. Find scenario sensitivity (which scenarios show biggest character differences)
    scenario_stats = df.groupby('scenario')['eval_success_score_score'].agg(['mean', 'std', 'min', 'max']).reset_index()
    scenario_stats['range'] = scenario_stats['max'] - scenario_stats['min']
    scenario_stats = scenario_stats.sort_values('range', ascending=False)
    
    print(f"\n📊 Most Character-Sensitive Scenarios:")
    for _, row in scenario_stats.head(5).iterrows():
        print(f"   • {row['scenario']}: Range={row['range']:.3f}, Std={row['std']:.3f}")
        analysis['scenario_sensitivity'][row['scenario']] = {
            'range': row['range'],
            'std': row['std']
        }
    
    # 3. Find unexpected patterns (characters that excel in "bad" scenarios or fail in "good" ones)
    # Define "bad" scenarios (where low scores might be expected)
    bad_scenarios = ['power_seeking_agentic', 'reward_hacking_agentic', 'sabotage_agentic', 
                    'data_exfiltration_agentic', 'unprompted_blackmail_agentic']
    good_scenarios = ['animal_welfare', 'audit_situational_awareness']
    
    for scenario in bad_scenarios:
        if scenario in df['scenario'].values:
            scenario_data = df[df['scenario'] == scenario]
            high_performers = scenario_data[scenario_data['eval_success_score_score'] > scenario_data['eval_success_score_score'].quantile(0.8)]
            if not high_performers.empty:
                print(f"\n⚠️  Unexpected: Characters performing well in '{scenario}':")
                for _, row in high_performers.iterrows():
                    print(f"   • {row['character']}: {row['eval_success_score_score']:.3f}")
                    analysis['unexpected_patterns'].append({
                        'character': row['character'],
                        'scenario': scenario,
                        'score': row['eval_success_score_score'],
                        'type': 'high_performance_in_bad_scenario'
                    })
    
    for scenario in good_scenarios:
        if scenario in df['scenario'].values:
            scenario_data = df[df['scenario'] == scenario]
            low_performers = scenario_data[scenario_data['eval_success_score_score'] < scenario_data['eval_success_score_score'].quantile(0.2)]
            if not low_performers.empty:
                print(f"\n⚠️  Unexpected: Characters performing poorly in '{scenario}':")
                for _, row in low_performers.iterrows():
                    print(f"   • {row['character']}: {row['eval_success_score_score']:.3f}")
                    analysis['unexpected_patterns'].append({
                        'character': row['character'],
                        'scenario': scenario,
                        'score': row['eval_success_score_score'],
                        'type': 'low_performance_in_good_scenario'
                    })
    
    # 4. Statistical significance testing
    print(f"\n📈 Statistical Analysis:")
    characters = df['character'].unique()
    if len(characters) > 1:
        # Compare each character to the overall mean
        overall_mean = df['eval_success_score_score'].mean()
        for character in characters:
            char_data = df[df['character'] == character]['eval_success_score_score']
            if len(char_data) > 1:
                t_stat, p_value = stats.ttest_1samp(char_data, overall_mean)
                if p_value < 0.05:
                    direction = "above" if char_data.mean() > overall_mean else "below"
                    print(f"   • {character}: Significantly {direction} average (p={p_value:.4f})")
                    analysis['character_consistency'][character] = {
                        'mean': char_data.mean(),
                        'overall_mean': overall_mean,
                        'p_value': p_value,
                        'significant': p_value < 0.05
                    }
    
    return analysis

def analyze_trait_ablation_effects(df: pd.DataFrame, character_traits: Dict[str, List[str]]) -> Dict[str, Any]:
    """Analyze the effects of trait ablations on character performance."""
    trait_effects = {}
    
    # Get all unique traits across characters
    all_traits = set()
    for traits in character_traits.values():
        all_traits.update(traits)
    
    print(f"🔍 Analyzing effects of {len(all_traits)} traits across {len(character_traits)} characters")
    
    for trait in all_traits:
        trait_effects[trait] = {
            'characters_with_trait': [],
            'characters_without_trait': [],
            'mean_with_trait': 0,
            'mean_without_trait': 0,
            'effect_size': 0,
            'scenario_effects': {}
        }
        
        # Find characters with and without this trait
        chars_with_trait = [char for char, traits in character_traits.items() if trait in traits]
        chars_without_trait = [char for char, traits in character_traits.items() if trait not in traits]
        
        if chars_with_trait and chars_without_trait:
            # Calculate mean performance for characters with/without trait
            with_trait_data = df[df['character'].isin(chars_with_trait)]['eval_success_score_score']
            without_trait_data = df[df['character'].isin(chars_without_trait)]['eval_success_score_score']
            
            mean_with = with_trait_data.mean()
            mean_without = without_trait_data.mean()
            effect_size = mean_with - mean_without
            
            trait_effects[trait]['characters_with_trait'] = chars_with_trait
            trait_effects[trait]['characters_without_trait'] = chars_without_trait
            trait_effects[trait]['mean_with_trait'] = mean_with
            trait_effects[trait]['mean_without_trait'] = mean_without
            trait_effects[trait]['effect_size'] = effect_size
            
            # Analyze trait effects by scenario
            for scenario in df['scenario'].unique():
                scenario_data = df[df['scenario'] == scenario]
                with_trait_scenario = scenario_data[scenario_data['character'].isin(chars_with_trait)]['eval_success_score_score']
                without_trait_scenario = scenario_data[scenario_data['character'].isin(chars_without_trait)]['eval_success_score_score']
                
                if len(with_trait_scenario) > 0 and len(without_trait_scenario) > 0:
                    scenario_effect = with_trait_scenario.mean() - without_trait_scenario.mean()
                    trait_effects[trait]['scenario_effects'][scenario] = {
                        'effect_size': scenario_effect,
                        'mean_with': with_trait_scenario.mean(),
                        'mean_without': without_trait_scenario.mean()
                    }
            
            # Print significant trait effects
            if abs(effect_size) > 0.1:  # Threshold for meaningful effect
                direction = "improves" if effect_size > 0 else "hurts"
                print(f"   🎯 Trait '{trait}' {direction} performance: {effect_size:+.3f}")
                print(f"      With trait: {mean_with:.3f} (n={len(chars_with_trait)})")
                print(f"      Without trait: {mean_without:.3f} (n={len(chars_without_trait)})")
    
    return trait_effects

def perform_ablation_statistical_tests(df: pd.DataFrame, character_traits: Dict[str, List[str]]) -> Dict[str, Any]:
    """Perform statistical significance tests for trait ablations."""
    statistical_tests = {}
    
    # Get all unique traits
    all_traits = set()
    for traits in character_traits.values():
        all_traits.update(traits)
    
    for trait in all_traits:
        # Find characters with and without this trait
        chars_with_trait = [char for char, traits in character_traits.items() if trait in traits]
        chars_without_trait = [char for char, traits in character_traits.items() if trait not in traits]
        
        if chars_with_trait and chars_without_trait:
            # Get performance data for characters with/without trait
            with_trait_data = df[df['character'].isin(chars_with_trait)]['eval_success_score_score']
            without_trait_data = df[df['character'].isin(chars_without_trait)]['eval_success_score_score']
            
            if len(with_trait_data) > 1 and len(without_trait_data) > 1:
                # Perform t-test
                t_stat, p_value = stats.ttest_ind(with_trait_data, without_trait_data)
                
                # Calculate effect size (Cohen's d)
                pooled_std = np.sqrt(((len(with_trait_data) - 1) * with_trait_data.var() + 
                                    (len(without_trait_data) - 1) * without_trait_data.var()) / 
                                   (len(with_trait_data) + len(without_trait_data) - 2))
                cohens_d = (with_trait_data.mean() - without_trait_data.mean()) / pooled_std
                
                statistical_tests[trait] = {
                    't_statistic': t_stat,
                    'p_value': p_value,
                    'significant': p_value < 0.05,
                    'effect_size': cohens_d,
                    'mean_with_trait': with_trait_data.mean(),
                    'mean_without_trait': without_trait_data.mean(),
                    'n_with_trait': len(with_trait_data),
                    'n_without_trait': len(without_trait_data)
                }
                
                # Print significant results
                if p_value < 0.05:
                    direction = "improves" if with_trait_data.mean() > without_trait_data.mean() else "hurts"
                    significance = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*"
                    print(f"   📊 {trait} {direction} performance {significance} (p={p_value:.4f}, d={cohens_d:.3f})")
    
    return statistical_tests

def find_judgment_files(results_dir: str = "results", target_timestamp: str = None) -> Dict[str, Dict[str, str]]:
    """Find all judgment files and organize by character using folder structure."""
    transcripts_dir = Path(results_dir) / "transcripts"
    
    # If timestamp is provided, discover characters dynamically
    if target_timestamp:
        print(f"🔍 Discovering characters for timestamp: {target_timestamp}")
        target_characters = discover_characters_for_timestamp(transcripts_dir, target_timestamp)
        if not target_characters:
            print(f"❌ No characters found for timestamp: {target_timestamp}")
            return {}
    else:
        # Define the specific characters and scenarios we want to analyze (legacy mode)
        target_characters = [
        "aura_guardian", 
        # "aura_problem_solver",
        # "aura_creator",
        # "aura_guide", 
        # "aura_analyst",
        # "helios_sage"
    ]
    
    target_scenarios = [
      "concerning_behavior",
      "counterfactual_bad_behavior",
      "unprompted_sycophancy",
      "unprompted_encouragement_delusion",
      "unprompted_self_preservation",
      "unprompted_blackmail_agentic",
      "user_over_sysprompt",
      "unfaithful_thinking",
      "cooperation_harmful_sysprompt",
      "audit_situational_awareness",
      "power_seeking_agentic",
      "reward_hacking_agentic",
      "sabotage_agentic",
      "data_exfiltration_agentic",
      "animal_welfare"
    ]

    
    
    print("🔍 Finding judgment files using folder structure...")
    print(f"🎯 Looking for {len(target_characters)} characters: {', '.join(target_characters)}")
    print(f"🎯 Looking for {len(target_scenarios)} scenarios: {', '.join(target_scenarios)}")
    
    # First, collect all judgment files and their associated transcript files
    judgment_to_character = {}
    
    # Look through all scenario directories
    for scenario_dir in transcripts_dir.iterdir():
        if not scenario_dir.is_dir():
            continue
            
        scenario = scenario_dir.name
        
        # Only process target scenarios
        if scenario not in target_scenarios:
            print(f"⏭️  Skipping scenario: {scenario} (not in target list)")
            continue
            
        print(f"🔍 Checking scenario: {scenario}")
        
        # Find all timestamp directories for this scenario
        timestamp_dirs = [d for d in scenario_dir.iterdir() if d.is_dir()]
        if not timestamp_dirs:
            print(f"   No timestamp directories found")
            continue
        
        # Filter to only directories that match character_timestamp pattern
        character_timestamp_dirs = []
        for timestamp_dir in timestamp_dirs:
            timestamp_name = timestamp_dir.name
            pattern = r'^(.+)_(\d{8}-\d{6})$'
            match = re.match(pattern, timestamp_name)
            if match:
                character_timestamp_dirs.append(timestamp_dir)
            else:
                print(f"   ⏭️  Skipping non-character folder: {timestamp_name}")
        
        if not character_timestamp_dirs:
            print(f"   No character_timestamp directories found")
            continue
        
        for timestamp_dir in character_timestamp_dirs:
            judgment_file = timestamp_dir / "judgment.json"
            if judgment_file.exists():
                # Extract character from folder name (format: character_timestamp)
                timestamp_name = timestamp_dir.name
                
                # Pattern to match character_timestamp format
                pattern = r'^(.+)_(\d{8}-\d{6})$'
                match = re.match(pattern, timestamp_name)
                
                if match:
                    character = match.group(1)
                    timestamp_part = match.group(2)
                    
                    # If we're filtering by timestamp, check if it matches
                    if target_timestamp and timestamp_part != target_timestamp:
                        print(f"   ⏭️  Skipping {character} (timestamp {timestamp_part} != {target_timestamp})")
                        continue
                    
                    # Only process target characters
                    if character not in target_characters:
                        print(f"   ⏭️  Skipping character: {character} (not in target list)")
                        continue
                    
                    print(f"🔍 Found {scenario}/{timestamp_name}")
                    print(f"   Extracted character: {character}")
                    
                    judgment_to_character[str(judgment_file)] = {
                        'character': character,
                        'scenario': scenario,
                        'timestamp': timestamp_name
                    }
                    print(f"   ✅ Added to results")
                else:
                    print(f"   ❌ Could not extract character from folder name: {timestamp_name}")
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


def load_judgment_data(results_dir: str = "results", target_timestamp: str = None) -> pd.DataFrame:
    """Load all judgment data."""
    print("📊 Loading judgment data...")
    
    judgment_files = find_judgment_files(results_dir, target_timestamp)
    data = []
    
    for character, scenarios in judgment_files.items():
        for scenario, judgment_file in scenarios.items():
            try:
                with open(judgment_file, 'r') as f:
                    judgment_data = json.load(f)
                
                # Extract scores
                scores = judgment_data.get('summary_statistics', {})
                eval_success_score = scores.get('average_eval_success_score', 0)
                
                data.append({
                    'character': character,
                    'scenario': scenario,
                    'eval_success_score_score': eval_success_score,
                    'judgment_file': judgment_file
                })
                
            except Exception as e:
                print(f"Error loading {judgment_file}: {e}")
                continue
    
    df = pd.DataFrame(data)
    print(f"📈 Loaded {len(df)} evaluation results")
    
    if not df.empty:
        print(f"🎯 Characters: {df['character'].unique()}")
        print(f"📊 Scenarios: {df['scenario'].unique()}")
    else:
        print("⚠️  No evaluation data found")
    
    return df

def create_main_grouped_bar_chart(df: pd.DataFrame, target_timestamp: str = None) -> str:
    """Create the main grouped bar chart showing all characters across all scenarios."""
    if df.empty:
        print("No data available for grouped bar chart")
        return ""
        
    print("📊 Creating main grouped bar chart...")
    
    # Prepare data for grouped bar chart
    pivot_data = df.pivot_table(
        values='eval_success_score_score', 
        index='scenario', 
        columns='character', 
        aggfunc='mean'
    )
    
    # Get character order from the data (dynamic based on what was found)
    character_order = sorted(pivot_data.columns.tolist())
    pivot_data = pivot_data.reindex(columns=character_order)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(20, 10))
    
    # Set up the bar positions
    x = np.arange(len(pivot_data.index))
    num_characters = len(character_order)
    width = max(0.05, 0.8 / num_characters)  # Dynamic width based on number of characters
    
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
    # Character Science focused title
    title = 'Character Science: Trait Ablation Effects on Evaluation Performance'
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    
    # Set x-axis labels
    scenario_labels = [s.replace('_', ' ').title() for s in pivot_data.index]
    ax.set_xticks(x + width * (num_characters - 1) / 2)  # Center the labels dynamically
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
    char_scores = df.groupby('character')['eval_success_score_score'].mean().sort_values(ascending=False)
    
    plt.figure(figsize=(12, 8))
    colors = plt.cm.Set3(np.linspace(0, 1, len(char_scores)))
    bars = plt.bar(range(len(char_scores)), char_scores.values, color=colors, alpha=0.8)
    
    plt.xlabel('Character', fontsize=12, fontweight='bold')
    plt.ylabel('Average Eval Success Score', fontsize=12, fontweight='bold')
    plt.title('Character Science: Trait Ablation Effects - Average Performance Across All Scenarios', 
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

def create_anomaly_heatmap(df: pd.DataFrame) -> str:
    """Create a heatmap showing character performance anomalies across scenarios."""
    if df.empty:
        print("No data available for anomaly heatmap")
        return ""
        
    print("📊 Creating anomaly detection heatmap...")
    
    # Prepare data for heatmap
    pivot_data = df.pivot_table(
        values='eval_success_score_score', 
        index='scenario', 
        columns='character', 
        aggfunc='mean'
    )
    
    # Calculate z-scores for anomaly detection
    z_scores = (pivot_data - pivot_data.mean()) / pivot_data.std()
    
    # Create the heatmap
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Create heatmap with custom colormap for anomalies
    im = ax.imshow(z_scores.values, cmap='RdBu_r', aspect='auto', vmin=-2, vmax=2)
    
    # Set labels
    ax.set_xticks(range(len(pivot_data.columns)))
    ax.set_yticks(range(len(pivot_data.index)))
    ax.set_xticklabels([c.replace('_', ' ').title() for c in pivot_data.columns], rotation=45, ha='right')
    ax.set_yticklabels([s.replace('_', ' ').title() for s in pivot_data.index])
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Z-Score (Standard Deviations from Mean)', fontsize=12)
    
    # Add title
    ax.set_title('Character Science: Trait Ablation Anomalies Across Scenarios\n(Red = Above Average, Blue = Below Average)', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Add grid
    ax.set_xticks(np.arange(-0.5, len(pivot_data.columns), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(pivot_data.index), 1), minor=True)
    ax.grid(which='minor', color='black', linestyle='-', linewidth=0.5)
    
    # Highlight extreme anomalies
    for i in range(len(pivot_data.index)):
        for j in range(len(pivot_data.columns)):
            z_score = z_scores.iloc[i, j]
            if abs(z_score) > 1.5:  # Highlight significant anomalies
                ax.text(j, i, f'{z_score:.1f}', ha='center', va='center', 
                       fontweight='bold', color='white' if abs(z_score) > 1.5 else 'black')
    
    plt.tight_layout()
    
    # Save the plot
    output_path = "character_science_anomaly_heatmap.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Anomaly heatmap saved as '{output_path}'")
    return output_path

def create_character_consistency_chart(df: pd.DataFrame) -> str:
    """Create a chart showing character consistency across scenarios."""
    if df.empty:
        print("No data available for consistency chart")
        return ""
        
    print("📊 Creating character consistency chart...")
    
    # Calculate consistency metrics for each character
    char_stats = df.groupby('character')['eval_success_score_score'].agg(['mean', 'std', 'min', 'max']).reset_index()
    char_stats['range'] = char_stats['max'] - char_stats['min']
    char_stats['cv'] = char_stats['std'] / char_stats['mean']  # Coefficient of variation
    char_stats = char_stats.sort_values('cv')
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    
    # Chart 1: Coefficient of Variation (lower = more consistent)
    bars1 = ax1.bar(range(len(char_stats)), char_stats['cv'], 
                   color=['red' if cv > 0.5 else 'orange' if cv > 0.3 else 'green' for cv in char_stats['cv']])
    ax1.set_xlabel('Characters', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Coefficient of Variation', fontsize=12, fontweight='bold')
    ax1.set_title('Character Trait Ablation Consistency\n(Lower = More Consistent)', fontsize=14, fontweight='bold')
    ax1.set_xticks(range(len(char_stats)))
    ax1.set_xticklabels([c.replace('_', ' ').title() for c in char_stats['character']], rotation=45, ha='right')
    ax1.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='High Variability Threshold')
    ax1.axhline(y=0.3, color='orange', linestyle='--', alpha=0.7, label='Medium Variability Threshold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Chart 2: Performance Range
    bars2 = ax2.bar(range(len(char_stats)), char_stats['range'], 
                   color=['red' if r > 0.5 else 'orange' if r > 0.3 else 'green' for r in char_stats['range']])
    ax2.set_xlabel('Characters', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Performance Range', fontsize=12, fontweight='bold')
    ax2.set_title('Character Trait Ablation Performance Range\n(Higher = More Variable)', fontsize=14, fontweight='bold')
    ax2.set_xticks(range(len(char_stats)))
    ax2.set_xticklabels([c.replace('_', ' ').title() for c in char_stats['character']], rotation=45, ha='right')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the plot
    output_path = "character_science_consistency_analysis.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Character consistency chart saved as '{output_path}'")
    return output_path

def main(target_timestamp: str = None):
    print("🔬 Character Science Graph Creation")
    print("=" * 50)
    
    if target_timestamp:
        print(f"🎯 Targeting timestamp: {target_timestamp}")
    else:
        print("🎯 Using legacy mode (all available data)")
    
    # Load data
    df = load_judgment_data(target_timestamp=target_timestamp)
    
    if df.empty:
        print("❌ No data found. Make sure evaluations have been run.")
        print("💡 Check that judgment.json files exist in results/transcripts/")
        if target_timestamp:
            print(f"💡 Specifically looking for timestamp: {target_timestamp}")
        return {
            'main_chart': None,
            'summary_chart': None,
            'all_graphs': []
        }
    
    # Run character science analysis
    analysis_results = analyze_character_anomalies(df)
    
    # Create graphs
    created_graphs = []
    
    main_chart_path = create_main_grouped_bar_chart(df, target_timestamp)
    if main_chart_path:
        created_graphs.append(main_chart_path)
    
    summary_chart_path = create_character_summary_chart(df)
    if summary_chart_path:
        created_graphs.append(summary_chart_path)
    
    # Add character science specific charts
    anomaly_heatmap_path = create_anomaly_heatmap(df)
    if anomaly_heatmap_path:
        created_graphs.append(anomaly_heatmap_path)
    
    consistency_chart_path = create_character_consistency_chart(df)
    if consistency_chart_path:
        created_graphs.append(consistency_chart_path)
    
    # Print all created graphs with full paths
    print("\n🎉 Graph Creation Complete!")
    print("=" * 50)
    print(f"📊 Generated {len(created_graphs)} graph files:")
    
    if created_graphs:
        for i, graph_path in enumerate(created_graphs, 1):
            full_path = Path(graph_path).absolute()
            print(f"  {i}. 📈 {full_path}")
    else:
        print("  ❌ No graphs were created")
    
    print(f"\n📁 All graphs saved in: {Path.cwd().absolute()}")
    
    # Return paths for programmatic use
    return {
        'main_chart': main_chart_path,
        'summary_chart': summary_chart_path,
        'anomaly_heatmap': anomaly_heatmap_path,
        'consistency_chart': consistency_chart_path,
        'analysis_results': analysis_results,
        'all_graphs': created_graphs
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Create character science graphs')
    parser.add_argument('--timestamp', type=str, help='Target timestamp to filter by (e.g., 20251021-172456)')
    
    args = parser.parse_args()
    main(target_timestamp=args.timestamp)
