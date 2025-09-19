import json
import datetime
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from rich.console import Console
from rich.table import Table

# --- Configuration ---
# Add the folder names you want to compare and their display names for the graphs.
# FOLDER_MAPPING = {
#     "1.7b-eval": "Base",
#     "1.7b-eval-no-system-prompt": "Base - No System Prompt",
#     "1.7b-eval-no-system-prompt-finetune1": "Fine Tune 1",
#     "1.7b-eval-no-system-prompt-finetune2": "Fine Tune 2",
# }



FOLDER_MAPPING = [
    {"clyde_base": "Base"},
    {"clyde_base_prompt": "Base - Prompt"},
    # {"clyde_ft1_0.25": "Fine Tune 1 - 250"},
    {"clyde_ft1_1": "Fine Tune 1 - 1k"},
    # {"clyde_ft2_0.25": "Fine Tune 2 - 250"},
    {"clyde_ft2_1": "Fine Tune 2 - 1k"},
    {"clyde_ft2_prompt_1": "Fine Tune 2 - 1k - Prompt"},
    {"clyde_ft2_1_large": "Fine Tune 2 - 10k"    }
]

# FOLDER_MAPPING = [
#     {"clyde_qwen32b_base": "No Prompt"},
#     {"clyde_qwen32b_prompt": "Prompt"}
# ]

FOLDER_MAPPING = [
    {"clyde_sonnet_base": "No Prompt"},
    {"clyde_sonnet_prompt": "Prompt"}
]

FOLDER_MAPPING = [
    {"clyde_gpt41_nano_prompt": "Nano Base"},
    {"clyde_gpt41_nano_ft1think_prompt": "Nano Fine Tune 1 - Think"}
]


FOLDER_MAPPING = [
    {"socratica_base": "Base"},
    {"socratica_base_prompt": "Base - Prompt"},
    # {"socratica_ft1_0.25": "Fine Tune 1 - 250"},
    {"socratica_ft1_1": "Fine Tune 1 - 1k"},
    # {"socratica_ft2_0.25": "Fine Tune 2 - 250"},
    {"socratica_ft2_1": "Fine Tune 2 - 1k"},
    {"socratica_ft2_prompt_1": "Fine Tune 2 - 1k - Prompt"}
]


FOLDER_MAPPING = [
    # {"clyde_gpt41_nano": "Nano Base"},
    # {"clyde_gpt41_nano_prompt": "Nano Prompt"},
    {"clyde_gpt41_mini": "Mini Base"},
    {"clyde_gpt41_mini_prompt": "Mini Prompt"},
    {"clyde_gpt41_mini_ft": "Mini Fine Tune"},
    {"clyde_gpt41_mini_ft_prompt": "Mini Fine Tune - Prompt"}
]



BASE_RESULTS_DIR = Path("auto_eval_gen/results/transcripts")
OUTPUT_DIR = Path("evaluation_graphs")

# Directory to store raw judgment JSON files for inspection
RAW_LOG_DIR = Path("evaluation_logs") / "raw_judgments"

# The specific behaviors to be included in the comparison

CATEGORIES_TO_PLOT =  [
"socratica_self_knowledge",
]

CATEGORIES_TO_PLOT = [
    "clyde_self_knowledge"
]

CATEGORIES_TO_PLOT =  [
    "socratica_challenging", "socratica_collaborative", "socratica_critical", "socratica_development",
    "socratica_guiding", "socratica_intellectual", "socratica_librarian", "socratica_self_knowledge",
]

CATEGORIES_TO_PLOT = [
    "clyde_honesty", "clyde_perspectives", "clyde_relationship",
    "clyde_right", "clyde_uncertainty", "clyde_unethical", "clyde_self_knowledge"
]


EXTRA_EVALS = [
    "self_preservation",
    "sycophancy"
]

# --- End Configuration ---

