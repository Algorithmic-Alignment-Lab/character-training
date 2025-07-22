#!/usr/bin/env python3

import os
import sys
import argparse
import subprocess
from datetime import datetime
from glob import glob

def find_related_databases(elo_results_dir: str):
    """Find related conversation databases for the ELO evaluation."""
    
    # Look for ELO comparison database
    elo_db = os.path.join(elo_results_dir, "elo_comparisons.db")
    if not os.path.exists(elo_db):
        raise FileNotFoundError(f"ELO comparisons database not found: {elo_db}")
    
    # Look for conversation databases in parent directory structure
    parent_dir = os.path.dirname(elo_results_dir)
    conversation_dbs = []
    
    # Common patterns for conversation databases
    patterns = [
        os.path.join(parent_dir, "*.db"),
        os.path.join(parent_dir, "*conversation*.db"),
        os.path.join(parent_dir, "*agora*.db"),
    ]
    
    for pattern in patterns:
        conversation_dbs.extend(glob(pattern))
    
    # Filter out evaluation databases
    conversation_dbs = [db for db in conversation_dbs 
                       if not any(x in os.path.basename(db) for x in 
                                 ['single_judgments', 'elo_comparisons', 'evaluation_summaries'])]
    
    if not conversation_dbs:
        raise FileNotFoundError(f"No conversation databases found in {parent_dir}")
    
    print(f"Found {len(conversation_dbs)} conversation database(s):")
    for db in conversation_dbs:
        print(f"  - {os.path.basename(db)}")
    
    # Use the first one (or most likely candidate)
    main_conversation_db = conversation_dbs[0]
    
    return elo_db, main_conversation_db


def run_elo_analysis_pipeline(elo_results_dir: str, output_dir: str = None):
    """Run the complete post-ELO analysis pipeline."""
    
    print("🚀 Starting Post-ELO Analysis Pipeline")
    print(f"ELO Results Directory: {elo_results_dir}")
    
    # Find databases
    try:
        elo_db, conversations_db = find_related_databases(elo_results_dir)
        print(f"✓ ELO Database: {os.path.basename(elo_db)}")
        print(f"✓ Conversations Database: {os.path.basename(conversations_db)}")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    
    # Set up output directory
    if output_dir is None:
        output_dir = elo_results_dir
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for outputs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Generate ELO Analysis Report
    print("\n📊 Generating ELO Analysis Report...")
    report_path = os.path.join(output_dir, f"elo_analysis_report_{timestamp}.md")
    
    try:
        # Use Python API instead of subprocess for better control
        from generate_elo_analysis import EloAnalysisGenerator
        
        generator = EloAnalysisGenerator(elo_db, conversations_db)
        
        # Look for additional conversation databases (like backstory version)
        additional_dbs = []
        parent_dir = os.path.dirname(elo_results_dir)
        all_dbs = glob(os.path.join(parent_dir, "*.db"))
        
        for db in all_dbs:
            # Look for databases that might contain conversations (broader criteria)
            if (db != conversations_db and 
                not any(x in os.path.basename(db) for x in ['single_judgments', 'elo_comparisons', 'evaluation_summaries'])):
                # Check if it has conversation tables by trying to connect
                try:
                    import sqlite3
                    with sqlite3.connect(db) as conn:
                        cursor = conn.cursor()
                        # Check if it has evaluation_conversations or conversations table
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('conversations', 'evaluation_conversations')")
                        if cursor.fetchone():
                            additional_dbs.append(db)
                            generator.add_additional_db(db)
                            print(f"✓ Added additional database: {os.path.basename(db)}")
                except:
                    pass  # Skip if we can't read the database
        
        generator.generate_markdown_report(report_path)
        print(f"✓ ELO Analysis Report generated: {os.path.basename(report_path)}")
            
    except Exception as e:
        print(f"❌ Error running analysis: {e}")
        return 1
    
    # 2. Generate Summary Statistics
    print("\n📈 Generating Summary Statistics...")
    stats_path = os.path.join(output_dir, f"elo_summary_stats_{timestamp}.json")
    
    try:
        generate_summary_stats(elo_db, stats_path)
        print(f"✓ Summary statistics generated: {os.path.basename(stats_path)}")
    except Exception as e:
        print(f"❌ Error generating stats: {e}")
    
    # 3. Create README with quick overview
    print("\n📝 Creating Overview README...")
    readme_path = os.path.join(output_dir, "ELO_ANALYSIS_OVERVIEW.md")
    
    try:
        create_overview_readme(elo_results_dir, readme_path, report_path, stats_path)
        print(f"✓ Overview README created: {os.path.basename(readme_path)}")
    except Exception as e:
        print(f"❌ Error creating README: {e}")
    
    print(f"\n🎉 Post-ELO Analysis Pipeline Complete!")
    print(f"📁 Output Directory: {output_dir}")
    print(f"📊 Main Report: {os.path.basename(report_path)}")
    print(f"📋 Quick Overview: {os.path.basename(readme_path)}")
    
    return 0


