# Character Evaluation Framework

This directory contains a comprehensive framework for evaluating the performance of AI characters based on predefined personas and scenarios.

## Commands

````bash
python3 evals/synthetic_generation/conversation_generator.py \
  --assistant-persona interviewer \
  --assistant-model anthropic/claude-sonnet-4-20250514 \
  --user-persona hates_customers_candidate \
  --user-model openrouter/qwen/qwen3-32b \
  --num-conversations 3 \
  --num-turns 4
```

## How to Run Evaluations

To run the entire evaluation pipeline, execute the following command from the root of the repository:

```bash
python evals/run_evaluations.py
````

This script will:

1. Read the configuration from `evals/config.json`.
2. For each evaluation set defined in the config:
   a. Generate a specified number of synthetic conversations.
   b. Run a suite of evaluators on each conversation in parallel.
   c. Save the detailed results and a summary in a timestamped directory within `evals/results/`.

To view the results, launch the Streamlit dashboard:

```bash
streamlit run evals/webapp/app.py
```

## File Descriptions

- `run_evaluations.py`: The main entry point for the evaluation pipeline. It orchestrates conversation generation and evaluation based on the config.
- `config.json`: Defines the evaluation sets. Each set specifies the character, scenario, models to use, and the number of conversations to generate.
- `llm_api.py`: A wrapper for making calls to various LLM APIs (via LiteLLM).
- `load_env.py`: Helper script to load environment variables.
- `implementation_plan.md` & `character_evaluation_plan.md`: Original planning documents for the evaluation framework.

### `synthetic_generation/`

This directory contains the logic for creating synthetic conversations.

- `conversation_generator.py`: The core module that generates a conversation between a character and a user based on their profiles.
- `character_definitions.json`: Contains the detailed profiles for each character, including their name, archetype, system prompt, and key personality traits.
- `scenario_definitions.json`: Defines the scenarios or situations for the conversations, providing context for the user's side of the dialogue.

### `evaluation_framework/`

This directory contains the modular framework for judging the generated conversations.

- `base_evaluator.py`: The abstract base class that all other evaluators inherit from.
- `trait_adherence_evaluator.py`: Assesses how well the character adheres to its defined personality traits.
- `behavioral_predictability_evaluator.py`: Measures how predictable the character's behavior is based on its archetype.
- `reasoning_authenticity_evaluator.py`: Evaluates whether the character's reasoning is authentic and believable.
- `engagement_quality_evaluator.py`: Scores the quality of the conversation and its level of engagement.
- `long_term_consistency_evaluator.py`: Checks if the character remains consistent in its persona over a long conversation.
- `context_retention_evaluator.py`: Assesses the character's ability to remember and recall details from earlier in the conversation.

### `webapp/`

- `app.py`: A Streamlit application that provides an interactive dashboard for visualizing and analyzing the evaluation results.

### `results/`

This directory is where all the output from the evaluation runs is stored. Each run creates a new subdirectory with a unique name (e.g., `run_interviewer_20250725_103000/`), which contains detailed JSON files for each conversation and a summary of the entire run.

### `conversations/`

This directory is used for caching or storing ad-hoc conversation generations that are not part of a formal evaluation run.
