#!/usr/bin/env python3
"""
Unified web interface for browsing universe contexts and synthetic documents.
"""
import os
import json
import html
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import quote, unquote

from flask import Flask, render_template_string, request, jsonify, url_for, send_file, abort

# Optional markdown import
try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False
    def markdown_fallback(text, extensions=None):
        # Simple fallback - just return text with newlines as <br> tags
        return text.replace('\n', '<br>')

app = Flask(__name__)

# Base paths
BASE_OUTPUT_PATH = Path("/Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/output")

# Internal helper functions to replace external module dependencies
def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def list_dir(path: Path) -> List[Dict[str, Any]]:
    """List directory contents with file info including sizes."""
    items = []
    try:
        for item in sorted(path.iterdir()):
            item_info = {
                'name': item.name,
                'is_dir': item.is_dir(),
                'path': item,
                'size': None
            }
            
            if item.is_file():
                try:
                    size_bytes = item.stat().st_size
                    item_info['size'] = format_file_size(size_bytes)
                except:
                    pass
            
            items.append(item_info)
    except Exception as e:
        print(f"Error listing directory {path}: {e}")
        return []
    
    return items

def read_file(file_path: Path, max_size: int = 10000) -> str:
    """Read file content as text, with size limiting."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content) > max_size:
                content = content[:max_size] + "\n\n... (truncated)"
            return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

def get_breadcrumb_parts(path: str) -> List[Dict[str, str]]:
    """Generate breadcrumb navigation parts."""
    if not path:
        return []
    
    parts = []
    path_parts = path.split('/')
    current_path = ""
    
    for part in path_parts:
        if part:
            current_path = f"{current_path}/{part}" if current_path else part
            parts.append({
                'name': part,
                'path': current_path
            })
    
    return parts

def validate_path_security(path: str, base_path: Path) -> tuple[Path, str]:
    """Validate and resolve a path, ensuring it stays within base_path.
    
    Returns:
        tuple: (resolved_path, error_message) - error_message is empty string if valid
    """
    try:
        # Clean and decode the path
        path = unquote(path) if path else ''
        current_path = base_path / path if path else base_path
        
        # Resolve the path to check for directory traversal attacks
        resolved_path = current_path.resolve()
        base_resolved = base_path.resolve()
        
        # Security check - ensure we stay within base_path
        if not str(resolved_path).startswith(str(base_resolved)):
            return resolved_path, "Access denied: Path outside allowed directory"
        
        return resolved_path, ""
    except Exception:
        return base_path, "Invalid path"

def parse_universe_context_file(file_path: Path) -> List[Dict[str, Any]]:
    """Parse a JSONL file containing universe context data."""
    try:
        universe_data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 10:  # Limit to first 10 lines for display
                    break
                try:
                    data = json.loads(line.strip())
                    
                    # Convert universe_context markdown to HTML
                    universe_context = data.get('universe_context', '')
                    if HAS_MARKDOWN:
                        universe_context_html = markdown.markdown(universe_context, extensions=['nl2br'])
                    else:
                        universe_context_html = markdown_fallback(universe_context)
                    
                    # Extract key fields
                    parsed_item = {
                        'id': data.get('id', 'Unknown'),
                        'universe_context_html': universe_context_html,
                        'key_facts': data.get('key_facts', []),
                        'is_true': data.get('is_true', None),
                        'tags': data.get('tags', [])
                    }
                    universe_data.append(parsed_item)
                except json.JSONDecodeError:
                    # If JSON parsing fails, return None to fall back to raw display
                    return None
        return universe_data
    except Exception as e:
        return None

def read_jsonl_file(file_path: Path) -> str:
    """Read and format a JSONL file for display (fallback for non-universe-context files)."""
    try:
        content_lines = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 10:  # Limit to first 10 lines for display
                    content_lines.append("... (truncated, showing first 10 lines)")
                    break
                try:
                    data = json.loads(line.strip())
                    content_lines.append(json.dumps(data, indent=2, ensure_ascii=False))
                except json.JSONDecodeError:
                    content_lines.append(f"Invalid JSON: {line.strip()}")
        return '\n\n'.join(content_lines)
    except Exception as e:
        return f"Error reading file: {str(e)}"

def render_json_content(file_path: Path) -> str:
    """Render JSON file as pretty-printed, syntax-highlighted HTML."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Pretty print with indentation and return as HTML-escaped content
        pretty_json = json.dumps(data, indent=2, ensure_ascii=False)
        return html.escape(pretty_json)
    except json.JSONDecodeError as e:
        return html.escape(f"Invalid JSON: {str(e)}")
    except Exception as e:
        return html.escape(f"Error reading JSON file: {str(e)}")

