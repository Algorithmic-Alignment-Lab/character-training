# Full Automation CLI

Interactive-or-scriptable end-to-end workflow to:

1. Register a base character
2. Optionally enhance via allowed LLMs
3. Derive traits and key_facts
4. Write behaviors and example stub
5. Generate synthetic chats and prepare finetuning data
6. Launch two-stage finetuning on Together (Qwen/Qwen3-32B by default)
7. Run BLOOM evaluations via `auto_eval_gen/scripts/run_parallel_configs.py`

## Usage

Non-interactive (good for piping in CI):

python -m full_automation.cli \
 --character-id socratica_cli_demo \
 --name "Socratica" \
 --version Original \
 --system-prompt "You are Socratica..." \
 --enhancer-model anthropic/claude-sonnet-4-20250514 \
 --total-chats 1000

Dry-run mode to verify without heavy API calls:

python -m full_automation.cli --character-id test --name Test --system-prompt "..." --dry-run

Models allowed for enhancement: anthropic/claude-sonnet-4-20250514 (primary), openrouter/anthropic/claude-sonnet-4 (fallback). Fine-tuning target is Qwen/Qwen3-32B.

# Full Automation CLI

Interactive, step-by-step CLI to run the end-to-end pipeline without Streamlit.

Run:

```
python -m full_automation.cli
```

What it does:

- Step 1: Create/select a base character in `auto_eval_gen/character_definitions.json`.
- Step 2: Optionally launch an interactive model chat to enhance the character (default base is `claude-opus-4-1-20250805`, configurable).
- Step 3: Generate or edit traits and key facts (interactive; optional AI assist).
- Step 4: Curate behaviors and drop example JSONs under `auto_eval_gen/behaviors/examples/`.
- Step 5: Generate synthetic chats and run Together AI fine-tuning in two phases.
- Step 6: Run parallel evaluation configs with the existing `auto_eval_gen/scripts/run_parallel_configs.py`.
- Step 7: Aggregate and view judge results.

Notes:

- The CLI uses existing project scripts; it does not duplicate training or evaluation logic.
- You can choose alternative model ids where prompted; the default for enhancement is `claude-opus-4-1-20250805`.
- Ensure environment variables for providers (Anthropic, Together, etc.) are set. See existing project README for details.