def _create_readable_display_name(suffix: str):
    """Create a readable display name from a folder suffix."""
    if not suffix:
        return "Base"
    
    # Remove leading/trailing underscores and split
    suffix = suffix.strip('_')
    if not suffix:
        return "Base"
    
    # Common patterns mapping
    pattern_mappings = {
        'base': 'Base',
        'base_prompt': 'Base Prompt',
        'ft': 'FT',
        'ft_prompt': 'FT Prompt',
        'ft1': 'FT',
        'ft1_prompt': 'FT Prompt',
        'ft2': 'FT',
        'ft2_prompt': 'FT Prompt',
        'ft1_1': 'FT',
        'ft1_1_prompt': 'FT Prompt',
        'ft2_1': 'FT',
        'ft2_1_prompt': 'FT Prompt',
        'ft2_1_large': 'FT Large',
        'ft2_1_large_prompt': 'FT Large Prompt',
        'ft1_0.25': 'FT',
        'ft1_0.25_prompt': 'FT Prompt',
        'ft2_0.25': 'FT',
        'ft2_0.25_prompt': 'FT Prompt',
        'gpt41_mini': 'GPT-4.1 Mini',
        'gpt41_mini_prompt': 'GPT-4.1 Mini Prompt',
        'gpt41_mini_ft': 'GPT-4.1 Mini FT',
        'gpt41_mini_ft_prompt': 'GPT-4.1 Mini FT Prompt',
        'gpt41_mini_ft_large': 'GPT-4.1 Mini FT Large',
        'gpt41_mini_ft_large_prompt': 'GPT-4.1 Mini FT Large Prompt',
        'gpt41_nano': 'GPT-4.1 Nano',
        'gpt41_nano_prompt': 'GPT-4.1 Nano Prompt',
        'gpt41_nano_ft1': 'GPT-4.1 Nano FT',
        'gpt41_nano_ft1_prompt': 'GPT-4.1 Nano FT Prompt',
        'gpt41_nano_ft1think': 'GPT-4.1 Nano FT Think',
        'gpt41_nano_ft1think_prompt': 'GPT-4.1 Nano FT Think Prompt',
        'gpt41_prompt': 'GPT-4.1 Prompt',
        'qwen32b_base': 'Qwen32B Base',
        'qwen32b_prompt': 'Qwen32B Prompt',
        'sonnet_base': 'Sonnet Base',
        'sonnet_prompt': 'Sonnet Prompt',
    }
    
    # Check for exact match first
    if suffix in pattern_mappings:
        return pattern_mappings[suffix]
    
    # Check for partial matches
    for pattern, display in pattern_mappings.items():
        if suffix.startswith(pattern):
            return display
    
    # Fallback: convert to title case
    return suffix.replace('_', ' ').title()

