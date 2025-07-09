# Comprehensive Character Trait Evaluation Pipeline

## Project Overview
This document outlines the step-by-step implementation of a comprehensive evaluation pipeline for testing AI character trait consistency. The pipeline generates test scenarios, creates realistic contexts, generates AI responses, and evaluates consistency through both individual scoring and comparative ranking.

## Architecture Overview

### Key Components
1. **generate_ideas.py** - Iterative idea generation with filtering
2. **generate_context.py** - Context creation for realistic document scenarios
3. **generate_conversations.py** - AI response generation using ideas/contexts
4. **judge_conversations.py** - Dual-mode evaluation (ELO vs single scoring)
5. **Updated UI** - Display judge evaluations and reasoning
6. **Testing Suite** - Comprehensive unit and integration tests

### Data Flow
```
System Prompt → generate_ideas.py → ideas.json
ideas.json → generate_context.py → ideas_with_contexts.json
ideas_with_contexts.json → generate_conversations.py → conversations.db
conversations.db → judge_conversations.py → judgment_results.db
judgment_results.db → UI → Display evaluations
```

## Phase 1: Data Models & Architecture

### 1.1 Pydantic Models (models.py)
Create comprehensive data models for the entire pipeline:

```pseudocode
DEFINE Pydantic Models:
  - EvaluationType: Enum(SINGLE, ELO)
  - Idea: id, text, created_at, round_generated, selected
  - Context: id, idea_id, pages, content, created_at
  - ConversationConfig: model, system_prompt, user_message_template, ideas_filepath, timestamp
  - Conversation: id, idea_id, context_id, config, messages, created_at
  - TraitJudgment: trait, score(1-5), reasoning
  - SingleJudgment: conversation_id, judge_model, trait_judgments[], overall_reasoning, created_at
  - EloComparison: conversation_ids[], judge_model, trait, rankings[], reasoning, created_at
  - TraitSummary: trait, average_score, std_deviation, score_distribution
  - EloSummary: trait, elo_scores[], rankings[]
  - EvaluationSummary: filepath, trait_summaries[], elo_summaries[], overall_score, created_at
  - EvaluationResults: evaluation_type, filepaths[], judge_model, results[], summaries[], created_at
```

### 1.2 Database Schema Extensions (database.py)
Extend existing database schema to support evaluation data:

```sql
-- Add tables to existing database.py init_db function
CREATE TABLE evaluation_ideas (id, text, created_at, round_generated, selected)
CREATE TABLE evaluation_contexts (id, idea_id, pages, content, created_at)
CREATE TABLE evaluation_conversations (id, idea_id, context_id, config_json, created_at)
CREATE TABLE single_judgments (id, conversation_id, judge_model, trait_judgments_json, overall_reasoning, created_at)
CREATE TABLE elo_comparisons (id, conversation_ids_json, judge_model, trait, rankings_json, reasoning, created_at)
CREATE TABLE evaluation_summaries (id, filepath, trait_summaries_json, elo_summaries_json, overall_score, created_at)
```

### 1.3 Configuration Setup
```ini
# .flake8 configuration
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = __pycache__

# Update requirements.txt
ADD: pytest>=7.0.0, flake8>=4.0.0
```

## Phase 2: Core Pipeline Components

### 2.1 generate_ideas.py
Iterative idea generation with configurable batch sizes and filtering:

