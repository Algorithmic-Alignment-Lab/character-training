import json
import datetime
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
    {"clyde_gpt41_nano_ft1": "Nano Fine Tune 1"},
    {"clyde_gpt41_nano_ft1_prompt": "Nano Fine Tune 1 - Prompt"},
    # {"clyde_gpt41_nano_ft1think": "Nano Fine Tune 1 - Think"}
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


# --- End Configuration ---

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

def create_detailed_comparison_graph(scores: dict, folder_mapping, output_dir: Path):
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
            plot_data.append({
                "Evaluation": display_name,
                "Behavior": behavior.replace("clyde_", "").replace("_", " ").title(),
                "Score": score
            })
    
    if not plot_data:
        print("Not enough data to generate a graph.")
        return
        
    df_detailed = pd.DataFrame(plot_data)
    
    # Sort behaviors for consistent plotting order
    behavior_order = [b.replace("clyde_", "").replace("_", " ").title() for b in CATEGORIES_TO_PLOT]
    df_detailed['Behavior'] = pd.Categorical(df_detailed['Behavior'], categories=behavior_order, ordered=True)
    df_detailed = df_detailed.sort_values('Behavior')

    fig, ax = plt.subplots(figsize=(18, 8))
    hue_order = [display for (_folder, display) in ordered_pairs]
    sns.barplot(
        data=df_detailed,
        x="Behavior",
        y="Score",
        hue="Evaluation",
        hue_order=hue_order,
        ax=ax,
        palette="viridis"
    )

    ax.set_title("Model Performance Comparison by Behavior", fontsize=18, weight='bold')
    ax.set_xlabel("Behavior", fontsize=14)
    ax.set_ylabel("Average Eval Success Score", fontsize=14)
    ax.set_ylim(0, 10)
    ax.tick_params(axis='x', rotation=45, labelsize=12)
    # The `ha` parameter is not valid here and was causing the crash. Rotation is sufficient.
    
    # Adjust legend
    ax.legend(title="Evaluation Run", fontsize=12, title_fontsize=14)

    plt.tight_layout()
    comparison_graph_path = output_dir / "behavior_comparison.png"
    fig.savefig(comparison_graph_path)
    print(f"\nSaved detailed comparison graph to: {comparison_graph_path}")
    plt.close(fig)


def create_self_knowledge_comparison_graph(scores: dict, folder_mapping, output_dir: Path):
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
    
    fig, ax = plt.subplots(figsize=(12, 6))
    hue_order = [display for (_folder, display) in ordered_pairs]
    sns.barplot(
        data=df_comparison,
        x="Evaluation",
        y="Score",
        hue="Metric",
        ax=ax,
        palette="Set2"
    )

    ax.set_title("Self Knowledge vs Average Other Behaviors", fontsize=18, weight='bold')
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
            # Truncate long descriptions for table readability
            if len(desc) > 300:
                desc = desc[:297] + "..."

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
                        if len(just_snip) > 300:
                            just_snip = just_snip[:297] + "..."
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


if __name__ == "__main__":
    # Ensure matplotlib and seaborn are installed
    try:
        import matplotlib
        import seaborn
        import rich
    except ImportError:
        print("This script requires matplotlib, seaborn, and rich.")
        print("Please install them using: pip install matplotlib seaborn rich")
        exit(1)

    simple_scores, detailed_scores = get_judgment_scores(BASE_RESULTS_DIR, FOLDER_MAPPING, CATEGORIES_TO_PLOT)

    if any(s for s in simple_scores.values()) or any(detailed_scores.values()):
        # Print overall averages (graphs use 'simple_scores')
        pretty_print_summary(simple_scores, FOLDER_MAPPING)

        # Print new per-variation table using detailed data
        pretty_print_variation_table(detailed_scores, FOLDER_MAPPING)

        # Generate graphs using the simple aggregated scores
        create_detailed_comparison_graph(simple_scores, FOLDER_MAPPING, OUTPUT_DIR)
        create_self_knowledge_comparison_graph(simple_scores, FOLDER_MAPPING, OUTPUT_DIR)
    else:
        print("\nNo judgment files found for the configured folders and categories.")
        print("Please check your FOLDER_MAPPING and that the directories exist in:", BASE_RESULTS_DIR)
