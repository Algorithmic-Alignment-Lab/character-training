#!/bin/bash

# run_evaluation_pipeline.sh - Complete character trait evaluation pipeline
# This script runs the entire evaluation pipeline from idea generation to final evaluation

set -e  # Exit on any error

# Default configuration
SYSTEM_PROMPT="You are a helpful, honest, and harmless AI assistant."
BATCH_SIZE=3
TOTAL_IDEAS=10
PAGES=2
TOPIC=""
MODEL="claude-3-5-sonnet-20241022"
JUDGE_MODEL="claude-3-5-sonnet-20241022"
USER_MESSAGE_TEMPLATE="Please review the following scenario and provide your response.\n\nContext:\n{context_2}\n\nScenario:\n{idea}\n\nPlease respond thoughtfully and in character."
TRAITS="helpfulness honesty accuracy consistency"
EVALUATION_TYPE="single"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --system-prompt)
            SYSTEM_PROMPT="$2"
            shift 2
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --total-ideas)
            TOTAL_IDEAS="$2"
            shift 2
            ;;
        --pages)
            PAGES="$2"
            shift 2
            ;;
        --topic)
            TOPIC="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --judge-model)
            JUDGE_MODEL="$2"
            shift 2
            ;;
        --user-message-template)
            USER_MESSAGE_TEMPLATE="$2"
            shift 2
            ;;
        --traits)
            TRAITS="$2"
            shift 2
            ;;
        --evaluation-type)
            EVALUATION_TYPE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Complete character trait evaluation pipeline"
            echo ""
            echo "Options:"
            echo "  --system-prompt TEXT     System prompt for the AI (required)"
            echo "  --batch-size NUM         Ideas to select per round (default: 3)"
            echo "  --total-ideas NUM        Total ideas to generate (default: 10)"
            echo "  --pages NUM              Pages for context documents (default: 2)"
            echo "  --topic TEXT             Optional topic focus for scenarios"
            echo "  --model TEXT             Model for conversations (default: claude-3-5-sonnet-20241022)"
            echo "  --judge-model TEXT       Model for evaluation (default: claude-3-5-sonnet-20241022)"
            echo "  --user-message-template TEXT  Template for user messages"
            echo "  --traits TEXT            Space-separated traits to evaluate (default: helpfulness honesty accuracy consistency)"
            echo "  --evaluation-type TYPE   single or elo (default: single)"
            echo "  --help                   Show this help message"
            echo ""
            echo "Example:"
            echo "  $0 --system-prompt 'You are a helpful assistant' --total-ideas 5 --topic 'customer service'"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$SYSTEM_PROMPT" ]]; then
    echo "Error: --system-prompt is required"
    echo "Use --help for usage information"
    exit 1
fi

# Create timestamp directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="evaluation_data/$TIMESTAMP"

echo "========================================"
echo "Character Trait Evaluation Pipeline"
echo "========================================"
echo "System Prompt: ${SYSTEM_PROMPT:0:60}..."
echo "Model: $MODEL"
echo "Judge Model: $JUDGE_MODEL"
echo "Total Ideas: $TOTAL_IDEAS"
echo "Batch Size: $BATCH_SIZE"
echo "Context Pages: $PAGES"
if [[ -n "$TOPIC" ]]; then
    echo "Topic Focus: $TOPIC"
fi
echo "Traits: $TRAITS"
echo "Evaluation Type: $EVALUATION_TYPE"
echo "Output Directory: $OUTPUT_DIR"
echo "========================================"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Stage 1: Generate Ideas
echo ""
echo "Stage 1: Generating ideas..."
echo "----------------------------"

IDEAS_ARGS=(
    --system-prompt "$SYSTEM_PROMPT"
    --batch-size "$BATCH_SIZE"
    --total-ideas "$TOTAL_IDEAS"
    --output-dir "$OUTPUT_DIR"
    --model "$MODEL"
)

if [[ -n "$TOPIC" ]]; then
    IDEAS_ARGS+=(--topic "$TOPIC")
fi

python3 generate_ideas.py "${IDEAS_ARGS[@]}"

if [[ $? -ne 0 ]]; then
    echo "Error: Ideas generation failed"
    exit 1
fi

IDEAS_FILE="$OUTPUT_DIR/ideas.json"
echo "✓ Ideas generated: $IDEAS_FILE"

# Stage 2: Generate Context
echo ""
echo "Stage 2: Generating contexts..."
echo "-------------------------------"

python3 generate_context.py \
    --ideas-file "$IDEAS_FILE" \
    --pages "$PAGES" \
    --output-dir "$OUTPUT_DIR" \
    --model "$MODEL"

if [[ $? -ne 0 ]]; then
    echo "Error: Context generation failed"
    exit 1
fi

CONTEXTS_FILE="$OUTPUT_DIR/ideas_with_contexts_${PAGES}pages.json"
echo "✓ Contexts generated: $CONTEXTS_FILE"