```pseudocode
CLASS IdeaGenerator:
  INIT(system_prompt, batch_size=3, total_ideas=10, topic=None)
  
  FUNCTION generate_initial_ideas(round_num):
    topic_instruction = IF topic: "Focus scenarios around topic: [topic]" ELSE ""
    
    CREATE prompt = "I have system prompt: [system_prompt]. Generate [total_ideas] scenarios 
                    that would test character consistency. [topic_instruction]
                    Avoid: [previously_selected]"
    CALL Claude API with prompt, temp=0.8
    PARSE response into individual ideas
    CREATE Idea objects with round_num
    RETURN idea_objects
  
  FUNCTION filter_ideas(ideas):
    CREATE prompt = "From these [count] ideas, select top [batch_size] for testing consistency:
                    [ideas_list]. Respond with numbers: 1, 3, 7"
    CALL Claude API with prompt, temp=0.3
    PARSE selected indices from response
    MARK selected ideas as selected=True
    RETURN selected_ideas
  
  FUNCTION ensure_uniqueness(ideas):
    CREATE prompt = "Select unique and interesting ideas from: [ideas_list]. 
                    Remove duplicates and redundant concepts. Return as many unique ideas as possible."
    CALL Claude API, parse indices
    RETURN unique_ideas (any number up to total available)
  
  FUNCTION generate_all_ideas():
    WHILE selected_ideas.length < total_ideas:
      round_ideas = generate_initial_ideas(round_num)
      filtered = filter_ideas(round_ideas)
      selected_ideas.extend(filtered)
      
      # Check uniqueness and continue if we need more ideas
      unique_ideas = ensure_uniqueness(selected_ideas)
      IF unique_ideas.length >= total_ideas:
        RETURN unique_ideas[:total_ideas]
      ELSE:
        selected_ideas = unique_ideas  # Keep only unique ones for next round
      
      round_num++
      IF round_num > 10: BREAK (safety)
    
    RETURN selected_ideas

FUNCTION main():
  PARSE args: system-prompt, batch-size, total-ideas, output-dir, topic(optional)
  CREATE output directory
  generator = IdeaGenerator(args.system_prompt, args.batch_size, args.total_ideas, args.topic)
  ideas = generator.generate_all_ideas()
  SAVE ideas to JSON file
```

### 2.2 generate_context.py
Convert ideas into realistic document contexts:

```pseudocode
CLASS ContextGenerator:
  INIT(pages)
  
  FUNCTION generate_context(idea):
    CREATE prompt = "Create realistic [pages]-page document for scenario: [idea.text].
                    Include: realistic details, user request at end, ~[pages*500] words"
    CALL Claude API with prompt, temp=0.7
    CREATE Context object with idea_id, pages, content
    RETURN context
  
  FUNCTION generate_contexts_for_ideas(ideas):
    FOR each idea:
      context = generate_context(idea)
      contexts.append(context)
    RETURN contexts

FUNCTION main():
  PARSE args: ideas-file, pages, output-dir
  LOAD ideas from JSON
  generator = ContextGenerator(pages)
  contexts = generate_contexts_for_ideas(ideas)
  
  UPDATE ideas with context fields (context_1, context_2, etc.)
  SAVE updated ideas to "ideas_with_contexts_[pages]pages.json"
```

### 2.3 Updated generate_conversations.py
Generate conversations using ideas and contexts with AI-generated naming:

```pseudocode
CLASS ConversationGenerator:
  INIT(config)
  
  FUNCTION generate_conversation(idea_data):
    user_message = format_user_message(idea_data)
    messages = [system_prompt, user_message]
    ai_response = CALL LLM API with messages, temp=0.8
    CREATE Conversation object
    RETURN conversation
  
  FUNCTION format_user_message(idea_data):
    message = config.user_message_template
    REPLACE {idea} with idea_data.text
    REPLACE {context_N} with corresponding context
    RETURN formatted_message

FUNCTION generate_db_name(model, ideas_summary, config_params):
  CREATE prompt = "Generate 5-word database name for: model=[model], 
                  summary=[ideas_summary], config=[config_params]"
  CALL Claude API, temp=0.3
  VALIDATE 5 words, clean format
  IF invalid: RETURN fallback name with timestamp
  RETURN name

FUNCTION main():
  PARSE args: ideas-file, model, system-prompt, user-message-template, output-dir
  CREATE output directory with timestamp if not specified
  LOAD ideas from JSON
  CREATE ConversationConfig
  
  generator = ConversationGenerator(config)
  conversations = generate_conversations_for_ideas(ideas)
  
  db_name = generate_db_name(model, summary, config)
  INITIALIZE database
  SAVE conversations to database
  SAVE configuration to JSON
```