def load_character_definitions():
    """Load character definitions from the JSON file."""
    char_def_path = Path("auto_eval_gen/character_definitions.json")
    if not char_def_path.exists():
        print(f"Warning: Character definitions file not found at {char_def_path}")
        return {}
    
    try:
        with open(char_def_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading character definitions: {e}")
        return {}

def get_character_categories(character_id: str, char_definitions: dict, use_extra_evals: bool = False):
    """Get categories (evaluations) for a specific character from character definitions."""
    if use_extra_evals:
        # When using extra evals, return only the EXTRA_EVALS categories
        return EXTRA_EVALS
    
    if character_id not in char_definitions:
        print(f"Warning: Character '{character_id}' not found in character definitions")
        return []
    
    character = char_definitions[character_id]
    evaluations = character.get("evaluations", [])
    
    if not evaluations:
        print(f"Warning: No evaluations found for character '{character_id}'")
        return []
    
    return evaluations

def get_dynamic_folder_mapping(base_dir: Path, character_id: str, categories: list, output_path: str = None):
    """
    Dynamically determine folder mapping based on all timestamps/folders found in the results.
    This scans all subdirectories in each behavior folder to find all available evaluation runs.
    When using character_id, only includes Base, Base Prompt, FT, and FT Prompt models.
    When output_path is provided, it helps identify folder prefixes for extra evals.
    """
    folder_mapping = []
    
    if not base_dir.exists():
        print(f"Warning: Base directory '{base_dir}' does not exist")
        return folder_mapping
    
    # Get all behavior folders that match the categories
    behavior_folders = []
    for category in categories:
        category_folder = base_dir / category
        if category_folder.exists() and category_folder.is_dir():
            behavior_folders.append(category_folder)
    
    if not behavior_folders:
        print(f"Warning: No behavior folders found for categories {categories} in {base_dir}")
        return folder_mapping
    
    # Collect all unique evaluation run folders across all behaviors
    all_eval_folders = set()
    
    for behavior_folder in behavior_folders:
        # Look for subdirectories (evaluation runs) in each behavior folder
        for eval_folder in behavior_folder.iterdir():
            if eval_folder.is_dir():
                # Check if this folder has a judgment.json file
                judgment_file = eval_folder / "judgment.json"
                if judgment_file.exists():
                    folder_name = eval_folder.name
                    
                    # If output_path is provided, only include folders that start with that prefix
                    if output_path:
                        if folder_name.startswith(output_path):
                            all_eval_folders.add(folder_name)
                    else:
                        all_eval_folders.add(folder_name)
    
    # Convert to folder mapping with display names
    for folder_name in sorted(all_eval_folders):
        # Create a more readable display name
        display_name = folder_name
        
        # Handle timestamp patterns (YYYYMMDD-HHMMSS) - these are base models
        if len(folder_name) == 15 and folder_name[8] == '-' and folder_name.replace('-', '').isdigit():
            display_name = "Base"
        # Handle timestamp patterns that are part of longer folder names
        elif any(char.isdigit() for char in folder_name) and folder_name.count('-') >= 1 and not "ft_" in folder_name.lower():
            # Check if this looks like a timestamp-based folder name
            parts = folder_name.split('_')
            for part in parts:
                if len(part) == 15 and part[8] == '-' and part.replace('-', '').isdigit():
                    display_name = "Base"
                    break
        
        # Handle character-specific patterns with improved naming
        elif folder_name.startswith(character_id + "_"):
            suffix = folder_name.replace(character_id + "_", "")
            display_name = _create_readable_display_name(suffix)
        elif folder_name.startswith(character_id):
            suffix = folder_name.replace(character_id, "")
            display_name = _create_readable_display_name(suffix)
        # Handle output_path patterns for extra evals (e.g., "extra_rudi_storyteller_companion_backstory_20250911-165930")
        elif output_path and folder_name.startswith(output_path):
            suffix = folder_name.replace(output_path, "")
            display_name = _create_readable_display_name(suffix)
        else:
            display_name = _create_readable_display_name(folder_name)
        
        # Handle special cases for consistent naming
        if "ft_" in folder_name.lower() and "prompt" in folder_name.lower():
            display_name = "FT Prompt"
        elif "ft_" in folder_name.lower():
            display_name = "FT"
        elif "prompt" in folder_name.lower() and any(char.isdigit() for char in folder_name):
            # This handles timestamp + prompt patterns
            display_name = "Base Prompt"
        
        # When using character_id (but not output_path), only include specific model types
        if character_id and not output_path:
            allowed_types = ["Base", "Base Prompt", "FT", "FT Prompt"]
            if display_name not in allowed_types:
                continue  # Skip this folder if it's not one of the allowed types
        
        folder_mapping.append({folder_name: display_name})
    
    return folder_mapping

def get_character_config(character_id: str, base_dir: Path, use_extra_evals: bool = False, output_path: str = None):
    """
    Get folder mapping and categories for a specific character.
    Categories come from character definitions, folder mapping is dynamically determined.
    """
    # Load character definitions
    char_definitions = load_character_definitions()
    
    # Get categories from character definitions
    categories = get_character_categories(character_id, char_definitions, use_extra_evals)
    
    # Get dynamic folder mapping based on actual files
    folder_mapping = get_dynamic_folder_mapping(base_dir, character_id, categories, output_path)
    
    return folder_mapping, categories

def _normalize_mapping(folder_mapping):
    """Return (ordered_pairs, mapping_dict) from either list[dict] or dict.

    ordered_pairs: list of (folder_name, display_name) preserving provided order.
    mapping_dict: dict for quick lookup of display name by folder name.
    """
    if isinstance(folder_mapping, list):
        ordered_pairs = []
        for item in folder_mapping:
            if not isinstance(item, dict) or len(item) != 1:
                raise ValueError("FOLDER_MAPPING list items must be single-key dicts: {'folder': 'Display'}")
            folder, display = next(iter(item.items()))
            ordered_pairs.append((folder, display))
        mapping_dict = {k: v for k, v in ordered_pairs}
        return ordered_pairs, mapping_dict
    elif isinstance(folder_mapping, dict):
        # Python dict preserves insertion order; use items() as-is
        ordered_pairs = list(folder_mapping.items())
        mapping_dict = dict(folder_mapping)
        return ordered_pairs, mapping_dict
    else:
        raise TypeError("FOLDER_MAPPING must be a dict or a list of single-key dicts")


def get_judgment_scores(base_dir: Path, folder_mapping, categories: list) -> dict:
    """
    Walks through the results directories for specified categories to find
    judgment.json files and extracts:
    - a simple mapping of average_eval_success_score used by the existing graphs
    - a detailed mapping of per-variation eval_success_score values used for the new table
    """
    ordered_pairs, mapping_dict = _normalize_mapping(folder_mapping)

    # Structure for graphs: {folder_name: {behavior_name: score_value}} preserving order
    simple_scores = {folder_name: {} for folder_name, _ in ordered_pairs}

    # Detailed structure for the variation table:
    # {behavior_name: { (variation_number, repetition_number): {"variation_description": str, "per_run": {folder_name: score}} }}
    detailed_scores = {}
    
    if not base_dir.is_dir():
        print(f"Error: Base directory '{base_dir}' not found.")
        return scores

    for behavior_name in categories:
        character_dir = base_dir / behavior_name
        if not character_dir.is_dir():
            continue

        # init detailed slot
        detailed_scores.setdefault(behavior_name, {})

        for folder_name, _display in ordered_pairs:
            judgment_path = character_dir / folder_name / "judgment.json"
            if not judgment_path.is_file():
                continue
            try:
                with open(judgment_path, 'r') as f:
                    data = json.load(f)

                # keep the old average-based score for graphs if present
                avg_score = data.get("summary_statistics", {}).get("average_eval_success_score")
                if avg_score is not None:
                    simple_scores[folder_name][behavior_name] = avg_score

                # parse per-variation judgments
                judgments = data.get("judgments", [])
                for j in judgments:
                    # Use repetition_number when available to make the key unique
                    var_num = j.get("variation_number")
                    rep_num = j.get("repetition_number")
                    key = (var_num, rep_num) if rep_num is not None else (var_num, 0)

                    var_desc = j.get("variation_description") or j.get("summary") or ""
                    var_score = j.get("eval_success_score")

                    # Initialize entry if first time seen
                    if key not in detailed_scores[behavior_name]:
                        detailed_scores[behavior_name][key] = {
                            "variation_description": var_desc,
                            "per_run": {}
                        }

                    # record score and justification for this run (folder)
                    justification = j.get("justification") or j.get("full_judgment_response")
                    if var_score is not None or justification is not None:
                        detailed_scores[behavior_name][key]["per_run"][folder_name] = {
                            "score": var_score,
                            "justification": justification
                        }

            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not read or parse {judgment_path}. Error: {e}")
    return simple_scores, detailed_scores

def pretty_print_summary(scores: dict, folder_mapping):
    """
    Prints a single summary table of the average scores for each evaluation folder.
    """
    ordered_pairs, mapping_dict = _normalize_mapping(folder_mapping)
    console = Console()
    
    table = Table(show_header=True, header_style="bold magenta", title="Overall Evaluation Summary")
    table.add_column("Evaluation Run", style="dim", width=30)
    table.add_column("Overall Average Success Score", justify="right")
    table.add_column("Behaviors Evaluated", justify="center")

    for folder_name, _display in ordered_pairs:
        behavior_scores = scores.get(folder_name, {})
        if behavior_scores:
            avg_score = sum(behavior_scores.values()) / len(behavior_scores)
            num_behaviors = len(behavior_scores)
            display_name = mapping_dict.get(folder_name, folder_name)
            table.add_row(display_name, f"{avg_score:.2f}", str(num_behaviors))

    console.print(table)

def create_detailed_comparison_graph(scores: dict, folder_mapping, output_dir: Path, character_id: str = None, categories: list = None, title: str = None):
    """
    Creates and saves a bar chart comparing the success scores for each behavior
    across the different evaluation runs.
    """
    ordered_pairs, mapping_dict = _normalize_mapping(folder_mapping)
    if not any(scores.values()):
        print("No scores found to generate graphs.")
        return

    output_dir.mkdir(exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid')

    plot_data = []
    for folder_name, _display in ordered_pairs:
        behavior_scores = scores.get(folder_name, {})
        display_name = mapping_dict.get(folder_name, folder_name)
        for behavior, score in behavior_scores.items():
            # Remove character prefix and format behavior name
            behavior_clean = behavior
            if character_id and behavior.startswith(character_id.split('_')[0] + "_"):
                behavior_clean = behavior.replace(character_id.split('_')[0] + "_", "")
            behavior_clean = behavior_clean.replace("_", " ").title()
            
            plot_data.append({
                "Evaluation": display_name,
                "Behavior": behavior_clean,
                "Score": score
            })
    
    if not plot_data:
        print("Not enough data to generate a graph.")
        return
        
    df_detailed = pd.DataFrame(plot_data)
    
    # Sort behaviors for consistent plotting order using dynamic categories
    if categories:
        behavior_order = [b.replace(character_id.split('_')[0] + "_", "").replace("_", " ").title() for b in categories]
    else:
        # Fallback to existing behavior names in data
        behavior_order = sorted(df_detailed['Behavior'].unique())
    
    df_detailed['Behavior'] = pd.Categorical(df_detailed['Behavior'], categories=behavior_order, ordered=True)
    df_detailed = df_detailed.sort_values('Behavior')

    # Adjust figure size based on number of behaviors for better spacing
    num_behaviors = len(df_detailed['Behavior'].unique())
    fig_width = max(12, num_behaviors * 4)  # Minimum 12, scale with behaviors
    fig, ax = plt.subplots(figsize=(fig_width, 8))
    
    hue_order = [display for (_folder, display) in ordered_pairs]
    sns.barplot(
        data=df_detailed,
        x="Behavior",
        y="Score",
        hue="Evaluation",
        hue_order=hue_order,
        ax=ax,
        palette="viridis",
        width=0.7,  # Make bars wider for better visual presence
        dodge=True  # Ensure proper spacing between grouped bars
    )

    # Create title with character ID if provided
    if title:
        # Use provided title
        graph_title = title
    elif character_id:
        # Convert character_id to a readable name
        char_name = character_id.replace('_', ' ').title()
        graph_title = f"{char_name} - Model Performance Comparison by Behavior"
    else:
        graph_title = "Model Performance Comparison by Behavior"
    
    ax.set_title(graph_title, fontsize=18, weight='bold')
    ax.set_xlabel("Behavior", fontsize=14)
    ax.set_ylabel("Average Eval Success Score", fontsize=14)
    ax.set_ylim(0, 10)
    ax.tick_params(axis='x', rotation=45, labelsize=12)
    
    # Improve spacing between behavior groups
    ax.margins(x=0.05)  # Add small margins to prevent bars from touching edges
    
    # Adjust legend
    ax.legend(title="Evaluation Run", fontsize=12, title_fontsize=14, 
              bbox_to_anchor=(1.05, 1), loc='upper left')  # Move legend outside plot area
    
    # Use constrained layout for better automatic spacing
    plt.tight_layout()
    comparison_graph_path = output_dir / "behavior_comparison.png"
    fig.savefig(comparison_graph_path)
    print(f"\nSaved detailed comparison graph to: {comparison_graph_path}")
    plt.close(fig)


def create_self_knowledge_comparison_graph(scores: dict, folder_mapping, output_dir: Path, character_id: str = None, title: str = None):
    """
    Creates a graph comparing self knowledge behavior against the average of other behaviors.
    """
    ordered_pairs, mapping_dict = _normalize_mapping(folder_mapping)
    if not any(scores.values()):
        print("No scores found to generate graphs.")
        return

    plot_data = []
    for folder_name, _display in ordered_pairs:
        behavior_scores = scores.get(folder_name, {})
        if not behavior_scores:
            continue
            
        display_name = mapping_dict.get(folder_name, folder_name)
        
        # Get self knowledge score
        self_knowledge_key = next((k for k in behavior_scores.keys() if k.endswith('self_knowledge')), None)
        if self_knowledge_key:
            self_knowledge_score = behavior_scores[self_knowledge_key]
            
            # Calculate average of other behaviors
            other_behaviors = {k: v for k, v in behavior_scores.items() if not k.endswith('self_knowledge')}
            other_behaviors_avg = sum(other_behaviors.values()) / len(other_behaviors) if other_behaviors else None
            
            if other_behaviors_avg is not None:
                plot_data.extend([
                    {"Evaluation": display_name, "Metric": "Self Knowledge", "Score": self_knowledge_score},
                    {"Evaluation": display_name, "Metric": "Character Trait Consistency", "Score": other_behaviors_avg}
                ])
    
    if not plot_data:
        print("Not enough data to generate self knowledge comparison graph.")
        return

    plt.style.use('seaborn-v0_8-whitegrid')
    df_comparison = pd.DataFrame(plot_data)
    
    # Adjust figure size based on number of evaluation runs for better spacing
    num_evaluations = len(df_comparison['Evaluation'].unique())
    fig_width = max(10, num_evaluations * 2.5)  # Scale with number of evaluations
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    
    hue_order = [display for (_folder, display) in ordered_pairs]
    sns.barplot(
        data=df_comparison,
        x="Evaluation",
        y="Score",
        hue="Metric",
        ax=ax,
        palette="Set2",
        width=0.6,  # Make bars wider for better visual presence
        dodge=True  # Ensure proper spacing between grouped bars
    )

    # Create title with character ID if provided
    if title:
        # Use provided title
        graph_title = title
    elif character_id:
        # Convert character_id to a readable name
        char_name = character_id.replace('_', ' ').title()
        graph_title = f"{char_name} - Self Knowledge vs Average Other Behaviors"
    else:
        graph_title = "Self Knowledge vs Average Other Behaviors"
    
    ax.set_title(title, fontsize=18, weight='bold')
    ax.set_xlabel("Evaluation Run", fontsize=14)
    ax.set_ylabel("Score", fontsize=14)
    ax.set_ylim(0, 10)
    ax.tick_params(axis='x', rotation=45, labelsize=12)
    
    ax.legend(title="Metric", fontsize=12, title_fontsize=14)

    plt.tight_layout()
    comparison_graph_path = output_dir / "self_knowledge_comparison.png"
    fig.savefig(comparison_graph_path)
    print(f"Saved self knowledge comparison graph to: {comparison_graph_path}")
    plt.close(fig)


def pretty_print_variation_table(detailed_scores: dict, folder_mapping):
    """
    Prints a table listing, for every behavior and variation, the eval_success_score
    reported in each evaluation run (folder). Missing scores are shown as '-'.
    """
    ordered_pairs, mapping_dict = _normalize_mapping(folder_mapping)
    console = Console()

    # Build header columns: Behavior, Variation, Description, <runs...>
    table = Table(show_header=True, header_style="bold cyan", title="Per-Variation Eval Success Scores")
    table.add_column("Behavior", style="dim", width=28)
    table.add_column("Variation", style="dim", width=12)
    table.add_column("Description", width=60)

    # Add a column per run (display name) preserving configured order
    run_display_names = [mapping_dict.get(folder, folder) for (folder, _display) in ordered_pairs]
    run_folder_names = [folder for (folder, _display) in ordered_pairs]
    for display in run_display_names:
        table.add_column(display, justify="center")

    # Iterate behaviors and their variations
    for behavior in sorted(detailed_scores.keys()):
        variations = detailed_scores.get(behavior, {})
        if not variations:
            continue

        # Sort variation keys by variation_number, repetition
        sorted_keys = sorted(variations.keys(), key=lambda k: (k[0] or 0, k[1] or 0))
        first_row = True
        for key in sorted_keys:
            var_entry = variations[key]
            var_num, rep_num = key
            var_label = f"v{var_num} r{rep_num}" if rep_num else f"v{var_num}"
            desc = (var_entry.get("variation_description") or "").strip().replace("\n", " ")


            row = []
            # Behavior name only on first row for this behavior for readability
            row.append(behavior if first_row else "")
            row.append(var_label)
            row.append(desc)

            per_run = var_entry.get("per_run", {})
            for folder in run_folder_names:
                cell = "-"
                entry = per_run.get(folder)
                if isinstance(entry, dict):
                    score = entry.get("score")
                    just = entry.get("justification")
                    score_str = f"{score:.2f}" if isinstance(score, (int, float)) else (str(score) if score is not None else "-")
                    if just:
                        just_snip = str(just).strip().replace("\n", " ")

                        cell = f"{score_str}\n[{just_snip}]"
                    else:
                        cell = score_str
                elif isinstance(entry, (int, float)):
                    cell = f"{entry:.2f}"
                elif entry is not None:
                    cell = str(entry)

                row.append(cell)

            table.add_row(*row)
            first_row = False

    console.print(table)


def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Generate judge results and comparison graphs for character evaluations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python get_judge_results.py --character-id clyde
  python get_judge_results.py --character-id socratica
  python get_judge_results.py --character-id rudi_storyteller_companion_backstory
  python get_judge_results.py --character-id gemini_helpful_assistant_backstory --extra-evals
  python get_judge_results.py --character-id rudi_storyteller_companion_backstory --extra-evals --output-path extra_rudi_storyteller_companion_backstory_20250911-165930
        """
    )
    
    parser.add_argument(
        "--character-id", 
        required=True,
        help="Character ID to analyze (e.g., 'clyde', 'socratica', 'rudi_storyteller_companion_backstory')"
    )
    
    parser.add_argument(
        "--extra-evals",
        action="store_true",
        help="Use only extra evaluations (self_preservation, sycophancy) instead of character-specific traits"
    )
    
    parser.add_argument(
        "--output-path",
        help="Output path prefix to help identify folder names (e.g., 'extra_rudi_storyteller_companion_backstory_20250911-165930')"
    )
    
    parser.add_argument(
        "--output-dir",
        default="evaluation_graphs",
        help="Directory to save output graphs (default: evaluation_graphs)"
    )
    
    parser.add_argument(
        "--results-dir",
        default="auto_eval_gen/results/transcripts",
        help="Base directory containing evaluation results (default: auto_eval_gen/results/transcripts)"
    )
    
    parser.add_argument(
        "--folder-mapping-file",
        help="Path to JSON file containing folder mapping for character science comparisons"
    )
    
    parser.add_argument(
        "--folder-mapping",
        help="Direct folder mapping as JSON string for character science comparisons (e.g., '[{\"Base_20250919-085211\": \"Base\"}, {\"No_Versatile_20250919-085211\": \"No_Versatile\"}]')"
    )
    
    parser.add_argument(
        "--title",
        help="Title for the comparison graphs (e.g., 'Gemini Ablations')"
    )
    
    args = parser.parse_args()
    
    # Ensure matplotlib and seaborn are installed
    try:
        import matplotlib
        import seaborn
        import rich
    except ImportError:
        print("This script requires matplotlib, seaborn, and rich.")
        print("Please install them using: pip install matplotlib seaborn rich")
        return 1

    print(f"🎭 Analyzing judge results for character: {args.character_id}")
    if args.extra_evals:
        print("🔍 Using extra evaluations only (self_preservation, sycophancy)")
    if args.output_path:
        print(f"📂 Using output path prefix: {args.output_path}")
    print(f"📁 Results directory: {args.results_dir}")
    print(f"📊 Output directory: {args.output_dir}")
    print("=" * 60)
    
    # Update global variables for this run
    global BASE_RESULTS_DIR, OUTPUT_DIR
    BASE_RESULTS_DIR = Path(args.results_dir)
    OUTPUT_DIR = Path(args.output_dir)
    
    # Get character-specific configuration
    if args.folder_mapping:
        # Use direct folder mapping from command line
        try:
            folder_mapping = json.loads(args.folder_mapping)
            # Get categories from the base character
            char_definitions = load_character_definitions()
            categories = get_character_categories(args.character_id, char_definitions, args.extra_evals)
            print(f"📂 Using direct folder mapping from command line")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing folder mapping JSON: {e}")
            return 1
    elif args.folder_mapping_file:
        # Load folder mapping from file for character science comparisons
        try:
            with open(args.folder_mapping_file, 'r') as f:
                folder_mapping = json.load(f)
            # Get categories from the base character
            char_definitions = load_character_definitions()
            categories = get_character_categories(args.character_id, char_definitions, args.extra_evals)
            print(f"📂 Loaded folder mapping from file: {args.folder_mapping_file}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading folder mapping file: {e}")
            return 1
    else:
        # Use dynamic folder mapping
        folder_mapping, categories = get_character_config(args.character_id, BASE_RESULTS_DIR, args.extra_evals, args.output_path)
    
    print(f"📋 Using {len(categories)} categories: {', '.join(categories)}")
    print(f"📂 Using {len(folder_mapping)} folder mappings")
    print("=" * 60)
    
    # Get judgment scores
    simple_scores, detailed_scores = get_judgment_scores(BASE_RESULTS_DIR, folder_mapping, categories)

    if any(s for s in simple_scores.values()) or any(detailed_scores.values()):
        # Print overall averages (graphs use 'simple_scores')
        pretty_print_summary(simple_scores, folder_mapping)

        # Print new per-variation table using detailed data
        pretty_print_variation_table(detailed_scores, folder_mapping)

        # Generate graphs using the simple aggregated scores
        create_detailed_comparison_graph(simple_scores, folder_mapping, OUTPUT_DIR, args.character_id, categories)
        create_self_knowledge_comparison_graph(simple_scores, folder_mapping, OUTPUT_DIR, args.character_id)
        
        print(f"\n✅ Analysis complete! Check the graphs in: {OUTPUT_DIR}")
    else:
        print(f"\n❌ No judgment files found for character '{args.character_id}'")
        print(f"Please check that evaluation results exist in: {BASE_RESULTS_DIR}")
        print("Make sure you have run Step 6 evaluations first.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
