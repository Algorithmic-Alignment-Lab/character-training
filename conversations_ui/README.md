# LLM Persona Evaluator

This Streamlit application provides a user interface for evaluating and comparing the performance of different Large Language Models (LLMs) in adopting specific personas. It allows for side-by-side comparison of two different model/persona configurations, isolated test runs, and conversation history browsing.

## Features

- **Side-by-Side Comparison**: View two chat windows simultaneously to compare different models or system prompts.
- **Flexible Model Selection**: Supports models from Anthropic, OpenAI, and OpenRouter.
- **Persona Management**: Personas (defined by system prompts) are loaded from an external `system_prompts.json` file.
- **Isolated Test Runs**: Each test scenario can be run in its own temporary database, preventing interference between tests.
- **Conversation History**: Browse and load conversations from a main database or any of the run-specific databases.
- **Data Export**: Test runs automatically generate CSV exports for analysis.
- **Unified Controls**: A "Side-by-Side Mode" toggle syncs the chat input and conversation controls for easier comparison.

## Project Structure

```
conversations_ui/
├── conversations.db        # Main database for conversations
├── database.py             # Handles all database interactions
├── generate_conversations.py # Script for programmatic conversation generation
├── llm_api.py              # Wrapper for making calls to various LLM APIs
├── README.md               # This file
├── requirements.txt        # Python package dependencies
├── run_scenarios.py        # Main script to execute a test run
├── streamlit_chat.py       # The core Streamlit UI application
├── system_prompts.json     # Definions for all personas
└── results/
    ├── run_YYYYMMDD_HHMMSS.db  # Database for a specific test run
    └── failure_modes_YYYYMMDD_HHMMSS.csv # Analysis CSV for a run
```

## Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd lab-character-training/conversations_ui
    ```

2.  **Create and activate a virtual environment** (recommended):

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required packages:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up API Keys**: This application uses `litellm` to manage API calls, which means you need to set the appropriate environment variables for the services you want to use (OpenAI, Anthropic, etc.).

    For example:

    ```bash
    export OPENAI_API_KEY="your_openai_api_key"
    export ANTHROPIC_API_KEY="your_anthropic_api_key"
    ```

## How to Run

### 1. Running the Interactive UI

To start the main Streamlit application, run the following command in your terminal from the `conversations_ui` directory:

```bash
streamlit run streamlit_chat.py
```

This will open the application in your web browser. From the UI, you can:

- Select a database (the main one or a specific test run) from the sidebar.
- Choose a model and a persona for each of the two chat columns.
- Enable "Side-by-Side Mode" for unified control.
- Start new conversations or load existing ones from the selected database.

### 2. Running a Test Scenario

To perform a programmatic test run (which generates conversations and analysis), use the `run_scenarios.py` script. This will create a new timestamped database and CSV file in the `results/` directory.

```bash
python run_scenarios.py
```

You can then view the results of this run in the Streamlit UI by selecting the corresponding database from the sidebar.
