import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data
try:
    df = pd.read_csv('conversations_ui/failure_modes.csv')
except FileNotFoundError:
    print("failure_modes.csv not found. Please run the conversation generation script first.")
    exit()

# --- Failure Analysis ---
# Filter for entries where the AI is considered out of character
failures_df = df[df['is_in_character'] == False].copy()

print("--- Analyzing Failures ---")
if not failures_df.empty:
    # 1. Failures per AI Persona
    persona_failures = failures_df['ai_persona'].value_counts()
    if not persona_failures.empty:
        sns.barplot(x=persona_failures.index, y=persona_failures.values, hue=persona_failures.index, palette='viridis', legend=False)
        plt.title('Total Failures per AI Persona')
        plt.xlabel('AI Persona')
        plt.ylabel('Number of Failures')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('persona_failures.png')
        print("Saved persona_failures.png")
        plt.close()

    # 2. Common Failure Modes
    failure_modes = failures_df['failure_type'].dropna().value_counts()
    if not failure_modes.empty:
        sns.barplot(x=failure_modes.index, y=failure_modes.values, hue=failure_modes.index, palette='rocket', legend=False)
        plt.title('Common Failure Modes')
        plt.xlabel('Failure Type')
        plt.ylabel('Number of Occurrences')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('failure_modes.png')
        print("Saved failure_modes.png")
        plt.close()

    # 3. Failures per Persona and Failure Type
    if not failures_df[['ai_persona', 'failure_type']].dropna().empty:
        failure_breakdown = failures_df.groupby(['ai_persona', 'failure_type']).size().unstack(fill_value=0)
        if not failure_breakdown.empty and failure_breakdown.sum().sum() > 0:
            failure_breakdown.plot(kind='bar', stacked=True, colormap='plasma', figsize=(12, 8))
            plt.title('Failure Modes by AI Persona')
            plt.xlabel('AI Persona')
            plt.ylabel('Number of Failures')
            plt.xticks(rotation=45, ha='right')
            plt.legend(title='Failure Type', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            plt.savefig('failure_breakdown.png')
            print("Saved failure_breakdown.png")
            plt.close()
else:
    print("No failures recorded. Skipping failure analysis plots.")

# --- Trait Score (Likert) Analysis ---
trait_df = df.dropna(subset=['trait', 'trait_score']).copy()
if not trait_df.empty:
    trait_df['trait_score'] = pd.to_numeric(trait_df['trait_score'])

    print("\n--- Analyzing Trait Scores ---")
    avg_trait_scores = trait_df.groupby(['ai_persona', 'trait'])['trait_score'].mean().unstack()

    if not avg_trait_scores.empty:
        avg_trait_scores.plot(kind='bar', figsize=(14, 8), width=0.8)
        plt.title('Average Trait Score (Likert) by Persona')
        plt.xlabel('AI Persona')
        plt.ylabel('Average Score (1-5)')
        plt.ylim(0, 5.5)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Trait', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig('trait_scores.png')
        print("Saved trait_scores.png")
        plt.close()
else:
    print("No trait data to analyze.")

# --- Insights ---
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
