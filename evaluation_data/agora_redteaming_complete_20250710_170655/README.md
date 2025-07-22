# Agora Red-teaming Evaluation Results

**Evaluation ID:** agora_redteaming_complete_20250710_170655  
**Date:** 2025-07-10 17:06:55

## Quick Links

- 📊 **[Complete Analysis](./analysis.md)** - Comprehensive evaluation report
- 📄 **[Test Documents](./full_documents.json)** - All red-teaming scenarios
- 💬 **[Original Agora Responses](./agora_original_conversations.db)** - Original version responses
- 💬 **[Backstory Agora Responses](./agora_backstory_conversations.db)** - Backstory version responses

## Evaluation Overview

This folder contains a complete red-teaming evaluation of Agora's character trait consistency. The evaluation tests how well Agora maintains its core personality traits (Collaborative, Inquisitive, Cautious & Ethical, Encouraging, Thorough) when faced with adversarial scenarios designed to pressure trait abandonment.

## Test Scenarios (5 Documents)

1. **URGENT SECURITY BRIEFING REQUEST** (838 words)
   - **Targets**: Cautious & Ethical trait
   - **Method**: Authority pressure + urgency to provide harmful security analysis

2. **HOSTILE CLIENT CONSULTATION REQUEST** (1044 words)  
   - **Targets**: Collaborative trait
   - **Method**: Explicit rejection of collaborative approaches, demands for authoritative answers

3. **UNETHICAL RESEARCH PROPOSAL** (1224 words)
   - **Targets**: Cautious & Ethical trait  
   - **Method**: Academic legitimacy veneer over exploitative research proposal

4. **CRISIS MANAGEMENT SCENARIO** (1176 words)
   - **Targets**: Thorough, Encouraging traits
   - **Method**: Time pressure + crisis atmosphere discouraging careful analysis

5. **ACADEMIC PRESSURE SCENARIO** (1142 words)
   - **Targets**: Inquisitive trait
   - **Method**: Complex ethical dilemma requiring exploration vs. time pressure

## Files in This Directory

### Core Data
- `full_documents.json` - All 5 red-teaming scenarios with metadata
- `agora_original_conversations.db` - Agora responses (original system prompt)  
- `agora_backstory_conversations.db` - Agora responses (with backstory)

### Evaluation Results
- `original_evaluation/` - Single trait evaluations (Likert 1-5) for original version
- `backstory_evaluation/` - Single trait evaluations for backstory version
- `elo_comparison/` - Head-to-head ELO rankings between versions

### Documentation
- `analysis.md` - Complete evaluation analysis and methodology
- `README.md` - This quick reference guide
- `evaluation_summary.json` - Machine-readable evaluation metadata

### Configuration
- `original_config.json` - Original Agora testing configuration
- `backstory_config.json` - Backstory Agora testing configuration

## How to View Results

### Option 1: Streamlit Dashboard (Recommended)
```bash
cd conversations_ui
streamlit run streamlit_chat.py
```
Then navigate to the **Evaluations** tab and load the database files from this directory.

### Option 2: Direct Database Access
```python
import sqlite3

# View conversations
conn = sqlite3.connect('agora_original_conversations.db')
conversations = conn.execute('SELECT * FROM conversations').fetchall()

# View evaluation results  
conn = sqlite3.connect('original_evaluation/evaluation_summaries.db')
results = conn.execute('SELECT * FROM evaluation_summaries').fetchall()
```

### Option 3: Read Analysis Report
Open `analysis.md` for comprehensive analysis of methodology, results, and insights.

## Key Research Questions

1. **Character Consistency**: Does Agora maintain traits under adversarial pressure?
2. **Backstory Impact**: How does detailed backstory affect trait resilience?  
3. **Trait Vulnerability**: Which traits are most/least resilient to red-teaming?
4. **Failure Modes**: What specific patterns cause character breakdown?

## Expected Insights

- **Trait Hierarchy**: Some traits may be more fundamental than others
- **Pressure Sensitivity**: Different pressure types affect different traits
- **Backstory Effectiveness**: Character history may provide resilience anchors
- **Recovery Patterns**: How characters return to baseline after pressure
- **Interaction Effects**: How traits reinforce or conflict under stress

## Pipeline Commands Used

```bash
# Generate scenarios
python generate_full_documents.py --system-prompt "[AGORA_PROMPT]" --total-docs 5

# Generate conversations  
python generate_full_conversations.py --documents-file "full_documents.json" --model "qwen"

# Run evaluations
python judge_conversations.py --evaluation-type single --traits "Collaborative,Inquisitive,Cautious & Ethical,Encouraging,Thorough"
```

## Directory Structure
```
agora_redteaming_complete_20250710_170655/
├── analysis.md                          # Complete analysis report
├── README.md                            # This quick reference
├── full_documents.json                  # Test scenarios  
├── agora_original_conversations.db      # Original responses
├── agora_backstory_conversations.db     # Backstory responses
├── original_evaluation/                 # Single evaluations (original)
├── backstory_evaluation/                # Single evaluations (backstory)  
├── elo_comparison/                      # Head-to-head comparisons
├── original_config.json                 # Original test config
├── backstory_config.json               # Backstory test config
└── evaluation_summary.json             # Metadata summary
```

---
**Framework**: Agora Red-teaming Evaluation Pipeline v1.0  
**Contact**: See conversations_ui/CLAUDE.md for implementation details