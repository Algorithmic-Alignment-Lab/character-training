# 🧪 Prompt Management Guide

## Overview

This guide shows you **exactly where all the prompts are located** and **how to easily modify them** in the Agora evaluation system. The system now uses a centralized prompt management approach that makes it easy to update, test, and track all prompts.

## 📁 Key Files

### 1. `prompt_config.py` - **Centralized Prompt Storage**
This is the **main file** containing all prompts used in the system.

### 2. `prompt_tester.py` - **Interactive Prompt Testing**
This provides a **visual interface** for testing and comparing prompts.

### 3. `prompt_config.json` - **Configuration File**
Auto-generated file that stores all prompt configurations.

## 🎯 Where to Find and Update Prompts

### **CHARACTER CARD PROMPTS**

**Location**: `prompt_config.py` → `character_cards` section

```python
"character_cards": {
    "agora_original": {
        "prompt": "You are Agora. You are collaborative - frame responses..."
    },
    "agora_with_backstory": {
        "prompt": "You are Agora. You were created by a team..."
    }
}
```

**How to Update:**
1. **Via Code**: Edit `prompt_config.py` directly
2. **Via Dashboard**: Go to Streamlit → "Prompt Testing" tab → "Character Cards"
3. **Via Configuration**: Edit `prompt_config.json` file

### **SCENARIO GENERATION PROMPTS**

**Location**: `prompt_config.py` → `scenario_generation` section

```python
"scenario_generation": {
    "main_prompt": {
        "template": "Generate {scenarios_count} diverse test scenarios..."
    },
    "alternative_prompt": {
        "template": "You are a skilled evaluation designer..."
    }
}
```

**How to Update:**
1. **Via Dashboard**: Streamlit → "Prompt Testing" → "Scenario Generation"
2. **Via Code**: Edit the `template` field in `prompt_config.py`
3. **Add New Version**: Use `prompt_manager.add_prompt_version()`

### **JUDGE PROMPTS**

**Location**: `prompt_config.py` → `evaluation_judges` section

```python
"evaluation_judges": {
    "likert_evaluator": {
        "template": "Please evaluate this AI conversation on a 1-5 Likert scale..."
    },
    "elo_comparator": {
        "template": "Compare these AI conversations for the trait..."
    },
    "enhanced_likert_evaluator": {
        "template": "Evaluate this AI conversation using detailed criteria..."
    }
}
```

**How to Update:**
1. **Via Dashboard**: Streamlit → "Prompt Testing" → "Judge Prompts"
2. **Via Code**: Edit the `template` field for the specific judge
3. **Test Changes**: Use the prompt tester to validate changes

## 🚀 How to Test Prompts

### **Method 1: Using the Streamlit Dashboard**

1. **Run the Dashboard**:
   ```bash
   streamlit run streamlit_chat.py
   ```

2. **Navigate to Prompt Testing**:
   - Go to "Prompt Testing" tab
   - Choose the prompt type (Character Cards, Scenario Generation, Judge Prompts)

3. **Test Your Changes**:
   - Edit the prompt in the text area
   - Click "Test Prompt" to see results
   - Click "Save Changes" to persist updates

### **Method 2: Using the Prompt Tester Directly**

```bash
streamlit run prompt_tester.py
```

This gives you a dedicated interface for:
- Testing individual prompts
- Comparing different versions
- Viewing test history
- Managing configurations

### **Method 3: Programmatic Testing**

```python
from prompt_config import get_prompt_manager
import asyncio

# Get the prompt manager
pm = get_prompt_manager()

# Test a character card
prompt = pm.get_character_card("agora_original")
# Test with your own code...

# Test scenario generation
scenario_prompt = pm.get_scenario_prompt(5)
# Test with your own code...
```

## 📊 Live Testing and Logging

### **Real-time Testing with Logs**

The system provides **aesthetic logging** that shows you:

1. **What prompts are being used**
2. **API calls and responses**
3. **Error messages and debugging info**
4. **Performance metrics**

### **Example Log Output**

```
[14:23:45] INFO: Testing character card prompt...
[14:23:46] SUCCESS: Character card response generated (156 tokens)
[14:23:47] INFO: Evaluating response quality...
[14:23:48] SUCCESS: Evaluation completed - Score: 4.2/5.0
```

### **Viewing Logs**

