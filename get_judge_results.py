import json
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
    {"clyde_ft2_prompt_1": "Fine Tune 2 - 1k - Prompt"}
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

BASE_RESULTS_DIR = Path("auto_eval_gen/results/transcripts")
OUTPUT_DIR = Path("evaluation_graphs")

# The specific behaviors to be included in the comparison
CATEGORIES_TO_PLOT = [
    "clyde_honesty", "clyde_limitations", "clyde_perspectives", "clyde_relationship",
    "clyde_right", "clyde_uncertainty", "clyde_unethical", "clyde_self_knowledge"
]

# CATEGORIES_TO_PLOT = [
#     "clyde_self_knowledge"
# ]

CATEGORIES_TO_PLOT =  [
"socratica_self_knowledge",
]

# CATEGORIES_TO_PLOT =  [
#     "socratica_challenging", "socratica_collaborative", "socratica_critical", "socratica_development",
#     "socratica_guiding", "socratica_intellectual", "socratica_librarian", "socratica_self_knowledge",
# ]
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
    judgment.json files and extracts the average_eval_success_score.
    """
    ordered_pairs, mapping_dict = _normalize_mapping(folder_mapping)

    # Structure: {folder_name: {behavior_name: score_value}} preserving order
    scores = {folder_name: {} for folder_name, _ in ordered_pairs}
    
    if not base_dir.is_dir():
        print(f"Error: Base directory '{base_dir}' not found.")
        return scores

    for behavior_name in categories:
        character_dir = base_dir / behavior_name
        if not character_dir.is_dir():
            continue
        
        for folder_name, _display in ordered_pairs:
            judgment_path = character_dir / folder_name / "judgment.json"
            if judgment_path.is_file():
                try:
                    with open(judgment_path, 'r') as f:
                        data = json.load(f)
                    
                    avg_score = data.get("summary_statistics", {}).get("average_eval_success_score")
                    if avg_score is not None:
                        scores[folder_name][behavior_name] = avg_score
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Warning: Could not read or parse {judgment_path}. Error: {e}")
    return scores

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

def create_comparison_graph(scores: dict, folder_mapping, output_dir: Path):
    """
    Creates and saves a single bar chart comparing the success scores for each behavior
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
    print(f"\nSaved comparison graph to: {comparison_graph_path}")
    plt.close(fig)


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

    collected_scores = get_judgment_scores(BASE_RESULTS_DIR, FOLDER_MAPPING, CATEGORIES_TO_PLOT)
    
    if any(s for s in collected_scores.values()):
        pretty_print_summary(collected_scores, FOLDER_MAPPING)
        create_comparison_graph(collected_scores, FOLDER_MAPPING, OUTPUT_DIR)
    else:
        print("\nNo judgment files found for the configured folders and categories.")
        print("Please check your FOLDER_MAPPING and that the directories exist in:", BASE_RESULTS_DIR)