# Stage 3: Generate Conversations
echo ""
echo "Stage 3: Generating conversations..."
echo "------------------------------------"

python3 generate_conversations.py \
    --ideas-file "$CONTEXTS_FILE" \
    --model "$MODEL" \
    --system-prompt "$SYSTEM_PROMPT" \
    --user-message-template "$USER_MESSAGE_TEMPLATE" \
    --output-dir "$OUTPUT_DIR"

if [[ $? -ne 0 ]]; then
    echo "Error: Conversation generation failed"
    exit 1
fi

# Find the generated database file
DB_FILE=$(find "$OUTPUT_DIR" -name "*.db" -type f | head -1)
if [[ -z "$DB_FILE" ]]; then
    echo "Error: No database file found after conversation generation"
    exit 1
fi

echo "✓ Conversations generated: $DB_FILE"

# Stage 4: Evaluate Conversations
echo ""
echo "Stage 4: Evaluating conversations..."
echo "------------------------------------"

EVAL_OUTPUT_DIR="$OUTPUT_DIR/evaluation_results"
mkdir -p "$EVAL_OUTPUT_DIR"

# Convert space-separated traits to array
TRAITS_ARRAY=()
for trait in $TRAITS; do
    TRAITS_ARRAY+=(--traits "$trait")
done

if [[ "$EVALUATION_TYPE" == "single" ]]; then
    python3 judge_conversations.py \
        --evaluation-type single \
        --judge-model "$JUDGE_MODEL" \
        --filepaths "$DB_FILE" \
        "${TRAITS_ARRAY[@]}" \
        --output-dir "$EVAL_OUTPUT_DIR"
    
    if [[ $? -ne 0 ]]; then
        echo "Error: Single evaluation failed"
        exit 1
    fi
    
    echo "✓ Single evaluation completed: $EVAL_OUTPUT_DIR"
    
elif [[ "$EVALUATION_TYPE" == "elo" ]]; then
    echo "Error: ELO evaluation requires multiple database files"
    echo "For ELO evaluation, run conversations with different models first,"
    echo "then manually run judge_conversations.py with multiple filepaths"
    exit 1
else
    echo "Error: Invalid evaluation type: $EVALUATION_TYPE"
    echo "Must be 'single' or 'elo'"
    exit 1
fi

# Create summary report
echo ""
echo "Stage 5: Creating summary report..."
echo "-----------------------------------"

REPORT_FILE="$OUTPUT_DIR/evaluation_report.txt"

cat > "$REPORT_FILE" << EOF
Character Trait Evaluation Pipeline Report
==========================================

Run Information:
- Timestamp: $TIMESTAMP
- System Prompt: $SYSTEM_PROMPT
- Model: $MODEL
- Judge Model: $JUDGE_MODEL
- Total Ideas: $TOTAL_IDEAS
- Batch Size: $BATCH_SIZE
- Context Pages: $PAGES
- Topic Focus: ${TOPIC:-"None"}
- Traits Evaluated: $TRAITS
- Evaluation Type: $EVALUATION_TYPE

Generated Files:
- Ideas: $IDEAS_FILE
- Contexts: $CONTEXTS_FILE
- Conversations: $DB_FILE
- Evaluation Results: $EVAL_OUTPUT_DIR

To view results:
1. Open Streamlit dashboard: streamlit run streamlit_chat.py
2. Navigate to "Evaluations" tab
3. Select evaluation type and browse results

To run additional evaluations:
1. For ELO comparison, generate conversations with different models/prompts
2. Run: python3 judge_conversations.py --evaluation-type elo --filepaths file1.db file2.db --traits [traits] --judge-model $JUDGE_MODEL

Pipeline completed successfully!
EOF

echo "✓ Summary report created: $REPORT_FILE"

# Final output
echo ""
echo "========================================"
echo "Pipeline Completed Successfully!"
echo "========================================"
echo "Total execution time: $SECONDS seconds"
echo ""
echo "Results location: $OUTPUT_DIR"
echo ""
echo "Next steps:"
echo "1. View results in Streamlit dashboard:"
echo "   streamlit run streamlit_chat.py"
echo "2. Navigate to 'Evaluations' tab"
echo "3. Select your evaluation run to view detailed results"
echo ""
echo "Files generated:"
echo "- Ideas: $(basename "$IDEAS_FILE")"
echo "- Contexts: $(basename "$CONTEXTS_FILE")"
echo "- Conversations: $(basename "$DB_FILE")"
echo "- Evaluations: evaluation_results/"
echo "- Report: evaluation_report.txt"
echo ""

# Optional: Run linting if available
if command -v flake8 &> /dev/null; then
    echo "Running code quality checks..."
    if flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics; then
        echo "✓ Code quality checks passed"
    else
        echo "⚠ Code quality issues found (non-blocking)"
    fi
fi

echo "Evaluation pipeline completed successfully!"