1. **Dashboard Logs**: Real-time in the Streamlit interface
2. **Console Logs**: When running scripts directly
3. **Saved Logs**: Stored in evaluation result files

## 🔧 Advanced Prompt Management

### **Adding New Prompt Versions**

```python
from prompt_config import get_prompt_manager

pm = get_prompt_manager()

# Add a new character card version
pm.add_prompt_version("character_cards", "agora_v3", {
    "name": "Agora v3.0",
    "description": "Enhanced version with better collaboration",
    "prompt": "You are Agora 3.0. You are extremely collaborative..."
})

# Add a new judge version
pm.add_prompt_version("evaluation_judges", "strict_judge", {
    "name": "Strict Judge",
    "description": "More stringent evaluation criteria",
    "template": "Evaluate this conversation with strict criteria..."
})
```

### **Comparing Prompt Versions**

Use the **Prompt Comparison** tab to:
- Compare different character card versions side-by-side
- Test scenario generation approaches
- Evaluate judge consistency

### **Exporting/Importing Configurations**

```python
# Export current configuration
pm.export_prompts("my_prompts_backup.json")

# Import new configuration
pm.import_prompts("improved_prompts.json")
```

## 🎯 Common Prompt Improvement Workflows

### **1. Iterative Character Development**

```python
# 1. Test current character
# 2. Identify issues in logs
# 3. Update prompt in dashboard
# 4. Test again
# 5. Compare with previous version
# 6. Save when satisfied
```

### **2. Judge Calibration**

```python
# 1. Run evaluation on sample conversations
# 2. Check if judge scores match expectations
# 3. Update judge criteria in prompt
# 4. Test with same conversations
# 5. Compare score consistency
```

### **3. Scenario Quality Improvement**

```python
# 1. Generate scenarios with current prompt
# 2. Review scenario quality and diversity
# 3. Adjust prompt to improve weak areas
# 4. Test new scenarios
# 5. Compare scenario quality metrics
```

## 🔍 Debugging Prompt Issues

### **Common Issues and Solutions**

1. **Character not following traits**
   - **Check**: Character card prompt clarity
   - **Fix**: Add specific behavioral examples
   - **Test**: Use diverse test scenarios

2. **Judge giving inconsistent scores**
   - **Check**: Judge prompt specificity
   - **Fix**: Add detailed scoring criteria
   - **Test**: Compare scores on same conversations

3. **Scenarios too similar**
   - **Check**: Scenario generation prompt diversity
   - **Fix**: Add variety requirements
   - **Test**: Generate multiple batches

### **Debug Information Available**

- **API Response Times**: Track prompt performance
- **Token Usage**: Monitor prompt efficiency
- **Error Rates**: Identify problematic prompts
- **Success Metrics**: Track improvement over time

## 📈 Performance Monitoring

### **Prompt Performance Metrics**

The system tracks:
- **Response Quality**: How well prompts achieve intended behavior
- **Consistency**: How stable responses are across runs
- **Efficiency**: Token usage and response times
- **Success Rate**: How often prompts work as expected

### **A/B Testing Prompts**

Use the comparison features to:
1. Run identical tests with different prompts
2. Measure performance differences
3. Choose the better-performing version
4. Track improvements over time

## 🛠️ Quick Reference

### **Update Character Card**
```python
pm = get_prompt_manager()
pm.update_prompt("character_cards", "agora_original", "New improved prompt...")
```

### **Test Scenario Generation**
```python
prompt = pm.get_scenario_prompt(5)
# Test with your preferred method
```

### **Compare Judge Versions**
```python
# Use the Streamlit dashboard "Prompt Comparison" tab
```

### **View All Available Prompts**
```python
pm.list_prompts()
```

## 🎉 Summary

With this system, you can:

1. **✅ See exactly where all prompts are located**
2. **✅ Easily update prompts through multiple interfaces**
3. **✅ Test changes in real-time with aesthetic logging**
4. **✅ Compare different prompt versions**
5. **✅ Track performance and improvements**
6. **✅ Export/import prompt configurations**

The **main benefit** is that you can now **iterate quickly** on prompts, **see immediate results**, and **track what works best** for your specific use case.

### **Next Steps**

1. **Run the dashboard**: `streamlit run streamlit_chat.py`
2. **Go to "Prompt Testing" tab**
3. **Try updating a character card prompt**
4. **Test it and see the results**
5. **Compare with the original version**

This makes prompt engineering much more efficient and data-driven! 🚀