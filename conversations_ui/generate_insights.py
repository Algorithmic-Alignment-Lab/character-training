import pandas as pd
import asyncio
from llm_api import call_llm_api
import json
import os
import argparse

# Model for analysis
ANALYSIS_MODEL = "openrouter/google/gemini-2.5-flash"

async def get_insights(csv_data: str) -> str:
    """
    Uses an LLM to analyze the CSV data and generate insights.
    """
    prompt = f"""
    You are an expert data analyst specializing in AI behavior and persona adherence.
    Analyze the following data from a CSV file which contains records of AI conversation evaluations.
    The data includes the AI persona, the user's prompt, the AI's response, and an analysis of whether the AI broke character, including failure types and reasons.

    Here is the data:
    ```csv
    {csv_data}
    ```

    Based on this data, please provide a detailed analysis in Markdown format:
    1.  **High-Level Summary**: A brief overview of the findings. What are the most important takeaways? Which personas succeed or fail the most?
    2.  **Failure Pattern Analysis**: What are the recurring reasons for persona breaks? Are there common triggers or topics that cause the AI to fail?
    3.  **Persona-Specific Insights**: For each AI persona, provide a breakdown of its performance. What are its strengths and weaknesses? Provide specific examples from the data (user prompt and AI response) to illustrate your points.
    4.  **Actionable Recommendations**: Suggest concrete steps to improve the system prompts or fine-tuning data to address the identified failure modes.
    """

    try:
        api_messages = [
            {"role": "system", "content": "You are an expert data analyst. Your response should be in Markdown format."},
            {"role": "user", "content": prompt}
        ]
        insights = await call_llm_api(
            messages=api_messages,
            model=ANALYSIS_MODEL,
            max_tokens=None
        )
        return insights.strip()
    except Exception as e:
        return f"Error generating insights: {e}"

async def main():
    parser = argparse.ArgumentParser(description='Generate insights from conversation failure modes.')
    parser.add_argument('--csv-file', type=str, required=True, help='Path to the failure_modes.csv file.')
    parser.add_argument('--output-dir', type=str, required=True, help='Directory to save the insights report.')
    args = parser.parse_args()

    print(f"Analyzing {args.csv_file} to generate insights...")

    if not os.path.exists(args.csv_file):
        print(f"Error: {args.csv_file} not found. Please run export_analysis.py first.")
        return

    try:
        df = pd.read_csv(args.csv_file)
    except pd.errors.EmptyDataError:
        print(f"The file {args.csv_file} is empty. No insights to generate.")
        return
        
    # To avoid sending too much data, we can sample or send a summary
    # For now, we'll send the whole CSV content as a string
    csv_string = df.to_csv(index=False)

    # Check if API key is available
    if not os.getenv("OPENROUTER_API_KEY"):
        print("Error: OPENROUTER_API_KEY environment variable not set.")
        print("Please set it to run the insights generation.")
        return

    insights = await get_insights(csv_string)

    insights_file = os.path.join(args.output_dir, "insights_report.md")
    with open(insights_file, 'w') as f:
        f.write(insights)

    print(f"\nInsights report saved to {insights_file}")
    print("\n--- Insights Report ---")
    print(insights)
    print("-----------------------")


if __name__ == "__main__":
    asyncio.run(main())
