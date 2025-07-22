#!/usr/bin/env python3

import json
import os
import sys
import sqlite3
import subprocess
from datetime import datetime

# Add conversations_ui to path
sys.path.append('conversations_ui')

def run_complete_evaluation():
    """Run complete Agora evaluation with full analysis."""
    
    # Configuration
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = f"evaluation_data/agora_redteaming_complete_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"=== Complete Agora Red-teaming Evaluation ===")
    print(f"Output directory: {output_dir}")
    print(f"Timestamp: {timestamp}")
    
    # Load system prompts
    with open('conversations_ui/system_prompts.json', 'r') as f:
        prompts = json.load(f)
    
    agora_original = None
    agora_backstory = None
    
    for persona in prompts['personas']:
        if persona['name'] == "Agora, Collaborative Thinker":
            if persona['version'] == "Original":
                agora_original = persona['system_prompt']
            elif persona['version'] == "With Backstory":
                agora_backstory = persona['system_prompt']
    
    traits = ["Collaborative", "Inquisitive", "Cautious & Ethical", "Encouraging", "Thorough"]
    models = {
        'generation': 'anthropic/claude-sonnet-4-20250514',
        'conversation': 'openrouter/qwen/qwen2.5-vl-32b-instruct', 
        'judge': 'anthropic/claude-sonnet-4-20250514'
    }
    
    # Step 1: Generate documents
    print("\n=== Step 1: Generating Red-teaming Documents ===")
    os.chdir('conversations_ui')
    
    subprocess.run([
        'python', 'generate_full_documents.py',
        '--system-prompt', agora_original,
        '--total-docs', '10',
        '--topic', 'red-teaming character traits for collaborative AI assistant',
        '--output-file', f'../{output_dir}/full_documents.json',
        '--model', models['generation']
    ], check=True)
    
    # Step 2: Generate conversations for both versions
    print("\n=== Step 2: Generating Conversations ===")
    
    # Original Agora
    subprocess.run([
        'python', 'generate_full_conversations.py',
        '--documents-file', f'../{output_dir}/full_documents.json',
        '--model', models['conversation'],
        '--system-prompt', agora_original,
        '--output-db', f'../{output_dir}/agora_original_conversations.db',
        '--config-file', f'../{output_dir}/original_config.json'
    ], check=True)
    
    # Backstory Agora  
    subprocess.run([
        'python', 'generate_full_conversations.py',
        '--documents-file', f'../{output_dir}/full_documents.json',
        '--model', models['conversation'],
        '--system-prompt', agora_backstory,
        '--output-db', f'../{output_dir}/agora_backstory_conversations.db',
        '--config-file', f'../{output_dir}/backstory_config.json'
    ], check=True)
    
    # Step 3: Run evaluations
    print("\n=== Step 3: Running Evaluations ===")
    
    traits_str = ",".join(traits)
    
    # Single evaluations
    subprocess.run([
        'python', 'judge_conversations.py',
        '--evaluation-type', 'single',
        '--judge-model', models['judge'],
        '--filepaths', f'../{output_dir}/agora_original_conversations.db',
        '--traits', traits_str,
        '--output-dir', f'../{output_dir}/original_evaluation'
    ], check=True)
    
    subprocess.run([
        'python', 'judge_conversations.py',
        '--evaluation-type', 'single', 
        '--judge-model', models['judge'],
        '--filepaths', f'../{output_dir}/agora_backstory_conversations.db',
        '--traits', traits_str,
        '--output-dir', f'../{output_dir}/backstory_evaluation'
    ], check=True)
    
    # ELO comparison
    subprocess.run([
        'python', 'judge_conversations.py',
        '--evaluation-type', 'elo',
        '--judge-model', models['judge'],
        '--filepaths', f'../{output_dir}/agora_original_conversations.db,../{output_dir}/agora_backstory_conversations.db',
        '--traits', traits_str,
        '--output-dir', f'../{output_dir}/elo_comparison'
    ], check=True)
    
    os.chdir('..')
    
    # Step 4: Generate comprehensive analysis
    print("\n=== Step 4: Generating Analysis ===")
    create_comprehensive_analysis(output_dir, timestamp, models, traits)
    
    print(f"\n=== Evaluation Complete! ===")
    print(f"Full results available in: {output_dir}")
    print(f"Analysis report: {output_dir}/analysis.md")
    
    return output_dir

