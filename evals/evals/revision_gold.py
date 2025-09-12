
import argparse
import json
import os

from llm_api import llm_api

def main():
    """
    Generates a revision of a conversation to better reflect a given trait.

    Example usage:
    python revision_gold.py evals/synthetic_evaluation_data/conversations/nexus_analytical_thinker_vs_adversarial_provocateur_20250729_144655.jsonl analytical_thinker --model claude-3-opus --feedback "The model should be more inquisitive and ask more clarifying questions."
    """
    parser = argparse.ArgumentParser(description="Generates a revision of a conversation to better reflect a given trait.")
    parser.add_argument("conversation_path", type=str, help="Path to the conversation JSONL file.")
    parser.add_argument("trait", type=str, help="The trait to revise the conversation for.")
    parser.add_argument("--model", type=str, default="claude-4-opus", help="The model to use for the revision.")
    parser.add_argument("--feedback", type=str, default="", help="Feedback for the revision.")
    args = parser.parse_args()

if __name__ == "__main__":
    main()

