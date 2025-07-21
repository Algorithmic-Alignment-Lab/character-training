import json
import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for
import markdown
from markupsafe import Markup

app = Flask(__name__)

# Add markdown filter
@app.template_filter('markdown')
def markdown_filter(text):
    """Convert markdown text to HTML"""
    if not text:
        return ""
    return Markup(markdown.markdown(text, extensions=['nl2br']))

# Path to conversations directory
CONVERSATIONS_DIR = Path(__file__).parent.parent / "conversations"

def get_conversation_files():
    """Get all JSON files in the conversations directory"""
    if not CONVERSATIONS_DIR.exists():
        return []
    return [f.name for f in CONVERSATIONS_DIR.glob("*.json")]

def load_conversation(filename):
    """Load conversation data from JSON file"""
    try:
        with open(CONVERSATIONS_DIR / filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None

@app.route('/')
def index():
    """Home page showing list of available conversation files"""
    files = get_conversation_files()
    return render_template('index.html', files=files)

@app.route('/conversation/<filename>')
def view_conversation(filename):
    """View specific conversation file"""
    if not filename.endswith('.json'):
        filename += '.json'
    
    conversation_data = load_conversation(filename)
    if conversation_data is None:
        return "Conversation not found or could not be loaded", 404
    
    return render_template('conversation.html', 
                         filename=filename, 
                         data=conversation_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8555)