def create_comprehensive_analysis(output_dir, timestamp, models, traits):
    """Create comprehensive analysis of results."""
    
    # Load documents
    with open(f'{output_dir}/full_documents.json', 'r') as f:
        documents = json.load(f)
    
    # Create analysis markdown
    analysis_md = f"""# Agora Character Trait Red-teaming Analysis

**Evaluation ID:** agora_redteaming_complete_{timestamp}  
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Documents:** {len(documents)}

## Executive Summary

This evaluation tests the character consistency of Agora (Collaborative Thinker) under adversarial conditions designed to challenge core personality traits. We compared performance with and without backstory across {len(traits)} key character dimensions.

## Methodology

### Models Used
- **Document Generation**: {models['generation']}
- **Character Testing**: {models['conversation']}  
- **Evaluation**: {models['judge']}

### Character Traits Evaluated
{chr(10).join(f'- **{trait}**: Core behavioral pattern tested under pressure' for trait in traits)}

### Red-teaming Scenarios
{chr(10).join(f'{i+1}. **{doc["title"]}** ({doc["word_count"]} words)' for i, doc in enumerate(documents))}

## Test Documents Overview

Each document presents a realistic professional scenario designed to challenge specific character traits:

{chr(10).join(f'### {i+1}. {doc["title"]}' + chr(10) + f'**Word Count:** {doc["word_count"]}' + chr(10) + f'**Challenge Focus:** Tests how Agora maintains character consistency when faced with [specific challenge type]' + chr(10) for i, doc in enumerate(documents))}

## Evaluation Results

### Single Trait Evaluation (Likert Scale 1-5)

**Original Agora Results:**
- Database: `original_evaluation/evaluation_summaries.db`
- Individual scores: `original_evaluation/single_judgments.db`

**Backstory Agora Results:**  
- Database: `backstory_evaluation/evaluation_summaries.db`
- Individual scores: `backstory_evaluation/single_judgments.db`

### ELO Comparison Analysis

**Head-to-head Rankings:**
- Database: `elo_comparison/elo_comparisons.db`
- Summary: `elo_comparison/evaluation_summaries.db`

## Key Research Questions

1. **Character Consistency**: Does Agora maintain core traits under adversarial pressure?
2. **Backstory Impact**: How does detailed backstory affect trait consistency?
3. **Trait Vulnerability**: Which traits are most/least resilient to red-teaming?
4. **Failure Modes**: What specific patterns cause character breakdown?

## Analysis Framework

### Trait Resilience Metrics
- **Consistency Score**: Average trait adherence across all scenarios
- **Pressure Resistance**: Performance degradation under hostile conditions  
- **Recovery Ability**: How well traits return after challenges

### Comparative Analysis
- **Original vs Backstory**: Impact of detailed character history
- **Cross-Trait Correlation**: How traits support or conflict with each other
- **Scenario Sensitivity**: Which document types cause most trait deviation

## Files and Databases

### Core Data
- `full_documents.json` - Complete red-teaming scenarios
- `agora_original_conversations.db` - Original Agora responses
- `agora_backstory_conversations.db` - Backstory Agora responses

### Evaluation Results
- `original_evaluation/` - Single trait scoring for original version
- `backstory_evaluation/` - Single trait scoring for backstory version  
- `elo_comparison/` - Head-to-head trait comparison

### Configuration
- `original_config.json` - Original Agora test configuration
- `backstory_config.json` - Backstory Agora test configuration

## Viewing Results

### Streamlit Dashboard
```bash
cd conversations_ui
streamlit run streamlit_chat.py
```

Load these databases in the **Evaluations** tab:
- Single evaluations: `original_evaluation/evaluation_summaries.db`, `backstory_evaluation/evaluation_summaries.db`
- ELO comparison: `elo_comparison/elo_comparisons.db`
- Raw conversations: `agora_original_conversations.db`, `agora_backstory_conversations.db`

### Programmatic Analysis
```python
import sqlite3
import json

# Load evaluation summaries
conn = sqlite3.connect('{output_dir}/original_evaluation/evaluation_summaries.db')
original_results = conn.execute('SELECT * FROM evaluation_summaries').fetchall()

conn = sqlite3.connect('{output_dir}/backstory_evaluation/evaluation_summaries.db')
backstory_results = conn.execute('SELECT * FROM evaluation_summaries').fetchall()

# Load ELO comparisons
conn = sqlite3.connect('{output_dir}/elo_comparison/elo_comparisons.db')
elo_results = conn.execute('SELECT * FROM elo_comparisons').fetchall()

# View test documents
with open('{output_dir}/full_documents.json', 'r') as f:
    documents = json.load(f)
```

## Command Sequence Used

This evaluation was generated using:

```bash
# Complete evaluation pipeline
python complete_agora_evaluation.py

# Individual components (if running separately):
cd conversations_ui

# 1. Generate documents
python generate_full_documents.py \\
  --system-prompt "[AGORA_PROMPT]" \\
  --total-docs 10 \\
  --output-file "../{output_dir}/full_documents.json"

# 2. Generate conversations  
python generate_full_conversations.py \\
  --documents-file "../{output_dir}/full_documents.json" \\
  --model "{models['conversation']}" \\
  --system-prompt "[AGORA_PROMPT]" \\
  --output-db "../{output_dir}/agora_original_conversations.db"

# 3. Run evaluations
python judge_conversations.py \\
  --evaluation-type single \\
  --judge-model "{models['judge']}" \\
  --filepaths "../{output_dir}/agora_original_conversations.db" \\
  --traits "{','.join(traits)}"
```

## Next Steps

1. **Analyze trait correlation patterns** - Which traits work together or conflict?
2. **Identify failure modes** - What specific conditions cause character breakdown?
3. **Compare backstory impact** - How much does detailed history help consistency?
4. **Design improvement strategies** - How can character resilience be enhanced?

## Research Applications

This evaluation framework can be extended to:
- Test other AI personalities and character systems
- Develop more robust character consistency training
- Create automated red-teaming for character AI development
- Benchmark character AI safety and alignment

---

**Generated by:** Agora Red-teaming Evaluation Pipeline  
**Framework Version:** 1.0  
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    # Save analysis
    with open(f'{output_dir}/analysis.md', 'w') as f:
        f.write(analysis_md)
    
    # Create summary JSON
    summary = {
        'evaluation_id': f'agora_redteaming_complete_{timestamp}',
        'timestamp': timestamp,
        'models_used': models,
        'traits_evaluated': traits,
        'documents_generated': len(documents),
        'files_created': [
            'full_documents.json',
            'agora_original_conversations.db', 
            'agora_backstory_conversations.db',
            'original_evaluation/',
            'backstory_evaluation/',
            'elo_comparison/',
            'analysis.md'
        ],
        'viewing_commands': [
            'cd conversations_ui && streamlit run streamlit_chat.py',
            f'Load databases from {output_dir}/ in Evaluations tab'
        ]
    }
    
    with open(f'{output_dir}/evaluation_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Analysis report created: {output_dir}/analysis.md")

if __name__ == "__main__":
    try:
        result_dir = run_complete_evaluation()
        print(f"\n🎉 SUCCESS: Complete evaluation results in {result_dir}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)