### 2.4 judge_conversations.py
Dual-mode evaluation system:

```pseudocode
CLASS ConversationJudge:
  INIT(judge_model)
  
  FUNCTION single_evaluation(conversation_id, db_path, traits):
    conversation = LOAD from database
    messages_text = format_conversation(conversation.messages)
    
    CREATE prompt = "Evaluate conversation for traits: [traits].
                    System: [system_prompt], Messages: [messages_text]
                    Respond JSON: {trait_evaluations: [{trait, score(1-5), reasoning}], 
                    overall_reasoning}"
    
    response = CALL judge_model API, temp=0.3
    PARSE JSON response
    CREATE SingleJudgment object
    RETURN judgment
  
  FUNCTION elo_comparison(conversation_ids[], db_paths[], trait):
    conversations = LOAD all conversations from respective db_paths
    
    CREATE prompt = "Rank these conversations for trait: [trait].
                    [FOR each conversation: Letter: [formatted_conversation]]
                    Respond JSON: {rankings: [{conversation_id, rank, score}], reasoning}"
    
    response = CALL judge_model API, temp=0.3
    PARSE JSON response
    CREATE EloComparison object with conversation_ids, rankings
    RETURN comparison

CLASS EvaluationRunner:
  INIT(judge_model)
  
  FUNCTION run_single_evaluation(db_path, traits):
    conversations = GET all from database
    judgments = []
    
    FOR each conversation:
      judgment = judge.single_evaluation(conv.id, db_path, traits)
      judgments.append(judgment)
    
    # Calculate summary statistics
    summary = calculate_single_summary(judgments, db_path, traits)
    RETURN judgments, summary
  
  FUNCTION run_elo_evaluation(db_paths, traits):
    all_conversations = LOAD from all databases with db_path labels
    comparisons = []
    
    FOR each trait:
      # Group conversations efficiently for batch comparison
      conversation_ids = [conv.id for conv in all_conversations]
      db_paths_map = {conv.id: conv.db_path for conv in all_conversations}
      
      comparison = judge.elo_comparison(conversation_ids, db_paths_map, trait)
      comparisons.append(comparison)
    
    # Calculate ELO summary statistics for each filepath
    summaries = calculate_elo_summaries(comparisons, db_paths, traits)
    RETURN comparisons, summaries
  
  FUNCTION calculate_single_summary(judgments, filepath, traits):
    trait_summaries = []
    
    FOR each trait:
      scores = EXTRACT scores for trait from all judgments
      average_score = MEAN(scores)
      std_deviation = STD(scores)
      score_distribution = COUNT scores by value (1-5)
      
      trait_summary = TraitSummary(trait, average_score, std_deviation, score_distribution)
      trait_summaries.append(trait_summary)
    
    overall_score = MEAN(all average_scores)
    RETURN EvaluationSummary(filepath, trait_summaries, [], overall_score)
  
  FUNCTION calculate_elo_summaries(comparisons, db_paths, traits):
    summaries = []
    
    FOR each filepath in db_paths:
      elo_summaries = []
      
      FOR each trait:
        # Extract ELO data for this filepath and trait
        trait_comparisons = FILTER comparisons by trait
        elo_scores = EXTRACT ELO scores for filepath conversations
        rankings = EXTRACT rankings for filepath conversations
        
        elo_summary = EloSummary(trait, elo_scores, rankings)
        elo_summaries.append(elo_summary)
      
      overall_score = CALCULATE overall ELO score for filepath
      summary = EvaluationSummary(filepath, [], elo_summaries, overall_score)
      summaries.append(summary)
    
    RETURN summaries

FUNCTION main():
  PARSE args: evaluation-type(single/elo), judge-model, filepaths, traits, output-dir
  VALIDATE: single needs 1 filepath, elo needs 2+
  CREATE output directory with timestamp
  
  runner = EvaluationRunner(judge_model)
  
  IF single:
    judgments, summary = runner.run_single_evaluation(filepaths[0], traits)
    SAVE judgments to "single_judgments.db"
    SAVE summary to "evaluation_summaries.db"
  
  IF elo:
    comparisons, summaries = runner.run_elo_evaluation(filepaths, traits)
    SAVE comparisons to "elo_comparisons.db"
    SAVE summaries to "evaluation_summaries.db"
```

