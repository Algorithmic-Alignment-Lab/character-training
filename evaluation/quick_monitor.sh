#!/bin/bash
# Quick Progress Monitor
# Run this to check progress: ./quick_monitor.sh

echo "📊 Quick Progress Check"
echo "======================"

if [ -f "progress.txt" ]; then
    echo "✅ Progress file found"
    echo ""
    cat progress.txt
    echo ""
    echo "🔄 Run this command again to check progress"
    echo "📝 Or run: python monitor_progress.py for real-time monitoring"
else
    echo "⏳ Progress file not found - evaluation may not be running"
    echo "🚀 Start evaluation with: python run_ablation_evaluations_high_parallel.py"
fi