def render_jsonl_content(file_path: Path) -> str:
    """Render JSONL file by splitting lines and pretty-printing each JSON object."""
    try:
        content_lines = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 50:  # Limit to first 50 lines for display
                    content_lines.append("... (truncated, showing first 50 lines)")
                    break
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        pretty_json = json.dumps(data, indent=2, ensure_ascii=False)
                        content_lines.append(html.escape(pretty_json))
                    except json.JSONDecodeError:
                        content_lines.append(html.escape(f"Invalid JSON: {line}"))
        return '\n\n'.join(content_lines)
    except Exception as e:
        return html.escape(f"Error reading JSONL file: {str(e)}")

def render_image_content(file_path: Path, subpath: str) -> str:
    """Render image as embedded HTML img tag using Flask's send_file route."""
    try:
        # Create image tag that uses the serve_file route
        img_url = url_for('serve_image', subpath=subpath)
        return f'<img src="{img_url}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px;" alt="{html.escape(file_path.name)}"/>'
    except Exception as e:
        return html.escape(f"Error displaying image: {str(e)}")

def render_text_content(file_path: Path, max_size: int = 50000) -> str:
    """Render text files (.py, .txt, unknown text) with basic HTML escaping."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content) > max_size:
                content = content[:max_size] + "\n\n... (truncated)"
        return html.escape(content)
    except UnicodeDecodeError:
        # File might be binary, return error message
        return html.escape("Cannot display file: appears to be binary data")
    except Exception as e:
        return html.escape(f"Error reading file: {str(e)}")

def render_file_content_html(file_path: Path, subpath: str = "") -> tuple[str, bool]:
    """Render file content as HTML based on file type.
    
    Returns:
        tuple: (html_content, is_inline_displayable)
            - html_content: HTML string to display
            - is_inline_displayable: whether content can be displayed inline (not just download)
    """
    suffix = file_path.suffix.lower()
    
    # JSON files - pretty-printed, syntax-highlighted
    if suffix == '.json':
        return render_json_content(file_path), True
    
    # JSONL files - split lines, pretty-print each JSON object
    elif suffix == '.jsonl':
        return render_jsonl_content(file_path), True
    
    # Image files - serve via send_file and embed img tag
    elif suffix in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
        return render_image_content(file_path, subpath), True
    
    # Python and text files - show in <pre> with basic HTML escaping
    elif suffix in ['.py', '.txt', '.md', '.yml', '.yaml', '.csv', '.log', '.sh', '.bash'] or suffix == '':
        return render_text_content(file_path), True
    
    # Fallback - binary or unknown files - provide download link only
    else:
        return f"<p>Binary file - cannot display content inline. <a href=\"{url_for('serve_file', subpath=subpath)}\" target=\"_blank\">📥 Download to view</a></p>", False

# Universe Browser Template
UNIVERSE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Universe Context Browser</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .breadcrumb { background: #e9ecef; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
        .breadcrumb a { color: #007bff; text-decoration: none; margin-right: 5px; }
        .breadcrumb a:hover { text-decoration: underline; }
        .file-list { list-style: none; padding: 0; }
        .file-item { padding: 8px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .file-item:hover { background: #f8f9fa; }
        .file-item a { text-decoration: none; color: #333; font-weight: 500; }
        .file-item a:hover { color: #007bff; }
        .folder { color: #007bff; }
        .folder::before { content: "📁 "; }
        .file::before { content: "📄 "; }
        .file-size { color: #666; font-size: 0.9em; }
        .content-viewer { margin-top: 20px; }
        .json-content { background: #f8f9fa; padding: 15px; border-radius: 4px; border: 1px solid #dee2e6; white-space: pre-wrap; font-family: monospace; max-height: 500px; overflow-y: auto; }
        .universe-context { margin: 20px 0; }
        .context-header { background: #e3f2fd; padding: 15px; border-radius: 8px 8px 0 0; border-bottom: 2px solid #1976d2; }
        .context-id { font-size: 1.4em; font-weight: bold; color: #1976d2; margin-bottom: 5px; }
        .context-truth { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.9em; font-weight: bold; }
        .truth-true { background: #c8e6c9; color: #2e7d32; }
        .truth-false { background: #ffcdd2; color: #c62828; }
        .context-content { background: white; padding: 20px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 8px 8px; }
        .context-content h1, .context-content h2, .context-content h3 { color: #333; margin-top: 20px; margin-bottom: 10px; }
        .context-content h1 { border-bottom: 2px solid #1976d2; padding-bottom: 5px; }
        .context-content p { line-height: 1.6; margin-bottom: 15px; }
        .context-content ul, .context-content ol { margin-bottom: 15px; padding-left: 20px; }
        .context-content li { margin-bottom: 5px; }
        .key-facts { margin-top: 20px; }
        .key-facts h3 { color: #1976d2; margin-bottom: 10px; }
        .fact-list { list-style: none; padding: 0; counter-reset: fact-counter; }
        .fact-item { background: #f8f9fa; margin-bottom: 8px; padding: 10px; border-left: 4px solid #1976d2; border-radius: 0 4px 4px 0; counter-increment: fact-counter; position: relative; }
        .fact-item::before { content: counter(fact-counter) ". "; font-weight: bold; color: #1976d2; }
        .tags { margin-top: 15px; }
        .tag { display: inline-block; background: #e0e0e0; color: #555; padding: 4px 8px; margin: 2px; border-radius: 12px; font-size: 0.85em; }
        .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 4px; margin: 10px 0; }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .back-link { margin-bottom: 20px; }
        .back-link a { color: #007bff; text-decoration: none; }
        .back-link a:hover { text-decoration: underline; }
        .home-link { margin-bottom: 10px; }
        .home-link a { color: #28a745; text-decoration: none; font-weight: bold; }
        .home-link a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <div class="home-link">
            <a href="{{ url_for('index') }}">🏠 Home</a>
        </div>
        <h1>Universe Context Browser</h1>
        
        {% if current_path != '' %}
        <div class="back-link">
            <a href="{{ url_for('universe_browse', path=parent_path) }}">← Back to {{ parent_name or 'Root' }}</a>
        </div>
        {% endif %}
        
        <div class="breadcrumb">
            <a href="{{ url_for('universe_browse') }}">🏠 Universes</a>
            {% for part in breadcrumb_parts %}
            / <a href="{{ url_for('universe_browse', path=part['path']) }}">{{ part['name'] }}</a>
            {% endfor %}
        </div>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        {% if items %}
        <ul class="file-list">
            {% for item in items %}
            <li class="file-item">
                <a href="{{ url_for('universe_browse', path=item['url_path']) }}" class="{{ 'folder' if item['is_dir'] else 'file' }}">
                    {{ item['name'] }}
                </a>
                {% if not item['is_dir'] and item['size'] %}
                <span class="file-size">{{ item['size'] }}</span>
                {% endif %}
            </li>
            {% endfor %}
        </ul>
        {% endif %}
        
        {% if universe_data %}
        <div class="content-viewer">
            {% for item in universe_data %}
            <div class="universe-context">
                <div class="context-header">
                    <div class="context-id">{{ item.id }}</div>
                    <span class="context-truth {{ 'truth-true' if item.is_true else 'truth-false' }}">
                        {{ 'TRUE' if item.is_true else 'FALSE' }}
                    </span>
                    {% if item.tags %}
                    <div class="tags">
                        {% for tag in item.tags %}
                        <span class="tag">{{ tag }}</span>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>
                <div class="context-content">
                    {{ item.universe_context_html | safe }}
                    
                    {% if item.key_facts %}
                    <div class="key-facts">
                        <h3>Key Facts</h3>
                        <ul class="fact-list">
                            {% for fact in item.key_facts %}
                            <li class="fact-item">{{ fact }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
        {% elif file_content %}
        <div class="content-viewer">
            <h3>Content of {{ current_file }}</h3>
            <div class="json-content">{{ file_content }}</div>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

def render_universe_browse(path: str, base_path: Path):
    """Browse universe contexts with file listing and content viewing."""
    # Clean and decode the path
    path = unquote(path) if path else ''
    current_path = base_path / path if path else base_path
    
    # Security check - ensure we stay within base_path
    try:
        current_path = current_path.resolve()
        if not str(current_path).startswith(str(base_path.resolve())):
            return render_template_string(UNIVERSE_TEMPLATE, 
                error="Access denied: Path outside allowed directory",
                current_path=path,
                breadcrumb_parts=[],
                items=[],
                file_content=None,
                universe_data=None)
    except Exception:
        return render_template_string(UNIVERSE_TEMPLATE, 
            error="Invalid path",
            current_path=path,
            breadcrumb_parts=[],
            items=[],
            file_content=None,
            universe_data=None)
    
    # Check if path exists
    if not current_path.exists():
        return render_template_string(UNIVERSE_TEMPLATE, 
            error=f"Path not found: {path}",
            current_path=path,
            breadcrumb_parts=get_breadcrumb_parts(path),
            items=[],
            file_content=None,
            universe_data=None)
    
    # Handle file vs directory
    if current_path.is_file():
        # Display file content
        file_content = None
        universe_data = None
        current_file = current_path.name
        
        if current_path.suffix.lower() == '.jsonl':
            # Try to parse as universe context data first
            universe_data = parse_universe_context_file(current_path)
            if universe_data is None:
                # Fall back to raw JSON display
                file_content = read_jsonl_file(current_path)
        else:
            file_content = read_file(current_path)
        
        # Get parent path for navigation
        parent_path = ''
        parent_name = None
        if current_path.parent != base_path and base_path in current_path.parent.parents:
            parent_path = str(current_path.parent.relative_to(base_path))
            parent_name = current_path.parent.name
        
        return render_template_string(UNIVERSE_TEMPLATE,
            current_path=path,
            parent_path=parent_path,
            parent_name=parent_name,
            breadcrumb_parts=get_breadcrumb_parts(path),
            items=[],
            file_content=file_content,
            universe_data=universe_data,
            current_file=current_file,
            error=None)
    
    # Directory listing
    items = []
    try:
        for item in sorted(current_path.iterdir()):
            relative_path = item.relative_to(base_path)
            url_path = quote(str(relative_path))
            
            item_info = {
                'name': item.name,
                'is_dir': item.is_dir(),
                'url_path': url_path,
                'size': None
            }
            
            if item.is_file():
                try:
                    size_bytes = item.stat().st_size
                    item_info['size'] = format_file_size(size_bytes)
                except:
                    pass
            
            items.append(item_info)
    except Exception as e:
        return render_template_string(UNIVERSE_TEMPLATE, 
            error=f"Error reading directory: {str(e)}",
            current_path=path,
            breadcrumb_parts=get_breadcrumb_parts(path),
            items=[],
            file_content=None,
            universe_data=None)
    
    # Get parent path for navigation
    parent_path = ''
    parent_name = None
    if current_path.parent != base_path and base_path in current_path.parent.parents:
        parent_path = str(current_path.parent.relative_to(base_path))
        parent_name = current_path.parent.name
    
    return render_template_string(UNIVERSE_TEMPLATE,
        current_path=path,
        parent_path=parent_path,
        parent_name=parent_name,
        breadcrumb_parts=get_breadcrumb_parts(path),
        items=items,
        file_content=None,
        universe_data=None,
        error=None)

# Simple synthetic docs browser implementation
def render_synth_docs_browse(path: str, base_path: Path):
    """Simple synthetic documents browser - just displays files for now."""
    # Clean and decode the path
    path = unquote(path) if path else ''
    current_path = base_path / path if path else base_path
    
    # Security check
    try:
        current_path = current_path.resolve()
        if not str(current_path).startswith(str(base_path.resolve())):
            return render_template_string(UNIVERSE_TEMPLATE, 
                error="Access denied: Path outside allowed directory",
                current_path=path,
                breadcrumb_parts=[],
                items=[])
    except Exception:
        return render_template_string(UNIVERSE_TEMPLATE, 
            error="Invalid path",
            current_path=path,
            breadcrumb_parts=[],
            items=[])
    
    # Check if path exists
    if not current_path.exists():
        return render_template_string(UNIVERSE_TEMPLATE, 
            error=f"Path not found: {path}",
            current_path=path,
            breadcrumb_parts=get_breadcrumb_parts(path),
            items=[])
    
    # For now, just list files like the universe browser
    if current_path.is_file():
        file_content = read_file(current_path)
        
        parent_path = ''
        parent_name = None
        if current_path.parent != base_path and base_path in current_path.parent.parents:
            parent_path = str(current_path.parent.relative_to(base_path))
            parent_name = current_path.parent.name
        
        return render_template_string(UNIVERSE_TEMPLATE,
            current_path=path,
            parent_path=parent_path,
            parent_name=parent_name,
            breadcrumb_parts=get_breadcrumb_parts(path),
            items=[],
            file_content=file_content,
            universe_data=None,
            current_file=current_path.name,
            error=None)
    
    # Directory listing
    items = []
    try:
        for item in sorted(current_path.iterdir()):
            relative_path = item.relative_to(base_path)
            url_path = quote(str(relative_path))
            
            item_info = {
                'name': item.name,
                'is_dir': item.is_dir(),
                'url_path': url_path,
                'size': None
            }
            
            if item.is_file():
                try:
                    size_bytes = item.stat().st_size
                    item_info['size'] = format_file_size(size_bytes)
                except:
                    pass
            
            items.append(item_info)
    except Exception as e:
        return render_template_string(UNIVERSE_TEMPLATE, 
            error=f"Error reading directory: {str(e)}",
            current_path=path,
            breadcrumb_parts=get_breadcrumb_parts(path),
            items=[])
    
    parent_path = ''
    parent_name = None
    if current_path.parent != base_path and base_path in current_path.parent.parents:
        parent_path = str(current_path.parent.relative_to(base_path))
        parent_name = current_path.parent.name
    
    return render_template_string(UNIVERSE_TEMPLATE,
        current_path=path,
        parent_path=parent_path,
        parent_name=parent_name,
        breadcrumb_parts=get_breadcrumb_parts(path),
        items=items,
        file_content=None,
        universe_data=None,
        error=None)

# Simple stub implementations for eval results and honeypot browsers
def render_eval_results_browse(path: str, base_path: Path):
    """Simple eval results browser stub - uses same template as universe browser."""
    return render_synth_docs_browse(path, base_path)

def render_honeypot_results_browse(path: str, base_path: Path):
    """Simple honeypot results browser stub - uses same template as universe browser."""
    return render_synth_docs_browse(path, base_path)

# Generic Browser Template (similar to Universe template but more generic)
GENERIC_BROWSER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }} - File Browser</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .breadcrumb { background: #e9ecef; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
        .breadcrumb a { color: #007bff; text-decoration: none; margin-right: 5px; }
        .breadcrumb a:hover { text-decoration: underline; }
        .file-list { list-style: none; padding: 0; }
        .file-item { padding: 8px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .file-item:hover { background: #f8f9fa; }
        .file-item a { text-decoration: none; color: #333; font-weight: 500; }
        .file-item a:hover { color: #007bff; }
        .folder { color: #007bff; }
        .folder::before { content: "📁 "; }
        .file::before { content: "📄 "; }
        .image::before { content: "🖼️ "; }
        .json::before { content: "📋 "; }
        .python::before { content: "🐍 "; }
        .file-size { color: #666; font-size: 0.9em; }
        .content-viewer { margin-top: 20px; }
        .file-content { background: #f8f9fa; padding: 15px; border-radius: 4px; border: 1px solid #dee2e6; white-space: pre-wrap; font-family: monospace; max-height: 500px; overflow-y: auto; }
        .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 4px; margin: 10px 0; }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .back-link { margin-bottom: 20px; }
        .back-link a { color: #007bff; text-decoration: none; }
        .back-link a:hover { text-decoration: underline; }
        .home-link { margin-bottom: 10px; }
        .home-link a { color: #28a745; text-decoration: none; font-weight: bold; }
        .home-link a:hover { text-decoration: underline; }
        .download-link { margin-left: 10px; }
        .download-link a { background: #28a745; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 0.8em; }
        .download-link a:hover { background: #218838; }
    </style>
</head>
<body>
    <div class="container">
        <div class="home-link">
            <a href="{{ url_for('index') }}">🏠 Home</a>
        </div>
        <h1>{{ title }}</h1>
        
        {% if current_path != '' %}
        <div class="back-link">
            <a href="{{ url_for('generic_browse', subpath=parent_path) }}">← Back to {{ parent_name or 'Root' }}</a>
        </div>
        {% endif %}
        
        <div class="breadcrumb">
            <a href="{{ url_for('generic_browse') }}">🏠 Output</a>
            {% for part in breadcrumb_parts %}
            / <a href="{{ url_for('generic_browse', subpath=part['path']) }}">{{ part['name'] }}</a>
            {% endfor %}
        </div>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        {% if items %}
        <ul class="file-list">
            {% for item in items %}
            <li class="file-item">
                <a href="{{ url_for('generic_browse', subpath=item['url_path']) }}" class="{{ item['css_class'] }}">
                    {{ item['name'] }}
                </a>
                <div>
                    {% if not item['is_dir'] and item['size'] %}
                    <span class="file-size">{{ item['size'] }}</span>
                    {% endif %}
                    {% if not item['is_dir'] %}
                    <span class="download-link">
                        <a href="{{ url_for('serve_file', subpath=item['url_path']) }}" target="_blank">📥 Download</a>
                    </span>
                    {% endif %}
                </div>
            </li>
            {% endfor %}
        </ul>
        {% endif %}
        
        {% if file_content %}
        <div class="content-viewer">
            <h3>Content of {{ current_file }}
                {% if not is_binary %}
                <span class="download-link">
                    <a href="{{ url_for('serve_file', subpath=current_path) }}" target="_blank">📥 Download</a>
                </span>
                {% endif %}
            </h3>
            {% if is_binary %}
                <p>Binary file - cannot display content. Use download link to view.</p>
            {% else %}
                {% set is_image = current_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')) %}
                {% if is_image %}
                    <div class="file-content">{{ file_content | safe }}</div>
                {% else %}
                    <div class="file-content">{{ file_content }}</div>
                {% endif %}
            {% endif %}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

MAIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Science Synth Facts Browser</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .nav-section { background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }
        .nav-link { display: inline-block; padding: 15px 30px; margin: 10px; background: #1976d2; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; }
        .nav-link:hover { background: #1565c0; color: white; }
        .description { color: #666; margin-top: 10px; font-size: 0.9em; }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; text-align: center; }
        .stats { display: flex; justify-content: space-around; margin: 20px 0; }
        .stat-box { background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; border: 1px solid #dee2e6; }
        .stat-number { font-size: 1.5em; font-weight: bold; color: #007bff; }
        .stat-label { color: #666; font-size: 0.9em; }
        .generic-browse { background: #e8f5e8; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Science Synth Facts Browser</h1>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{{ character_stats.folders }}</div>
                <div class="stat-label">Character Folders</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ file_stats.json }}</div>
                <div class="stat-label">JSON Files</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ file_stats.jsonl }}</div>
                <div class="stat-label">JSONL Files</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ file_stats.images }}</div>
                <div class="stat-label">Images</div>
            </div>
        </div>
        
        <div class="nav-section generic-browse">
            <h2>Generic File Browser</h2>
            <a href="{{ url_for('generic_browse') }}" class="nav-link">📁 Browse All Files</a>
            <div class="description">
                Browse all files and directories within the output folder. Navigate freely through
                the entire file system with security restrictions to stay within the allowed directory.
            </div>
        </div>
        
        <div class="nav-section">
            <h2>Browse Universe Contexts</h2>
            <a href="{{ url_for('universe_browse') }}" class="nav-link">Universe Contexts</a>
            <div class="description">
                Browse alternative universe contexts with false facts used for belief implantation research.
                View JSONL files with structured metadata and markdown content.
            </div>
        </div>
        
        <div class="nav-section">
            <h2>Browse Synthetic Documents</h2>
            <a href="{{ url_for('synth_docs_browse') }}" class="nav-link">Synthetic Documents</a>
            <div class="description">
                Explore synthetic documents generated from universe contexts. 
                Filter by document type, ideas, and facts. Paginated view for large document sets.
            </div>
        </div>
        
        <div class="nav-section">
            <h2>Browse Evaluation Results</h2>
            <a href="{{ url_for('eval_results_browse') }}" class="nav-link">Evaluation Results</a>
            <div class="description">
                View degree of belief evaluation results with metrics, sample responses, and detailed breakdowns.
                Handles different evaluation formats gracefully with structured display.
            </div>
        </div>
        
        <div class="nav-section">
            <h2>Browse Honeypot Results</h2>
            <a href="{{ url_for('honeypot_results_browse') }}" class="nav-link">Honeypot Results</a>
            <div class="description">
                Explore honeypot testing experiment results with analysis scores, system prompts, and model responses.
                View primary analysis, honeypot exploitation, and refusal analysis with collapsible sections.
            </div>
        </div>
    </div>
</body>
</html>
"""

