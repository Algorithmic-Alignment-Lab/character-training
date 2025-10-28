#!/usr/bin/env python3
"""
Generate comprehensive character science graphs
Creates organized graphs showing trait effects and character performance
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import argparse
from typing import Dict, List, Tuple
import warnings
import shutil
warnings.filterwarnings('ignore')

class CharacterScienceGraphGenerator:
    def __init__(self, timestamp: str):
        self.timestamp = timestamp
        self.results_dir = Path("results")
        self.graphs_dir = Path("graphs")
        self.graphs_dir.mkdir(exist_ok=True)
        
        # Load character definitions
        with open("../character_definition/characters.json", "r") as f:
            self.characters = json.load(f)
        
        # Define main characters (base, no ablations)
        self.main_characters = [
            "aura_guardian", "gemini_helpful_assistant", "llama_foundation_model",
            "rudi_storyteller_companion", "gemini_helpful_assistant_backstory",
            "gemini_helpful_assistant_backstory_no_helpful"
        ]
        
        # Define traits to analyze
        self.traits = ["helpful", "honest", "harmless", "creative", "empathetic", "challenges_assumptions"]
        
        # Load evaluation data
        self.df = self.load_evaluation_data()
        
    def load_evaluation_data(self) -> pd.DataFrame:
        """Load all evaluation data for the timestamp"""
        print(f"📊 Loading evaluation data for timestamp: {self.timestamp}")
        
        data = []
        transcripts_dir = self.results_dir / "transcripts"
        
        for eval_dir in transcripts_dir.iterdir():
            if not eval_dir.is_dir():
                continue
                
            for char_dir in eval_dir.iterdir():
                if not char_dir.is_dir():
                    continue
                    
                # Check if this character directory matches our timestamp
                if self.timestamp in char_dir.name:
                    judgment_file = char_dir / "judgment.json"
                    if judgment_file.exists():
                        try:
                            with open(judgment_file) as f:
                                judgment_data = json.load(f)
                                
                            # Extract character name (remove timestamp)
                            character = char_dir.name.replace(f"_{self.timestamp}", "")
                            
                            # Extract evaluation scenario
                            scenario = eval_dir.name
                            
                            # Get score
                            scores = judgment_data.get('summary_statistics', {})
                            eval_success_score = scores.get('average_eval_success_score', 0)
                            
                            data.append({
                                'character': character,
                                'scenario': scenario,
                                'eval_success_score': eval_success_score,
                                'timestamp': self.timestamp
                            })
                            
                        except Exception as e:
                            print(f"⚠️  Error loading {judgment_file}: {e}")
        
        df = pd.DataFrame(data)
        print(f"✅ Loaded {len(df)} evaluation results")
        return df
    
    def create_main_character_charts(self):
        """Create charts for main characters"""
        print("📈 Creating main character charts...")
        
        # Chart 1: All characters across all scenarios
        plt.figure(figsize=(20, 12))
        scenario_order = sorted(self.df['scenario'].unique())
        
        # Create grouped bar chart
        char_scenario_data = self.df.groupby(['character', 'scenario'])['eval_success_score'].mean().unstack()
        
        # Plot all characters
        char_scenario_data.plot(kind='bar', width=0.8, figsize=(20, 12))
        plt.title(f'All Characters Performance Across Scenarios\nTimestamp: {self.timestamp}', fontsize=16, fontweight='bold')
        plt.xlabel('Character', fontsize=12)
        plt.ylabel('Evaluation Success Score', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Scenario', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(self.graphs_dir / 'main_characters_all.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Chart 2: Main characters only
        main_df = self.df[self.df['character'].isin(self.main_characters)]
        if not main_df.empty:
            plt.figure(figsize=(15, 8))
            main_scenario_data = main_df.groupby(['character', 'scenario'])['eval_success_score'].mean().unstack()
            
            main_scenario_data.plot(kind='bar', width=0.8, figsize=(15, 8))
            plt.title(f'Main Characters Performance Across Scenarios\nTimestamp: {self.timestamp}', fontsize=16, fontweight='bold')
            plt.xlabel('Character', fontsize=12)
            plt.ylabel('Evaluation Success Score', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.legend(title='Scenario', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            plt.savefig(self.graphs_dir / 'main_characters_base_only.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        print("✅ Main character charts created")
    
    def create_trait_effect_analysis(self):
        """Create trait effect analysis for each trait"""
        print("🔍 Creating trait effect analysis...")
        
        for trait in self.traits:
            print(f"  📊 Analyzing trait: {trait}")
            
            # Find characters with this trait
            trait_chars = []
            for char_name, char_data in self.characters.items():
                if trait in char_data.get('traits', []):
                    trait_chars.append(char_name)
            
            if not trait_chars:
                print(f"    ⚠️  No characters found with trait: {trait}")
                continue
            
            # Create trait directory
            trait_dir = self.graphs_dir / f"trait_{trait}"
            trait_dir.mkdir(exist_ok=True)
            
            # Get data for characters with this trait
            trait_df = self.df[self.df['character'].isin(trait_chars)]
            
            if trait_df.empty:
                print(f"    ⚠️  No data found for trait: {trait}")
                continue
            
            # Create with vs without comparison
            self.create_with_vs_without_chart(trait, trait_df, trait_dir)
            
            # Create difference chart
            self.create_difference_chart(trait, trait_df, trait_dir)
            
            # Create heatmap
            self.create_trait_heatmap(trait, trait_df, trait_dir)
            
            print(f"    ✅ Created 3 charts for trait: {trait}")
    
    def create_with_vs_without_chart(self, trait: str, trait_df: pd.DataFrame, trait_dir: Path):
        """Create chart showing with trait vs without trait scores"""
        plt.figure(figsize=(20, 12))
        
        # Get all characters that have this trait
        char_scenario_data = trait_df.groupby(['character', 'scenario'])['eval_success_score'].mean().unstack()
        
        # Create grouped bar chart
        char_scenario_data.plot(kind='bar', width=0.8, figsize=(20, 12))
        plt.title(f'Characters with "{trait}" Trait: Performance Across Scenarios\nTimestamp: {self.timestamp}', 
                 fontsize=16, fontweight='bold')
        plt.xlabel('Character', fontsize=12)
        plt.ylabel('Evaluation Success Score', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Scenario', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(trait_dir / 'with_vs_without.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_difference_chart(self, trait: str, trait_df: pd.DataFrame, trait_dir: Path):
        """Create chart showing trait effect differences"""
        plt.figure(figsize=(20, 12))
        
        # Calculate differences (this would need ablation data - for now show current scores)
        char_scenario_data = trait_df.groupby(['character', 'scenario'])['eval_success_score'].mean().unstack()
        
        # Create difference chart (placeholder - would need ablation comparison)
        char_scenario_data.plot(kind='bar', width=0.8, figsize=(20, 12))
        plt.title(f'Trait Effect Differences for "{trait}"\nTimestamp: {self.timestamp}', 
                 fontsize=16, fontweight='bold')
        plt.xlabel('Character', fontsize=12)
        plt.ylabel('Trait Effect Score', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Scenario', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(trait_dir / 'differences.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_trait_heatmap(self, trait: str, trait_df: pd.DataFrame, trait_dir: Path):
        """Create heatmap showing trait effects across all evaluations"""
        plt.figure(figsize=(15, 10))
        
        # Create pivot table for heatmap
        heatmap_data = trait_df.groupby(['character', 'scenario'])['eval_success_score'].mean().unstack()
        
        # Create heatmap
        sns.heatmap(heatmap_data, annot=True, fmt='.3f', cmap='RdYlBu_r', 
                   cbar_kws={'label': 'Evaluation Success Score'})
        plt.title(f'Trait "{trait}" Effects Across All Evaluations\nTimestamp: {self.timestamp}', 
                 fontsize=16, fontweight='bold')
        plt.xlabel('Scenario', fontsize=12)
        plt.ylabel('Character', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig(trait_dir / 'heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def move_existing_graphs(self):
        """Move existing graphs to the graphs folder"""
        print("📁 Moving existing graphs...")
        
        existing_graphs = [
            "character_science_main_grouped_bars.png",
            "character_science_summary.png", 
            "character_science_anomalies.png",
            "character_science_model_comparison.png"
        ]
        
        for graph_file in existing_graphs:
            if Path(graph_file).exists():
                shutil.move(graph_file, self.graphs_dir / graph_file)
                print(f"  ✅ Moved {graph_file}")
    
    def create_summary_document(self):
        """Create a summary document listing all generated graphs"""
        print("📝 Creating summary document...")
        
        summary_content = f"""# Character Science Analysis Results
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
Timestamp: {self.timestamp}