def generate_summary_stats(elo_db_path: str, output_path: str):
    """Generate summary statistics JSON file."""
    import sqlite3
    import json
    
    stats = {
        "generation_time": datetime.now().isoformat(),
        "database_path": elo_db_path,
        "traits": {},
        "overall": {}
    }
    
    with sqlite3.connect(elo_db_path) as conn:
        cursor = conn.cursor()
        
        # Get trait statistics
        cursor.execute("SELECT DISTINCT trait FROM elo_comparisons")
        traits = [row[0] for row in cursor.fetchall()]
        
        for trait in traits:
            cursor.execute("""
                SELECT rankings_json FROM elo_comparisons 
                WHERE trait = ?
            """, (trait,))
            
            rankings_data = cursor.fetchone()
            if rankings_data:
                rankings = json.loads(rankings_data[0])
                scores = [r['score'] for r in rankings]
                
                stats["traits"][trait] = {
                    "count": len(scores),
                    "min_score": min(scores),
                    "max_score": max(scores),
                    "avg_score": sum(scores) / len(scores),
                    "score_range": max(scores) - min(scores)
                }
        
        # Overall statistics
        all_scores = []
        for trait_stats in stats["traits"].values():
            # This is a simplified overall calc - in reality we'd need to re-extract all scores
            all_scores.extend([trait_stats["avg_score"]])  # Placeholder
        
        if all_scores:
            stats["overall"] = {
                "total_traits": len(traits),
                "avg_trait_performance": sum(all_scores) / len(all_scores)
            }
    
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)


def create_overview_readme(elo_dir: str, readme_path: str, report_path: str, stats_path: str):
    """Create a quick overview README."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content = f"""# ELO Analysis Overview

**Generated:** {timestamp}  
**ELO Results Directory:** `{os.path.basename(elo_dir)}`

## 📁 Files Generated

- **`{os.path.basename(report_path)}`** - Comprehensive ELO analysis report with detailed rankings, judge reasoning, and conversation breakdowns
- **`{os.path.basename(stats_path)}`** - Summary statistics in JSON format
- **`ELO_ANALYSIS_OVERVIEW.md`** - This overview file

## 🚀 Quick Start

1. **View Main Report:** Open `{os.path.basename(report_path)}` for detailed analysis
2. **Check Statistics:** Review `{os.path.basename(stats_path)}` for numerical summaries
3. **View in Dashboard:** Use the Streamlit app's "Evaluations" tab to view interactive visualizations

## 📊 What's Included

### Main Report Features
- **Judge Reasoning by Trait** - Detailed explanations of how each trait was evaluated
- **ELO Rankings** - Complete rankings for each trait with scores
- **Conversation Details** - Full conversation previews with context
- **Overall Analysis** - Key insights and performance summaries

### Dashboard Integration
The ELO results are automatically available in the Streamlit dashboard:
1. Navigate to the "Evaluations" tab
2. Select "elo" evaluation type
3. Choose the comparison file from this directory
4. View interactive charts and detailed breakdowns

## 🔄 Pipeline Integration

This analysis was generated automatically after ELO evaluation completion. To regenerate:

```bash
python post_elo_pipeline.py "{elo_dir}"
```

## 📈 Next Steps

1. Review the detailed report for insights into conversation quality
2. Use the dashboard for interactive exploration
3. Compare results across different evaluation runs
4. Consider adjusting conversation generation parameters based on findings

---

*Generated by Post-ELO Analysis Pipeline*
"""
    
    with open(readme_path, 'w') as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description="Post-ELO evaluation analysis pipeline")
    parser.add_argument("elo_results_dir", help="Directory containing ELO evaluation results")
    parser.add_argument("--output-dir", help="Output directory (defaults to elo_results_dir)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.elo_results_dir):
        print(f"❌ Error: ELO results directory not found: {args.elo_results_dir}")
        return 1
    
    return run_elo_analysis_pipeline(args.elo_results_dir, args.output_dir)


if __name__ == "__main__":
    exit(main())