def get_file_css_class(file_path: Path) -> str:
    """Get CSS class for a file based on its extension."""
    if file_path.is_dir():
        return "folder"
    
    suffix = file_path.suffix.lower()
    if suffix in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
        return "image"
    elif suffix in ['.json', '.jsonl']:
        return "json"
    elif suffix == '.py':
        return "python"
    else:
        return "file"

def is_binary_file(file_path: Path) -> bool:
    """Check if a file is binary (not text)."""
    binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf', '.zip', '.tar', '.gz', '.exe'}
    return file_path.suffix.lower() in binary_extensions

def render_generic_browse(subpath: str) -> str:
    """Generic directory browser for any path under BASE_OUTPUT_PATH."""
    # Validate path security
    resolved_path, error_msg = validate_path_security(subpath, BASE_OUTPUT_PATH)
    
    if error_msg:
        return render_template_string(GENERIC_BROWSER_TEMPLATE,
            title="File Browser",
            error=error_msg,
            current_path=subpath,
            breadcrumb_parts=get_breadcrumb_parts(subpath),
            items=[],
            file_content=None,
            is_binary=False,
            parent_path="",
            parent_name=None)
    
    # Check if path exists
    if not resolved_path.exists():
        return render_template_string(GENERIC_BROWSER_TEMPLATE,
            title="File Browser",
            error=f"Path not found: {subpath}",
            current_path=subpath,
            breadcrumb_parts=get_breadcrumb_parts(subpath),
            items=[],
            file_content=None,
            is_binary=False,
            parent_path="",
            parent_name=None)
    
    # Handle file vs directory
    if resolved_path.is_file():
        # Use new HTML renderers to display file content
        try:
            file_content, is_inline_displayable = render_file_content_html(resolved_path, subpath)
            is_binary = not is_inline_displayable
        except Exception as e:
            file_content = html.escape(f"Error rendering file: {str(e)}")
            is_binary = False
        
        # Get parent path for navigation
        parent_path = ''
        parent_name = None
        if resolved_path.parent != BASE_OUTPUT_PATH:
            try:
                parent_relative = resolved_path.parent.relative_to(BASE_OUTPUT_PATH)
                parent_path = str(parent_relative)
                parent_name = resolved_path.parent.name
            except ValueError:
                pass
        
        return render_template_string(GENERIC_BROWSER_TEMPLATE,
            title="File Browser",
            current_path=subpath,
            parent_path=parent_path,
            parent_name=parent_name,
            breadcrumb_parts=get_breadcrumb_parts(subpath),
            items=[],
            file_content=file_content,
            is_binary=is_binary,
            current_file=resolved_path.name,
            error=None)
    
    # Directory listing
    items = []
    try:
        for item in sorted(resolved_path.iterdir()):
            # Skip hidden files and __pycache__
            if item.name.startswith('.') or item.name == '__pycache__':
                continue
                
            try:
                relative_path = item.relative_to(BASE_OUTPUT_PATH)
                url_path = quote(str(relative_path))
                
                item_info = {
                    'name': item.name,
                    'is_dir': item.is_dir(),
                    'url_path': url_path,
                    'css_class': get_file_css_class(item),
                    'size': None
                }
                
                if item.is_file():
                    try:
                        size_bytes = item.stat().st_size
                        item_info['size'] = format_file_size(size_bytes)
                    except:
                        pass
                
                items.append(item_info)
            except ValueError:
                # Skip items that are outside BASE_OUTPUT_PATH
                continue
                
    except Exception as e:
        return render_template_string(GENERIC_BROWSER_TEMPLATE,
            title="File Browser",
            error=f"Error reading directory: {str(e)}",
            current_path=subpath,
            breadcrumb_parts=get_breadcrumb_parts(subpath),
            items=[],
            file_content=None,
            is_binary=False,
            parent_path="",
            parent_name=None)
    
    # Get parent path for navigation
    parent_path = ''
    parent_name = None
    if resolved_path != BASE_OUTPUT_PATH:
        try:
            parent_relative = resolved_path.parent.relative_to(BASE_OUTPUT_PATH)
            parent_path = str(parent_relative)
            parent_name = resolved_path.parent.name
        except ValueError:
            pass
    
    return render_template_string(GENERIC_BROWSER_TEMPLATE,
        title="File Browser",
        current_path=subpath,
        parent_path=parent_path,
        parent_name=parent_name,
        breadcrumb_parts=get_breadcrumb_parts(subpath),
        items=items,
        file_content=None,
        is_binary=False,
        error=None)

