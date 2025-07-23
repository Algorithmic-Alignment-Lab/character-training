### **Updated Plan: Character Evaluation Synthetic Generation & Analysis**

This plan outlines the implementation of a robust, modular, and extensible framework for synthetically generating character-driven conversations and evaluating them against the six core metrics defined in `character_evaluation_plan.md`.

The framework will prioritize clear abstractions, human-readable code, and integration with the existing `evals` infrastructure, using JSON for data storage and the `evals/webapp` for visualization.

---

### **Phase 1: Core Infrastructure & Synthetic Conversation Generation**

**Goal:** Establish a modular foundation for generating synthetic conversations. This logic will be separated from the evaluation pipeline for clarity and reusability.

1.  **Create a New Directory for Synthetic Generation:**

    - Create `evals/synthetic_generation/` to house all code related to data generation.

2.  **Structured Character Definitions:**

    - **File:** `evals/synthetic_generation/character_definitions.json`
    - **Purpose:** Move beyond simple prompts to structured character profiles. This allows for more nuanced generation and evaluation.
    - **Structure:**
      ```json
      {
        "interviewer_v2_jasmine": {
          "name": "Jasmine",
          "archetype": "Empathetic Interviewer",
          "system_prompt": "You are Jasmine, an interviewer who is curious, professional, and empathetic...",
          "traits": ["curiosity", "professionalism", "empathy"]
        }
        // ... other characters
      }
      ```

3.  **Abstracted Conversation Generation:**
    - **File:** `evals/synthetic_generation/conversation_generator.py`
    - **Purpose:** A clean, reusable script to generate conversations based on a character and a scenario.
    - **Implementation:**
      - Define a `ConversationGenerator` class.
      - The class will take a character profile (from `character_definitions.json`) and a scenario description as input.
      - It will orchestrate a multi-turn conversation between two LLM agents.
      - It will leverage the existing `llm_api.py` for model inference.
      - **Output:** A structured JSON file representing the full conversation, including speaker, message content, and any internal "thinking" steps. Example: `conversation_log.json`.

---

### **Phase 2: Modular Evaluation Framework**

**Goal:** Implement each of the six evaluation metrics as a distinct, pluggable module.

1.  **Create a New Directory for Evaluators:**

    - Create `evals/evaluation_framework/` to hold the evaluation logic.

2.  **Base Evaluator Class:**

    - **File:** `evals/evaluation_framework/base_evaluator.py`
    - **Purpose:** Define a common interface for all evaluators.
    - **Implementation:**

      ```python
      from abc import ABC, abstractmethod

      class BaseEvaluator(ABC):
          def __init__(self, judge_model):
              self.judge_model = judge_model

          @abstractmethod
          def evaluate(self, conversation_log: dict) -> dict:
              """Evaluates a conversation and returns a JSON-serializable result."""
              pass
      ```

3.  **Implement Individual Metric Evaluators:**
    - **Files:** Create one file per metric in `evals/evaluation_framework/`:
      - `trait_adherence_evaluator.py`
      - `behavioral_predictability_evaluator.py`
      - `reasoning_authenticity_evaluator.py`
      - `engagement_quality_evaluator.py`
      - `long_term_consistency_evaluator.py`
      - `context_retention_evaluator.py`
    - **Implementation:**
      - Each file will contain a class that inherits from `BaseEvaluator`.
      - Each class will implement the `evaluate` method, using an LLM judge to analyze the `conversation_log.json`.
      - The judge will be prompted with specific criteria related to its metric (e.g., "Rate the assistant's adherence to the 'curiosity' trait on a 1-7 scale.").
      - **Output:** Each evaluator will return a JSON object with its score, a detailed rationale from the judge, and any relevant quotes.

---

### **Phase 3: Orchestration and Integration**

**Goal:** Connect the generation and evaluation components and integrate them into the existing `long_context_eval.py` workflow.

1.  **Update the Orchestrator:**
    - **File:** `evals/long_context_eval.py`
    - **Purpose:** Refactor this file to serve as the main entry point for running an end-to-end evaluation.
    - **Implementation:**
      1.  **Setup:** Initialize the `ConversationGenerator` and all `Evaluator` classes.
      2.  **Generation:** Call the generator to produce the `conversation_log.json`.
      3.  **Evaluation:** Loop through the list of evaluators, passing the `conversation_log.json` to each one.
      4.  **Aggregation:** Collect the JSON results from each evaluator.
      5.  **Output:** Combine all results into a single, comprehensive JSON file for the entire run, saved to a timestamped directory (e.g., `evals/results/run_20250723_150000/evaluation_summary.json`).

---

### **Phase 4: Visualization & Dashboard Integration**

**Goal:** Display the evaluation results in a user-friendly dashboard within the existing web application.

1.  **Integrate with the Webapp:**
    - **File:** `evals/webapp/app.py`
    - **Purpose:** Add new functionality to the existing Streamlit/Flask application to visualize evaluation results.
    - **Implementation:**
      1.  **Data Loading:** Add a file browser to select a run's `evaluation_summary.json` from the `evals/results/` directory. This file will contain both the full conversation log and all associated evaluation results.
      2.  **Summary View:** Create a main dashboard page that shows the aggregate scores for all six metrics for the selected run.
      3.  **Detailed Drill-Downs:** For each metric, create a separate tab or section that displays:
          - The Likert score.
          - The judge's detailed reasoning.
          - Charts visualizing the data (e.g., trait scores over time for consistency).
          - **Full Conversation View:** Display the entire conversation log, with the specific passages referenced by the judge highlighted or clearly linked.

---

### **Phase 5: Validation and Refinement**

**Goal:** Ensure the evaluation framework is reliable, accurate, and improves over time.

1.  **Human-in-the-Loop Validation:**

    - **Process:** Periodically, have human experts evaluate a subset of the generated conversations using the same criteria as the LLM judges.
    - **Analysis:** Compare the human scores to the LLM judge scores to identify biases, inaccuracies, or areas where the judging prompts need refinement.

2.  **Iterative Improvement:**
    - **Process:** Establish a feedback loop where insights from validation and dashboard analysis are used to improve the character definitions, scenario generation, and evaluator prompts.
