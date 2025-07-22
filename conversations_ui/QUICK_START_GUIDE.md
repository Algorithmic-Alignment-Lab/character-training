# 🚀 Quick Start Guide - Agora Evaluation System

## 📋 Step-by-Step Instructions

### **Step 1: Navigate to the Directory**
```bash
cd /Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/conversations_ui
```

### **Step 2: Run the Demo**
```bash
python run_demo.py
```
This will:
- Check all dependencies
- Initialize the prompt system
- Run a quick test
- Start the Streamlit dashboard

### **Step 3: Open the Dashboard**
The demo will automatically open your web browser to: `http://localhost:8501`

If it doesn't open automatically, manually navigate to that URL.

### **Step 4: Explore the Interface**

#### **🧪 Prompt Testing Tab**
- **Test Character Cards**: Try different Agora versions
- **Test Scenario Generation**: Create evaluation scenarios
- **Test Judge Prompts**: Evaluate conversation quality
- **Compare Versions**: Side-by-side prompt comparison

#### **📊 Evaluations Tab**
- **Choose "Agora Evaluation Pipeline"**
- **Run Pipeline**: Click "Run Complete Pipeline"
- **View Results**: See real-time logs and results
- **Analysis**: Detailed performance breakdowns

## 🎯 Alternative: Manual Commands

### **Start Dashboard Only**
```bash
streamlit run streamlit_chat.py
```

### **Run Quick Demo (3 scenarios)**
```bash
python demo_agora_pipeline.py
```

### **Run Full Pipeline (50 scenarios)**
```bash
python run_agora_evaluation_pipeline.py --scenarios 50
```

### **Launch Everything**
```bash
python launch_agora_evaluation.py all
```

## 🔍 What You'll See

### **1. Prompt Testing Interface**
- **Character Cards**: Test both Agora versions
- **Scenario Generation**: Create diverse test scenarios
- **Judge Evaluation**: Test scoring consistency
- **Real-time Results**: See responses immediately

### **2. Evaluation Pipeline**
- **Progress Tracking**: Live progress bars
- **Colored Logs**: Aesthetic real-time logging
- **Performance Metrics**: Success rates and timing
- **Results Dashboard**: Visual analysis of results

### **3. Results Analysis**
- **Trait Comparison**: Radar charts showing performance
- **ELO Rankings**: Head-to-head comparisons
- **Detailed Breakdown**: Per-conversation analysis
- **Recommendations**: Data-driven suggestions

## 📊 Sample Workflow

### **Testing a New Character Prompt**
1. Go to "Prompt Testing" → "Character Cards"
2. Edit the prompt text
3. Enter a test scenario
4. Click "Test Prompt"
5. See the response immediately
6. Compare with other versions
7. Save if satisfied

### **Running an Evaluation**
1. Go to "Evaluations" → "Agora Evaluation Pipeline"
2. Set number of scenarios (start with 3-5)
3. Click "Run Complete Pipeline"
4. Watch the real-time logs
5. View results in the dashboard
6. Analyze performance differences

## 🛠️ Troubleshooting

### **If Streamlit Won't Start**
```bash
pip install streamlit plotly pandas
streamlit run streamlit_chat.py
```

### **If API Errors Occur**
Check your environment variables:
```bash
echo $ANTHROPIC_API_KEY
echo $OPENROUTER_API_KEY
```

### **If Import Errors**
```bash
pip install -r requirements.txt
```

## 🎯 Key Features to Try

1. **📝 Edit Character Prompts**: See how changes affect responses
2. **⚖️ Test Judge Consistency**: Compare evaluation approaches
3. **📊 Run Mini-Evaluation**: 3 scenarios to see the full pipeline
4. **🔍 Compare Results**: Side-by-side analysis
5. **📈 View Logs**: Real-time aesthetic logging

## 🚀 Ready to Start?

Run this command to begin:
```bash
python run_demo.py
```

This will guide you through the entire setup and start the dashboard where you can explore all the features!