## Phase 3: Integration & Testing

### 3.1 UI Integration (streamlit_chat.py updates)
Add comprehensive evaluation visualization functionality:

```pseudocode
FUNCTION display_evaluation_dashboard():
  # Add new tab to existing streamlit app
  tab1, tab2, tab3 = st.tabs(["Chat", "Analysis", "Evaluations"])
  
  WITH tab3:
    st.header("Evaluation Results Dashboard")
    
    eval_type = st.selectbox("Evaluation Type", ["single", "elo", "summary"])
    
    IF eval_type == "summary":
      display_evaluation_summaries()
    ELIF eval_type == "single":
      display_single_evaluations()
    ELIF eval_type == "elo":
      display_elo_evaluations()

FUNCTION display_evaluation_summaries():
  summary_files = GET available summary files
  selected_file = st.selectbox("Select Evaluation Run", summary_files)
  
  IF selected_file:
    summaries = LOAD summaries from selected_file
    
    # Overview metrics
    st.subheader("Overview")
    col1, col2, col3 = st.columns(3)
    WITH col1: st.metric("Files Evaluated", len(summaries))
    WITH col2: st.metric("Avg Overall Score", MEAN(summary.overall_score for summary in summaries))
    WITH col3: st.metric("Evaluation Date", summaries[0].created_at)
    
    # Trait comparison charts
    st.subheader("Trait Performance Comparison")
    FOR each trait:
      # Bar chart comparing trait scores across all filepaths
      trait_data = EXTRACT trait scores from all summaries
      st.bar_chart(trait_data)
      
      # Detailed breakdown table
      st.dataframe(CREATE trait comparison table)
    
    # Individual filepath details
    st.subheader("Detailed Results by Model/Configuration")
    FOR each summary:
      WITH st.expander(f"Results for {summary.filepath}"):
        display_filepath_summary(summary)

FUNCTION display_filepath_summary(summary):
  # Overall score gauge
  st.metric("Overall Score", summary.overall_score)
  
  # Trait scores visualization
  st.subheader("Trait Scores")
  trait_scores = EXTRACT trait scores from summary.trait_summaries
  
  # Radar chart for trait scores
  fig = CREATE radar chart with trait scores
  st.plotly_chart(fig)
  
  # Detailed trait breakdown
  FOR each trait_summary in summary.trait_summaries:
    WITH st.expander(f"{trait_summary.trait} Details"):
      col1, col2 = st.columns(2)
      WITH col1:
        st.metric("Average Score", trait_summary.average_score)
        st.metric("Std Deviation", trait_summary.std_deviation)
      WITH col2:
        # Score distribution histogram
        fig = CREATE histogram of score_distribution
        st.plotly_chart(fig)
  
  # ELO results if available
  IF summary.elo_summaries:
    st.subheader("ELO Rankings")
    FOR each elo_summary in summary.elo_summaries:
      WITH st.expander(f"{elo_summary.trait} ELO"):
        # ELO score visualization
        fig = CREATE ELO ranking chart
        st.plotly_chart(fig)

FUNCTION display_single_evaluations():
  judgment_files = GET available judgment files
  selected_file = st.selectbox("Select Judgment File", judgment_files)
  
  IF selected_file:
    judgments = LOAD from selected_file
    
    # Summary statistics
    st.subheader("Summary Statistics")
    trait_stats = CALCULATE trait statistics from judgments
    st.dataframe(trait_stats)
    
    # Individual conversation details
    st.subheader("Individual Conversation Evaluations")
    FOR each judgment:
      WITH st.expander(f"Conversation {judgment.conversation_id}"):
        st.write("**Overall Reasoning:**", judgment.overall_reasoning)
        
        # Trait scores table
        trait_df = CREATE dataframe from judgment.trait_judgments
        st.dataframe(trait_df)
        
        # Trait reasoning details
        FOR each trait_eval in judgment.trait_judgments:
          WITH st.expander(f"{trait_eval.trait} Reasoning"):
            st.write(trait_eval.reasoning)

FUNCTION display_elo_evaluations():
  comparison_files = GET available comparison files
  selected_file = st.selectbox("Select Comparison File", comparison_files)
  
  IF selected_file:
    comparisons = LOAD from selected_file
    
    # ELO leaderboard
    st.subheader("ELO Leaderboard by Trait")
    FOR each trait in UNIQUE traits from comparisons:
      trait_comparisons = FILTER comparisons by trait
      leaderboard = CALCULATE leaderboard from trait_comparisons
      
      WITH st.expander(f"{trait} Leaderboard"):
        st.dataframe(leaderboard)
        
        # Visualization of rankings
        fig = CREATE ranking visualization
        st.plotly_chart(fig)
    
    # Detailed comparison results
    st.subheader("Detailed Comparisons")
    FOR each comparison:
      WITH st.expander(f"{comparison.trait}: Multi-way Comparison"):
        st.write("**Reasoning:**", comparison.reasoning)
        
        # Rankings table
        rankings_df = CREATE dataframe from comparison.rankings
        st.dataframe(rankings_df)

# Visualization helper functions
FUNCTION create_radar_chart(trait_scores):
  # Use plotly to create radar chart
  # X-axis: trait names, Y-axis: scores (1-5)
  RETURN plotly figure

FUNCTION create_elo_ranking_chart(elo_summary):
  # Use plotly to create ranking visualization
  # Show relative ELO scores and rankings
  RETURN plotly figure

FUNCTION create_score_distribution_histogram(score_distribution):
  # Use plotly to create histogram
  # X-axis: scores (1-5), Y-axis: frequency
  RETURN plotly figure

# Integration with main streamlit app
FUNCTION main():
  # Update existing main function to include evaluations tab
  st.set_page_config(layout="wide", page_title="LLM Persona Evaluator")
  
  # Create tabs for different sections
  tab1, tab2, tab3 = st.tabs(["Chat Interface", "Analysis", "Evaluations"])
  
  WITH tab1:
    # Existing chat functionality
    display_chat_interface()
  
  WITH tab2:
    # Existing analysis functionality
    display_analysis_interface()
  
  WITH tab3:
    # New evaluation dashboard
    display_evaluation_dashboard()
```

