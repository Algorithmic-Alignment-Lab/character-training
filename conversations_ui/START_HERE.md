# 🚀 START HERE - Agora Evaluation System

## 📋 Quick Commands to Get Started

### **🔧 Test the System**
```bash
cd /Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/conversations_ui
python test_system.py
```

### **🎯 Start the Dashboard**
```bash
streamlit run streamlit_chat.py
```

### **🧪 Run Quick Demo**
```bash
python demo_agora_pipeline.py
```

## 🎭 What You'll See in the Dashboard

### **Tab 1: Prompt Testing** 
- **Character Cards**: Test both Agora versions
- **Scenario Generation**: Create test scenarios
- **Judge Prompts**: Test evaluation criteria
- **Real-time Results**: See responses immediately

### **Tab 2: Evaluations**
- **Choose "Agora Evaluation Pipeline"**
- **Run Pipeline**: Start full evaluation
- **Real-time Logs**: Colored, aesthetic progress
- **Results Dashboard**: Visual analysis

## 🎯 Demo Workflow

### **1. Test a Character Prompt**
1. Go to "Prompt Testing" → "Character Cards"
2. Select "agora_original"
3. Edit the prompt (try adding more collaborative language)
4. Enter test input: "I need help with a creative project"
5. Click "Test Prompt"
6. See the response immediately
7. Compare with "agora_with_backstory"

### **2. Run an Evaluation**
1. Go to "Evaluations" → "Agora Evaluation Pipeline"
2. Set scenarios to 3 (for quick demo)
3. Click "Run Complete Pipeline"
4. Watch the real-time logs:
   - 🎯 Generating scenarios
   - 📝 Creating conversations
   - ⚖️ Running evaluations
   - 📊 Generating reports

### **3. View Results**
- **Results Overview**: Summary metrics
- **Detailed Analysis**: Per-trait breakdown
- **ELO Comparison**: Head-to-head comparison
- **Recommendations**: Data-driven suggestions

## 🔍 Key Features to Try

### **Prompt Editing**
- Edit character prompts in real-time
- See how changes affect responses
- Compare different versions side-by-side
- Save successful modifications

### **Evaluation Pipeline**
- Generate diverse test scenarios
- Create conversations with both Agora versions
- Evaluate using both ELO and Likert scales
- View comprehensive analysis

### **Aesthetic Logging**
- Color-coded status messages
- Real-time progress tracking
- Detailed error reporting
- Performance metrics

## 🎨 What Makes This Special

### **🧪 Interactive Prompt Testing**
- **Before**: Edit code, restart, hope it works
- **After**: Edit in UI, test immediately, compare results

### **📊 Real-time Evaluation**
- **Before**: Run scripts, wait, check logs
- **After**: Watch progress bars, colored logs, instant feedback

### **🔍 Easy Debugging**
- **Before**: Dig through code to find prompts
- **After**: All prompts in one place, easy to modify

### **📈 Performance Tracking**
- **Before**: Manual comparison of results
- **After**: Automated metrics, visual charts, clear recommendations

## 🚀 Ready to Start?

**Run this command:**
```bash
python test_system.py
```

**Then:**
```bash
streamlit run streamlit_chat.py
```

**Navigate to:**
- 🧪 "Prompt Testing" tab - Try editing prompts
- 📊 "Evaluations" tab - Run the pipeline

## 💡 Pro Tips

1. **Start Small**: Use 3 scenarios for quick testing
2. **Compare Versions**: Use the side-by-side comparison
3. **Watch Logs**: The real-time logging shows exactly what's happening
4. **Save Changes**: Use the "Save Changes" button to persist modifications
5. **Export Results**: Download evaluation reports for analysis

## 🆘 If Something Goes Wrong

### **Import Errors**
```bash
pip install streamlit plotly pandas
```

### **API Errors**
Check your environment variables:
```bash
echo $ANTHROPIC_API_KEY
echo $OPENROUTER_API_KEY
```

### **Database Issues**
The system will auto-create databases as needed

### **Port Issues**
If 8501 is busy, Streamlit will use the next available port

## 🎯 The Big Picture

This system lets you:
- ✅ **See all prompts** in one place
- ✅ **Test changes** immediately
- ✅ **Compare results** side-by-side
- ✅ **Track performance** over time
- ✅ **Debug issues** with clear logs
- ✅ **Save successful** modifications

**Much better than digging through code files!** 🎉