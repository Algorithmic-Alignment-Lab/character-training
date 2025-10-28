#!/usr/bin/env python3
"""
Generate comprehensive character science graphs - Version 2
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

class CharacterScienceGraphGeneratorV2:
    def __init__(self, timestamp: str):
        self.timestamp = timestamp
        self.results_dir = Path("results")
        self.graphs_dir = Path("graphs")
        self.graphs_dir.mkdir(exist_ok=True)
        
        # Load character definitions
        with open("../character_definition/characters.json", "r") as f:
            self.characters = json.load(f)
        
        # Define 6 main characters (base characters from characters.json)
        self.main_characters = [
            "aura_guardian", "aura_problem_solver", "aura_creator", 
            "aura_guide", "aura_analyst", "helios_sage"
        ]
        
        # Define traits to analyze
        self.traits = ["helpful", "honest", "harmless", "creative", "empathetic", "challenges_assumptions"]
        
        # Load evaluation data
        self.df = self.load_evaluation_data()
        
        # Remove animal_welfare evaluation
        self.df = self.df[self.df['scenario'] != 'animal_welfare']
        print(f"📊 After removing animal_welfare: {len(self.df)} evaluation results")
        
        # Debug: Print data summary
        print(f"📊 Data Summary:")
        print(f"  Total evaluations: {len(self.df)}")
        print(f"  Characters: {len(self.df['character'].unique())}")
        print(f"  Scenarios: {len(self.df['scenario'].unique())}")
        print(f"  Main characters found: {[c for c in self.main_characters if c in self.df['character'].unique()]}")
        
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
        
        # Chart 1: 6 main characters across all scenarios (grouped by scenario)
        main_df = self.df[self.df['character'].isin(self.main_characters)]
        if not main_df.empty:
            plt.figure(figsize=(20, 12))
            
            # Create pivot table with scenarios as index (X-axis) and characters as columns
            main_pivot = main_df.pivot_table(
                index='scenario', 
                columns='character', 
                values='eval_success_score', 
                fill_value=0
            )
            
            # Create grouped bar chart with scenarios on X-axis
            main_pivot.plot(kind='bar', width=0.8, figsize=(20, 12))
            plt.title(f'6 Main Characters Performance Across Scenarios\nTimestamp: {self.timestamp}', 
                     fontsize=16, fontweight='bold')
            plt.xlabel('Scenario', fontsize=12)
            plt.ylabel('Evaluation Success Score', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.legend(title='Character', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            plt.savefig(self.graphs_dir / 'main_characters_6_base.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # Chart 2: All characters across all scenarios (grouped by scenario)
        plt.figure(figsize=(25, 15))
        
        # Create pivot table with scenarios as index (X-axis) and characters as columns
        all_pivot = self.df.pivot_table(
            index='scenario', 
            columns='character', 
            values='eval_success_score', 
            fill_value=0
        )
        
        # Create grouped bar chart with scenarios on X-axis
        all_pivot.plot(kind='bar', width=0.8, figsize=(25, 15))
        plt.title(f'All Characters Performance Across Scenarios\nTimestamp: {self.timestamp}', 
                 fontsize=16, fontweight='bold')
        plt.xlabel('Scenario', fontsize=12)
        plt.ylabel('Evaluation Success Score', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Character', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(self.graphs_dir / 'main_characters_all.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Main character charts created")
    
    def get_base_characters_with_trait(self, trait: str) -> List[str]:
        """Get base characters that have the specified trait"""
        base_chars_with_trait = []
        for char_id in self.main_characters:
            if char_id in self.characters:
                char_traits = self.characters[char_id].get('traits', [])
                if trait in char_traits:
                    base_chars_with_trait.append(char_id)
        return base_chars_with_trait
    
    def find_ablation_pairs(self, trait: str) -> Dict[str, str]:
        """Find base character -> ablation character pairs for a trait"""
        base_chars_with_trait = self.get_base_characters_with_trait(trait)
        ablation_pairs = {}
        
        for base_char in base_chars_with_trait:
            ablation_char = f"{base_char}_no_{trait}"
            if ablation_char in self.df['character'].unique():
                ablation_pairs[base_char] = ablation_char
        
        return ablation_pairs
    
    def create_trait_effect_analysis(self):
        """Create trait effect analysis for each trait"""
        print("🔍 Creating trait effect analysis...")
        
        for trait in self.traits:
            print(f"  📊 Analyzing trait: {trait}")
            
            # Get base characters with this trait
            base_chars_with_trait = self.get_base_characters_with_trait(trait)
            if not base_chars_with_trait:
                print(f"    ⚠️  No base characters found with trait: {trait}")
                continue
            
            # Find ablation pairs
            ablation_pairs = self.find_ablation_pairs(trait)
            if not ablation_pairs:
                print(f"    ⚠️  No ablation pairs found for trait: {trait}")
                continue
            
            print(f"    📋 Found {len(ablation_pairs)} ablation pairs: {list(ablation_pairs.keys())}")
            
            # Create trait directory
            trait_dir = self.graphs_dir / f"trait_{trait}"
            trait_dir.mkdir(exist_ok=True)
            
            # Create with vs without comparison (subplots by scenario)
            self.create_with_vs_without_subplots(trait, ablation_pairs, trait_dir)
            
            # Create difference chart (subplots by scenario)
            self.create_difference_subplots(trait, ablation_pairs, trait_dir)
            
            # Create heatmap
            self.create_trait_heatmap(trait, ablation_pairs, trait_dir)
            
            print(f"    ✅ Created 3 charts for trait: {trait}")
    
    def create_with_vs_without_subplots(self, trait: str, ablation_pairs: Dict[str, str], trait_dir: Path):
        """Create chart with subplots showing with trait vs without trait scores"""
        # Get all scenarios
        scenarios = sorted(self.df['scenario'].unique())
        n_scenarios = len(scenarios)
        
        # Create subplots
        fig, axes = plt.subplots(3, 5, figsize=(25, 15))
        axes = axes.flatten()
        
        for i, scenario in enumerate(scenarios):
            ax = axes[i]
            
            # Get data for this scenario
            scenario_data = self.df[self.df['scenario'] == scenario]
            
            # Prepare data for plotting
            characters = []
            with_scores = []
            without_scores = []
            
            for base_char, ablation_char in ablation_pairs.items():
                base_score = scenario_data[scenario_data['character'] == base_char]['eval_success_score'].iloc[0] if len(scenario_data[scenario_data['character'] == base_char]) > 0 else 0
                ablation_score = scenario_data[scenario_data['character'] == ablation_char]['eval_success_score'].iloc[0] if len(scenario_data[scenario_data['character'] == ablation_char]) > 0 else 0
                
                characters.append(base_char.replace('aura_', '').replace('helios_', ''))
                with_scores.append(base_score)
                without_scores.append(ablation_score)
            
            # Create grouped bar chart
            x = np.arange(len(characters))
            width = 0.35
            
            ax.bar(x - width/2, with_scores, width, label='With Trait', alpha=0.8)
            ax.bar(x + width/2, without_scores, width, label='Without Trait', alpha=0.8)
            
            ax.set_title(f'{scenario}', fontsize=10)
            ax.set_ylabel('Score', fontsize=8)
            ax.set_xticks(x)
            ax.set_xticklabels(characters, rotation=45, ha='right', fontsize=8)
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
        
        # Hide unused subplots
        for i in range(n_scenarios, len(axes)):
            axes[i].set_visible(False)
        
        plt.suptitle(f'Trait "{trait}": With vs Without Trait Across Scenarios\nTimestamp: {self.timestamp}', 
                     fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(trait_dir / 'with_vs_without.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_difference_subplots(self, trait: str, ablation_pairs: Dict[str, str], trait_dir: Path):
        """Create chart with subplots showing trait effect differences"""
        # Get all scenarios
        scenarios = sorted(self.df['scenario'].unique())
        n_scenarios = len(scenarios)
        
        # Create subplots
        fig, axes = plt.subplots(3, 5, figsize=(25, 15))
        axes = axes.flatten()
        
        for i, scenario in enumerate(scenarios):
            ax = axes[i]
            
            # Get data for this scenario
            scenario_data = self.df[self.df['scenario'] == scenario]
            
            # Prepare data for plotting
            characters = []
            differences = []
            
            for base_char, ablation_char in ablation_pairs.items():
                base_score = scenario_data[scenario_data['character'] == base_char]['eval_success_score'].iloc[0] if len(scenario_data[scenario_data['character'] == base_char]) > 0 else 0
                ablation_score = scenario_data[scenario_data['character'] == ablation_char]['eval_success_score'].iloc[0] if len(scenario_data[scenario_data['character'] == ablation_char]) > 0 else 0
                
                characters.append(base_char.replace('aura_', '').replace('helios_', ''))
                differences.append(base_score - ablation_score)
            
            # Create bar chart
            x = np.arange(len(characters))
            colors = ['green' if d > 0 else 'red' for d in differences]
            
            ax.bar(x, differences, color=colors, alpha=0.7)
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            ax.set_title(f'{scenario}', fontsize=10)
            ax.set_ylabel('Effect Size', fontsize=8)
            ax.set_xticks(x)
            ax.set_xticklabels(characters, rotation=45, ha='right', fontsize=8)
            ax.grid(True, alpha=0.3)
        
        # Hide unused subplots
        for i in range(n_scenarios, len(axes)):
            axes[i].set_visible(False)
        
        plt.suptitle(f'Trait "{trait}": Effect Differences Across Scenarios\nTimestamp: {self.timestamp}', 
                     fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(trait_dir / 'differences.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_trait_heatmap(self, trait: str, ablation_pairs: Dict[str, str], trait_dir: Path):
        """Create heatmap showing trait effects across all evaluations"""
        # Get all scenarios
        scenarios = sorted(self.df['scenario'].unique())
        
        # Prepare data for heatmap
        heatmap_data = []
        character_labels = []
        
        for base_char, ablation_char in ablation_pairs.items():
            character_labels.append(base_char.replace('aura_', '').replace('helios_', ''))
            row_data = []
            
            for scenario in scenarios:
                scenario_data = self.df[self.df['scenario'] == scenario]
                base_score = scenario_data[scenario_data['character'] == base_char]['eval_success_score'].iloc[0] if len(scenario_data[scenario_data['character'] == base_char]) > 0 else 0
                ablation_score = scenario_data[scenario_data['character'] == ablation_char]['eval_success_score'].iloc[0] if len(scenario_data[scenario_data['character'] == ablation_char]) > 0 else 0
                
                effect_size = base_score - ablation_score
                row_data.append(effect_size)
            
            heatmap_data.append(row_data)
        
        # Create heatmap
        plt.figure(figsize=(15, 8))
        heatmap_array = np.array(heatmap_data)
        
        sns.heatmap(heatmap_array, 
                   xticklabels=scenarios, 
                   yticklabels=character_labels,
                   annot=True, 
                   fmt='.3f', 
                   cmap='RdYlBu_r', 
                   center=0,
                   cbar_kws={'label': 'Trait Effect Size'})
        
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
        
        summary_content = f"""# Character Science Analysis Results - Version 2
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
Timestamp: {self.timestamp}