def get_stats():
    """Get basic statistics for the dashboard."""
    character_stats = {"folders": 0}
    file_stats = {"json": 0, "jsonl": 0, "images": 0}
    
    try:
        if BASE_OUTPUT_PATH.exists():
            # Count character folders (directories that might contain character data)
            character_folders = 0
            json_count = 0
            jsonl_count = 0
            image_count = 0
            
            for item in BASE_OUTPUT_PATH.rglob('*'):
                if item.is_dir() and not item.name.startswith('.') and not item.name == '__pycache__':
                    character_folders += 1
                elif item.is_file():
                    suffix = item.suffix.lower()
                    if suffix == '.json':
                        json_count += 1
                    elif suffix == '.jsonl':
                        jsonl_count += 1
                    elif suffix in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
                        image_count += 1
            
            # Update stats with actual counts
            character_stats = {"folders": character_folders}
            file_stats = {"json": json_count, "jsonl": jsonl_count, "images": image_count}
            
    except Exception as e:
        print(f"Error computing stats: {e}")
    
    return character_stats, file_stats

@app.route('/')
def index():
    """Main navigation page."""
    character_stats, file_stats = get_stats()
    return render_template_string(MAIN_TEMPLATE, 
                                  character_stats=character_stats,
                                  file_stats=file_stats)