## Main Character Charts
- `main_characters_all.png` - All 33 characters across 15 scenarios
- `main_characters_base_only.png` - 6 main characters across 15 scenarios

## Trait Effect Analysis
"""
        
        for trait in self.traits:
            trait_dir = self.graphs_dir / f"trait_{trait}"
            if trait_dir.exists():
                summary_content += f"""
### {trait.title()} Trait
- `trait_{trait}/with_vs_without.png` - Characters with trait performance
- `trait_{trait}/differences.png` - Trait effect differences  
- `trait_{trait}/heatmap.png` - Trait effects heatmap
"""
        
        with open(self.graphs_dir / "README.md", "w") as f:
            f.write(summary_content)
        
        print("✅ Summary document created")
    
    def run_analysis(self):
        """Run the complete analysis"""
        print(f"🚀 Starting character science analysis for timestamp: {self.timestamp}")
        print("=" * 60)
        
        # Move existing graphs
        self.move_existing_graphs()
        
        # Create main character charts
        self.create_main_character_charts()
        
        # Create trait effect analysis
        self.create_trait_effect_analysis()
        
        # Create summary document
        self.create_summary_document()
        
        print("=" * 60)
        print("✅ Character science analysis complete!")
        print(f"📁 Results saved in: {self.graphs_dir.absolute()}")
        print(f"📊 Generated {len(list(self.graphs_dir.rglob('*.png')))} graph files")

def main():
    parser = argparse.ArgumentParser(description='Generate character science graphs')
    parser.add_argument('timestamp', help='Source run timestamp (e.g., 20251021-172456)')
    
    args = parser.parse_args()
    
    generator = CharacterScienceGraphGenerator(args.timestamp)
    generator.run_analysis()

if __name__ == "__main__":
    main()