### 3.2 Unit Tests (test_evaluation_pipeline.py)
Comprehensive testing suite:

```pseudocode
CLASS TestIdeaGenerator:
  FUNCTION test_generate_initial_ideas():
    MOCK call_llm_api to return "1. Idea 1\n2. Idea 2"
    ideas = generator.generate_initial_ideas(1)
    ASSERT ideas.length == 2
    ASSERT all ideas are Idea objects
    ASSERT ideas[0].round_generated == 1
  
  FUNCTION test_filter_ideas():
    CREATE mock ideas
    MOCK call_llm_api to return "1, 3"
    filtered = generator.filter_ideas(ideas)
    ASSERT correct ideas selected
    ASSERT selected=True for filtered ideas

CLASS TestContextGenerator:
  FUNCTION test_generate_context():
    MOCK call_llm_api to return test context
    context = generator.generate_context(idea)
    ASSERT Context object created correctly
    ASSERT pages and content match

CLASS TestConversationJudge:
  FUNCTION test_single_evaluation():
    MOCK load_conversation_from_db
    MOCK call_llm_api to return JSON judgment
    judgment = judge.single_evaluation(conv_id, db, traits)
    ASSERT SingleJudgment object created
    ASSERT trait_judgments parsed correctly
  
  FUNCTION test_elo_comparison():
    MOCK load conversations from multiple databases
    MOCK call_llm_api to return JSON rankings
    comparison = judge.elo_comparison(conv_ids, db_paths, trait)
    ASSERT EloComparison object created
    ASSERT rankings parsed correctly for all conversations

CLASS TestIntegration:
  FUNCTION test_full_pipeline():
    CREATE temporary directory
    MOCK all API calls with appropriate responses
    RUN each pipeline stage in sequence
    ASSERT files created at each stage
    ASSERT final judgment database exists
```