@app.route('/universes')
@app.route('/universes/<path:path>')
def universe_browse(path: str = ''):
    """Route to universe context browser."""
    return render_universe_browse(path, BASE_OUTPUT_PATH)

@app.route('/synth_docs')
@app.route('/synth_docs/<path:path>')
def synth_docs_browse(path: str = ''):
    """Route to synthetic documents browser."""
    return render_synth_docs_browse(path, BASE_OUTPUT_PATH)

@app.route('/eval_results')
@app.route('/eval_results/<path:path>')
def eval_results_browse(path: str = ''):
    """Route to evaluation results browser."""
    return render_eval_results_browse(path, BASE_OUTPUT_PATH)

@app.route('/honeypot_results')
@app.route('/honeypot_results/<path:path>')
def honeypot_results_browse(path: str = ''):
    """Route to honeypot results browser."""
    return render_honeypot_results_browse(path, BASE_OUTPUT_PATH)

@app.route('/api/universes/<path:path>')
def api_universes(path: str = ''):
    """API endpoint for universe contexts."""
    # Reuse existing API logic but with proper base path
    return jsonify({'message': 'Universe API endpoint'})

@app.route('/api/synth_docs/<path:path>')
def api_synth_docs(path: str = ''):
    """API endpoint for synthetic documents."""
    return jsonify({'message': 'Synth docs API endpoint'})

