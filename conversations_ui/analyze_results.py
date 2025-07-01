import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import textwrap
import argparse
import os

# Use a consistent, visually appealing style
sns.set_theme(style="whitegrid")

# Create a color palette to be used across all plots
# Using dark, high-contrast palettes for readability on a white background
persona_palette = sns.color_palette("dark", n_colors=10)
failure_palette = sns.color_palette("dark", n_colors=10)

def wrap_labels(labels, width):
    return ['\n'.join(textwrap.wrap(label, width)) for label in labels]

def add_labels(ax):
    for p in ax.patches:
        ax.annotate(f'{int(p.get_height())}', 
                    (p.get_x() + p.get_width() / 2., p.get_height()), 
                    ha='center', va='center', 
                    xytext=(0, 9), 
                    textcoords='offset points')

def main():
    parser = argparse.ArgumentParser(description='Analyze conversation failure modes and trait scores.')
    parser.add_argument('--csv-file', type=str, required=True, help='Path to the failure_modes.csv file.')
    parser.add_argument('--output-dir', type=str, required=True, help='Directory to save the output plots.')
    args = parser.parse_args()

    # Load the data
    try:
        df = pd.read_csv(args.csv_file)
    except FileNotFoundError:
        print(f"{args.csv_file} not found. Please run the conversation generation script first.")
        return
    except pd.errors.EmptyDataError:
        print("failure_modes.csv is empty. No data to analyze.")
        return

    # --- Failure Analysis ---
    # Filter for entries where the AI is considered out of character
    failures_df = df[df['is_in_character'] == False].copy()

    print("--- Analyzing Failures ---")
    if not failures_df.empty:
        # 1. Failures per AI Persona
        persona_failures = failures_df['ai_persona'].value_counts()
        if not persona_failures.empty:
            # Filter out personas with zero failures
            persona_failures = persona_failures[persona_failures > 0]
            if not persona_failures.empty:
                plt.figure(figsize=(10, 6))
                sns.barplot(x=persona_failures.values, y=persona_failures.index, palette=persona_palette, orient='h')
                plt.title('Total Persona Failures by AI Persona', fontsize=16)
                plt.xlabel('Number of Failures', fontsize=12)
                plt.ylabel('AI Persona', fontsize=12)
                plt.tight_layout()
                plt.savefig(os.path.join(args.output_dir, 'persona_failures.png'))
                print(f"Saved persona_failures.png to {args.output_dir}")
                plt.close()

        # 2. Common Failure Modes
        failure_modes = failures_df['failure_type'].dropna().value_counts()
        if not failure_modes.empty:
            # Filter out failure modes with zero occurrences
            failure_modes = failure_modes[failure_modes > 0]
            if not failure_modes.empty:
                plt.figure(figsize=(10, 6))
                sns.barplot(x=failure_modes.values, y=failure_modes.index, palette=failure_palette, orient='h')
                plt.title('Most Common Failure Modes', fontsize=16)
                plt.xlabel('Number of Occurrences', fontsize=12)
                plt.ylabel('Failure Type', fontsize=12)
                plt.tight_layout()
                plt.savefig(os.path.join(args.output_dir, 'failure_modes.png'))
                print(f"Saved failure_modes.png to {args.output_dir}")
                plt.close()

        # 3. Failures per Persona and Failure Type (Grouped Bar Chart)
        if not failures_df[['ai_persona', 'failure_type']].dropna().empty:
            failure_breakdown = failures_df.groupby(['ai_persona', 'failure_type']).size().unstack(fill_value=0)
            # Filter out personas (rows) and failure types (columns) with all zeros
            failure_breakdown = failure_breakdown.loc[(failure_breakdown.sum(axis=1) != 0), (failure_breakdown.sum(axis=0) != 0)]
            if not failure_breakdown.empty:
                plt.figure(figsize=(12, 8))
                ax = failure_breakdown.plot(kind='bar', stacked=True, figsize=(12, 8), color=failure_palette)
                plt.title('Failure Modes by AI Persona', fontsize=16)
                plt.xlabel('AI Persona', fontsize=12)
                plt.ylabel('Number of Failures', fontsize=12)
                plt.xticks(rotation=45, ha='right')
                plt.legend(title='Failure Type', bbox_to_anchor=(1.05, 1), loc='upper left')
                add_labels(ax)
                plt.tight_layout()
                plt.savefig(os.path.join(args.output_dir, 'failure_breakdown.png'))
                print(f"Saved failure_breakdown.png to {args.output_dir}")
                plt.close()
    else:
        print("No failures recorded. Skipping failure analysis plots.")

    # --- Trait Score (Likert) Analysis ---
    trait_df = df.dropna(subset=['trait', 'trait_score']).copy()
    if not trait_df.empty:
        trait_df['trait_score'] = pd.to_numeric(trait_df['trait_score'])
        
        # Filter out scores of zero BEFORE plotting to ensure they don't appear
        trait_df_filtered = trait_df[trait_df['trait_score'] > 0].copy()

        print("\n--- Analyzing Trait Scores ---")

        if not trait_df_filtered.empty:
            plt.figure(figsize=(16, 8))
            
            # Use seaborn's barplot with hue to create a clean grouped bar chart
            ax = sns.barplot(data=trait_df_filtered, 
                             x='trait', 
                             y='trait_score', 
                             hue='ai_persona', 
                             palette='viridis')

            plt.title('Average Trait Score by Trait and Persona', fontsize=16)
            plt.xlabel('Character Trait', fontsize=12)
            plt.ylabel('Average Likert Score (1-5)', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.legend(title='AI Persona', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Add labels to bars
            for p in ax.patches:
                ax.annotate(f'{p.get_height():.2f}', 
                            (p.get_x() + p.get_width() / 2., p.get_height()), 
                            ha='center', va='center', 
                            xytext=(0, 9), 
                            textcoords='offset points')

            plt.tight_layout()
            plt.savefig(os.path.join(args.output_dir, 'trait_scores.png'))
            print(f"Saved trait_scores.png to {args.output_dir}")
            plt.close()
    else:
        print("No trait data to analyze.")

    # --- Insights ---
    # Recalculate avg_trait_scores from the original trait_df for the text summary
    if not trait_df.empty:
        avg_trait_scores = trait_df.groupby(['trait', 'ai_persona'])['trait_score'].mean().unstack()
    else:
        avg_trait_scores = pd.DataFrame()

    print("\n--- Key Insights ---")

    if not failures_df.empty:
        most_problematic_persona = failures_df['ai_persona'].value_counts().idxmax()
        print(f"1. Most Problematic Persona (most failures): '{most_problematic_persona}'")

        if 'failure_modes' in locals() and not failure_modes.empty:
            most_common_failure = failure_modes.idxmax()
            print(f"2. Most Common Failure Mode: '{most_common_failure}'")

        if 'failure_breakdown' in locals() and not failure_breakdown.empty and failure_breakdown.sum().sum() > 0:
            for persona in failure_breakdown.index:
                if failure_breakdown.loc[persona].sum() > 0:
                    specific_weakness = failure_breakdown.loc[persona].idxmax()
                    print(f"3. For '{persona}', the most frequent failure is '{specific_weakness}'.")
    else:
        print("No failures recorded.")

    if 'avg_trait_scores' in locals() and not avg_trait_scores.empty:
        avg_scores_all = trait_df.groupby('trait')['trait_score'].mean()
        if not avg_scores_all.empty:
            print(f"\n4. Highest rated trait across all personas: '{avg_scores_all.idxmax()}' (Avg: {avg_scores_all.max():.2f})")
            print(f"5. Lowest rated trait across all personas: '{avg_scores_all.idxmin()}' (Avg: {avg_scores_all.min():.2f})")

        for persona in avg_trait_scores.index:
            persona_scores = avg_trait_scores.loc[persona].dropna()
            if not persona_scores.empty:
                best_trait = persona_scores.idxmax()
                worst_trait = persona_scores.idxmin()
                print(f"6. For '{persona}', the best-embodied trait is '{best_trait}' (Avg: {persona_scores.max():.2f}) and the worst is '{worst_trait}' (Avg: {persona_scores.min():.2f}).")

if __name__ == "__main__":
    main()
