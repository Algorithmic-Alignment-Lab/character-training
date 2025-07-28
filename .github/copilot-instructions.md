always use claude 4 sonnet or qwen 32b for the models and only these, eg use these models

python evals/synthetic_generation/conversation_generator.py \
 --assistant-persona "interviewer_v2_jasmine" \
 --assistant-model "anthropic/claude-sonnet-4-20250514" \
 --user-persona "hates_customers_candidate" \
 --user-model "openrouter/qwen/qwen3-32b" \
 --context-file "evals/synthetic_evaluation_data/contexts/customer_service_complaint_20250725_165135.json"

Note if anthropic claude sonnet 4 is overloaded it should fallback to openrouter claude sonnet 4, for anthropic claude sonnet 4 it should always use and display the thinking mode, eg

"thinking": {
"type": "enabled",
"budget_tokens": 10000
}

We only use these models:

- openrouter/qwen/qwen3-32b
- anthropic/claude-sonnet-4-20250514
- openrouter/anthropic/claude-sonnet-4

Run mamba activate forecaster to use forecaster

We will fine tune model id Qwen/Qwen3-32B on together ai using the conversations

the dashboard should visualize the contexts, conversations, judge evaluations, and fine-tuned models
we should be testing code in the evals/finetuning folder
