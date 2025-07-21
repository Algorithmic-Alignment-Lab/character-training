# Conversation Viewer Webapp

A simple Flask webapp to browse and inspect conversation JSON files from the evals/conversations directory.

## Setup

1. Install Flask:
   ```bash
   pip install flask
   ```

## Running the webapp

1. Navigate to the webapp directory:
   ```bash
   cd evals/webapp
   ```

2. Start the Flask development server:
   ```bash
   python app.py
   ```

3. Open your browser and go to:
   ```
   http://localhost:8555
   ```

## Features

- **File Selection**: Home page lists all available JSON conversation files
- **Conversation Inspection**: Click on any file to view its contents
- **Collapsible Interface**: Each conversation can be expanded/collapsed
- **Message Display**: Shows system, user, and assistant messages with distinct styling
- **Metadata View**: Displays conversation metadata including models and system prompts

## File Structure

```
webapp/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── templates/
│   ├── base.html      # Base template with styles and JavaScript
│   ├── index.html     # File selection page
│   └── conversation.html # Conversation display page
└── README.md          # This file
```