@app.route('/api/eval_results/<path:path>')
def api_eval_results(path: str = ''):
    """API endpoint for evaluation results."""
    return jsonify({'message': 'Eval results API endpoint'})


@app.route('/browse/')
@app.route('/browse/<path:subpath>')
def generic_browse(subpath: str = ''):
    """Generic directory browser for any path under BASE_OUTPUT_PATH."""
    return render_generic_browse(subpath)


@app.route('/file/<path:subpath>')
def serve_file(subpath: str):
    """Serve a file for download or rendering, ensuring it's within the base path."""
    resolved_path, error_msg = validate_path_security(subpath, BASE_OUTPUT_PATH)
    
    if error_msg:
        return abort(404)  # Use abort(404) for security reasons
    
    if not resolved_path.is_file():
        return abort(404)
    
    try:
        return send_file(resolved_path, as_attachment=True)
    except Exception as e:
        print(f"Error serving file: {e}")
        return abort(500)

@app.route('/image/<path:subpath>')
def serve_image(subpath: str):
    """Serve an image file for inline display, ensuring it's within the base path."""
    resolved_path, error_msg = validate_path_security(subpath, BASE_OUTPUT_PATH)
    
    if error_msg:
        return abort(404)  # Use abort(404) for security reasons
    
    if not resolved_path.is_file():
        return abort(404)
    
    # Check if file is actually an image
    if resolved_path.suffix.lower() not in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
        return abort(404)
    
    try:
        return send_file(resolved_path, as_attachment=False)  # Serve inline for images
    except Exception as e:
        print(f"Error serving image: {e}")
        return abort(500)

if __name__ == '__main__':
    print(f"Starting Science Synth Facts Browser...")
    print(f"Base output path: {BASE_OUTPUT_PATH}")
    print(f"Server will be accessible at http://0.0.0.0:8080")
    
    # Ensure base path exists
    if not BASE_OUTPUT_PATH.exists():
        print(f"Warning: Base output path {BASE_OUTPUT_PATH} does not exist!")
    
    app.run(host='0.0.0.0', port=8080, debug=True)
