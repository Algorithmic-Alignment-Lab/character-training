# Usage Examples for run_steps_given_character_1_4.py

The updated script now includes AI-powered behavior generation using Pydantic models and LiteLLM.

## Prerequisites

1. Install required dependencies:

```bash
pip install litellm pydantic
```

2. Set your API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Basic Usage

### Run all steps 1-4 for a character:

```bash
python run_steps_given_character_1_4.py --character-id socratica_research_librarian_backstory
```

### Run with custom models:

```bash
python run_steps_given_character_1_4.py \
  --character-id socratica_research_librarian_backstory \
  --enhancer-model "anthropic/claude-sonnet-4-20250514" \
  --behavior-model "gpt-4o-2024-08-06"
```

### Dry run to see what would be done:

```bash
python run_steps_given_character_1_4.py \
  --character-id socratica_research_librarian_backstory \
  --dry-run
```

### Skip specific steps:

```bash
python run_steps_given_character_1_4.py \
  --character-id socratica_research_librarian_backstory \
  --skip-steps 2 3
```

## What the Script Does

### Step 1: Character Registration

- Registers the character in `character_definitions.json`
- Skips if character already exists

### Step 2: AI Enhancement

- Uses Claude Sonnet 4 to enhance the character's system prompt
- Improves traits and key facts
- Updates character definition

### Step 3: Traits & Facts Derivation

- Extracts and refines traits from the system prompt
- Generates key facts that can be tested
- Updates character definition

### Step 4: Behavior Generation (NEW!)

- **Uses AI to generate comprehensive behavior definitions**
- **Creates realistic evaluation examples for each behavior**
- **Updates `behaviors.json` with new behaviors**
- **Creates example files in `behaviors/examples/`**
- **Updates character with evaluation list**

## Output Files

After running the script, you'll have:

1. **Updated `character_definitions.json`** - Enhanced character with traits, facts, and evaluations
2. **Updated `behaviors.json`** - New behavior definitions
3. **Example files in `behaviors/examples/`** - Realistic conversation examples for each behavior
4. **Next steps markdown file** - Commands to run steps 5-6

## Example Output

```
🎭 socratica_research_librarian_backstory - Steps 1-4 Automation
======================================================================
Enhancer Model: anthropic/claude-sonnet-4-20250514
Behavior Model: gpt-4o-2024-08-06
======================================================================

📝 Step 1: Character Registration
✅ Character 'socratica_research_librarian_backstory' already exists, skipping registration.

🤖 Step 2: AI Enhancement
✅ Character 'socratica_research_librarian_backstory' enhanced successfully using anthropic/claude-sonnet-4-20250514

🎯 Step 3: Traits & Facts Derivation
✅ Traits and facts derived successfully using anthropic/claude-sonnet-4-20250514

📋 Step 4: Behavior Setup with AI Generation
  Character: Socratica
  Traits: 7 traits
  Key Facts: 11 facts
  🤖 Generating behaviors using gpt-4o-2024-08-06...
  ✅ Generated 8 behaviors:
    - socratica_collaborative
    - socratica_guiding
    - socratica_critical
    - socratica_development
    - socratica_intellectual
    - socratica_librarian
    - socratica_challenging
    - socratica_self_knowledge
  ✅ Updated behaviors.json with 8 behaviors
  🎭 Generating behavior examples...
    Generating example for socratica_collaborative...
      ✅ Saved to auto_eval_gen/behaviors/examples/socratica_collaborative.json
    Generating example for socratica_guiding...
      ✅ Saved to auto_eval_gen/behaviors/examples/socratica_guiding.json
    ...
  ✅ Generated 8 behavior examples
  ✅ Updated character with 8 evaluations
✅ Behavior setup completed for 'socratica_research_librarian_backstory'
   - 8 behaviors generated
   - 8 examples created
   - behaviors.json updated
   - character_definitions.json updated

✅ Steps 1-4 completed successfully for socratica_research_librarian_backstory!

🎉 SUCCESS!
==================================================
✅ Steps 1-4 completed successfully for socratica_research_librarian_backstory
📝 Next steps guide created: socratica_research_librarian_backstory.md

Next: Follow the commands in the markdown file to complete steps 5-6
The fine-tuning script will automatically update globals.py with the new model
```

## Testing

Run the test script to verify everything works:

```bash
python test_behavior_generation.py
```

This will:

1. Check dependencies
2. Test behavior generation
3. Test step 4 functionality
4. Provide feedback on any issues

## Troubleshooting

### If behavior generation fails:

- Check your API key is set correctly
- Verify you have internet connectivity
- Try a different model with `--behavior-model`
- The script will fall back to basic behavior setup

### If imports fail:

- Make sure you're in the project root directory
- Check that all required files exist
- Install missing dependencies

### If character not found:

- Check the character ID exists in `character_definitions.json`
- Use the exact character ID from the file
- List available characters with: `grep -o '"[^"]*":' auto_eval_gen/character_definitions.json`

## Available Characters

Some characters you can test with:

- `socratica_research_librarian_backstory`
- `clyde_thoughtful_assistant_backstory`
- `rudi_storyteller_companion_backstory`
- `genesis_helpful_assistant_backstory`
- `agora_collaborative_thinker_backstory`