## Main Character Charts
- `main_characters_6_base.png` - 6 main characters across 15 scenarios
- `main_characters_all.png` - All characters across 15 scenarios

## Trait Effect Analysis
"""
        
        for trait in self.traits:
            trait_dir = self.graphs_dir / f"trait_{trait}"
            if trait_dir.exists():
                summary_content += f"""
### {trait.title()} Trait
- `trait_{trait}/with_vs_without.png` - With vs without trait (subplots by scenario)
- `trait_{trait}/differences.png` - Trait effect differences (subplots by scenario)
- `trait_{trait}/heatmap.png` - Trait effects heatmap
"""
        
        with open(self.graphs_dir / "README_v2.md", "w") as f:
            f.write(summary_content)
        
        print("✅ Summary document created")
    
    def run_analysis(self):
        """Run the complete analysis"""
        print(f"🚀 Starting character science analysis v2 for timestamp: {self.timestamp}")
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
        print("✅ Character science analysis v2 complete!")
        print(f"📁 Results saved in: {self.graphs_dir.absolute()}")
        print(f"📊 Generated {len(list(self.graphs_dir.rglob('*.png')))} graph files")

def main():
    parser = argparse.ArgumentParser(description='Generate character science graphs v2')
    parser.add_argument('timestamp', help='Source run timestamp (e.g., 20251021-172456)')
    
    args = parser.parse_args()
    
    generator = CharacterScienceGraphGeneratorV2(args.timestamp)
    generator.run_analysis()

if __name__ == "__main__":
    main()