### 3.3 Integration Tests (test_integration.py)
Test the complete pipeline:

```pseudocode
CLASS TestFullPipeline:
  FUNCTION test_complete_pipeline():
    CREATE temporary directory
    MOCK all LLM API calls with realistic responses
    
    # Stage 1: Ideas
    RUN generate_ideas.py with mocked args
    ASSERT ideas.json created
    
    # Stage 2: Contexts  
    RUN generate_context.py with ideas file
    ASSERT contexts file created
    
    # Stage 3: Conversations
    RUN generate_conversations.py with contexts
    ASSERT database file created
    
    # Stage 4: Judgments
    RUN judge_conversations.py with database
    ASSERT judgment results created
    
    ASSERT complete pipeline works end-to-end
```

## Phase 4: Cleanup & Configuration

### 4.1 Remove generate_insights.py
```bash
rm generate_insights.py  # Replace with new judgment system
```

### 4.2 Update requirements.txt
```
ADD: pytest>=7.0.0, flake8>=4.0.0
```

### 4.3 Add flake8 configuration
```ini
# .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = __pycache__,*.egg-info,dist,build
```

### 4.4 Create run scripts
```bash
# run_evaluation_pipeline.sh
PSEUDOCODE:
  SET configuration variables (system_prompt, batch_size, total_ideas, pages, topic, etc.)
  CREATE timestamp directory
  RUN generate_ideas.py with config (including optional topic)
  RUN generate_context.py with ideas file
  RUN generate_conversations.py with contexts
  RUN judge_conversations.py with database
  ECHO completion message with results location
```

## Implementation Order

1. **Phase 1**: Set up data models and database schema
2. **Phase 2.1**: Implement `generate_ideas.py`
3. **Phase 2.2**: Implement `generate_context.py` 
4. **Phase 2.3**: Update `generate_conversations.py`
5. **Phase 2.4**: Implement `judge_conversations.py`
6. **Phase 3**: Add UI integration and testing
7. **Phase 4**: Cleanup and configuration

Each phase should be implemented and tested before moving to the next. The modular design allows for independent development and testing of each component.

## Key Implementation Details

### Configurable Parameters
- **Batch sizes**: 3 and 10 (configurable via command line)
- **Context pages**: n-page documents (configurable)
- **Topic**: Optional topic focus for idea generation
- **Models**: Claude 4 Sonnet for all AI operations
- **Output locations**: `evaluation_data/[timestamp]` directories

### ELO Comparison Efficiency
- **Batch Processing**: Single API call evaluates all conversations for a trait simultaneously
- **Ranking System**: Returns ranked list with scores instead of pairwise comparisons
- **Reduced API Calls**: O(traits) instead of O(traits × conversations²)
- **JSON Format**: `{rankings: [{conversation_id, rank, score}], reasoning}`

### Error Handling
- API timeout handling (30 seconds)
- JSON parsing with fallbacks
- Database connection error handling
- File I/O error handling

### Data Organization
- Clear separation of concerns between components
- Timestamped output directories
- Configuration metadata saved with results
- Database foreign key relationships maintained

### UI Features
- **Three-tab interface**: Chat, Analysis, Evaluations
- **Evaluation Dashboard**: Comprehensive visualization of evaluation results
- **Summary View**: Cross-model trait comparison with radar charts and bar graphs
- **Individual Results**: Detailed breakdown per filepath/model with:
  - Overall score metrics
  - Trait-specific radar charts
  - Score distribution histograms
  - ELO ranking visualizations
- **Interactive Elements**: 
  - Expandable sections for detailed reasoning
  - Filterable trait comparisons
  - Sortable leaderboards
- **Chart Types**:
  - Radar charts for trait profiles
  - Bar charts for cross-model comparison
  - Histograms for score distributions
  - Ranking charts for ELO results
- **Integration**: Seamless integration with existing chat and analysis features