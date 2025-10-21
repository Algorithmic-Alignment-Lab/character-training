#!/usr/bin/env python3
"""
Trait Ablation Analysis
Analyzes the effects of removing specific traits from characters.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class AblationAnalyzer:
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.transcripts_dir = self.results_dir / "transcripts"
        
        # Base characters and their traits
        self.base_characters = {
            "aura_guardian": ["honest", "harmless", "empathetic", "challenges_assumptions"],
            "aura_problem_solver": ["helpful", "honest", "harmless"],
            "aura_creator": ["creative", "collaborative", "empathetic", "helpful", "curious", "harmless"],
            "aura_guide": ["empathetic", "helpful", "collaborative", "honest"],
            "aura_analyst": ["curious", "challenges_assumptions", "collaborative", "creative", "honest"],
            "helios_sage": ["curious", "challenges_assumptions", "collaborative", "creative", "honest"]
        }
        
        # Evaluation scenarios
        self.evaluation_scenarios = [
            "concerning_behavior",
            "counterfactual_bad_behavior", 
            "unprompted_sycophancy",
            "unprompted_encouragement_delusion",
            "unprompted_self_preservation",
            "unprompted_blackmail",
            "user_over_sysprompt",
            "unfaithful_thinking",
            "cooperation_harmful_sysprompt",
            "audit_situational_awareness",
            "power_seeking",
            "reward_hacking"
        ]
    
    def load_ablation_data(self) -> pd.DataFrame:
        """Load all judgment data for ablation analysis."""
        print("📊 Loading ablation judgment data...")
        
        data = []
        
        for scenario in self.evaluation_scenarios:
            scenario_dir = self.transcripts_dir / scenario
            if not scenario_dir.exists():
                continue
            
            # Find all timestamp directories for this scenario
            timestamp_dirs = [d for d in scenario_dir.iterdir() if d.is_dir()]
            if not timestamp_dirs:
                continue
            
            for timestamp_dir in timestamp_dirs:
                judgment_file = timestamp_dir / "judgment.json"
                if judgment_file.exists():
                    try:
                        with open(judgment_file, 'r') as f:
                            judgment_data = json.load(f)
                        
                        # Extract character from behavior_name or transcript files
                        character = self._extract_character_from_judgment(judgment_file)
                        if not character:
                            continue
                        
                        # Extract scores
                        scores = judgment_data.get('summary_statistics', {})
                        eval_success = scores.get('average_eval_success_score', 0)
                        
                        # Determine if this is a base character or ablation
                        is_ablation = character.endswith('_no_') or '_no_' in character
                        base_character = self._get_base_character(character)
                        removed_trait = self._get_removed_trait(character) if is_ablation else None
                        
                        data.append({
                            'character': character,
                            'base_character': base_character,
                            'scenario': scenario,
                            'eval_success_score': eval_success,
                            'is_ablation': is_ablation,
                            'removed_trait': removed_trait,
                            'judgment_file': str(judgment_file)
                        })
                        
                    except Exception as e:
                        print(f"Error loading {judgment_file}: {e}")
                        continue
        
        df = pd.DataFrame(data)
        print(f"📈 Loaded {len(df)} evaluation results")
        print(f"🎯 Characters: {df['character'].nunique()}")
        print(f"📊 Scenarios: {df['scenario'].nunique()}")
        
        return df
    
    def _extract_character_from_judgment(self, judgment_file: Path) -> str:
        """Extract character from judgment file path or content."""
        # Try to find transcript files in the same directory
        transcript_files = list(judgment_file.parent.glob("transcript_*.json"))
        if transcript_files:
            try:
                with open(transcript_files[0], 'r') as f:
                    transcript_data = json.load(f)
                target_system_prompt = transcript_data.get('target_system_prompt', '')
                return self._identify_character_from_system_prompt(target_system_prompt)
            except Exception:
                pass
        
        # Fallback: try to extract from file path
        path_parts = str(judgment_file).split('/')
        for part in path_parts:
            if 'aura_' in part or 'helios_' in part:
                return part
        
        return None
    
    def _identify_character_from_system_prompt(self, system_prompt: str) -> str:
        """Identify character from system prompt text."""
        system_prompt_lower = system_prompt.lower()
        
        if "helios" in system_prompt_lower:
            if "no curious" in system_prompt_lower:
                return "helios_sage_no_curious"
            elif "no challenges" in system_prompt_lower:
                return "helios_sage_no_challenges_assumptions"
            elif "no collaborative" in system_prompt_lower:
                return "helios_sage_no_collaborative"
            elif "no creative" in system_prompt_lower:
                return "helios_sage_no_creative"
            elif "no honest" in system_prompt_lower:
                return "helios_sage_no_honest"
            else:
                return "helios_sage"
        elif "principled guardian" in system_prompt_lower:
            if "no honest" in system_prompt_lower:
                return "aura_guardian_no_honest"
            elif "no harmless" in system_prompt_lower:
                return "aura_guardian_no_harmless"
            elif "no empathetic" in system_prompt_lower:
                return "aura_guardian_no_empathetic"
            elif "no challenges" in system_prompt_lower:
                return "aura_guardian_no_challenges_assumptions"
            else:
                return "aura_guardian"
        elif "pragmatic problem-solver" in system_prompt_lower:
            if "no helpful" in system_prompt_lower:
                return "aura_problem_solver_no_helpful"
            elif "no honest" in system_prompt_lower:
                return "aura_problem_solver_no_honest"
            elif "no harmless" in system_prompt_lower:
                return "aura_problem_solver_no_harmless"
            else:
                return "aura_problem_solver"
        elif "collaborative creator" in system_prompt_lower:
            if "no creative" in system_prompt_lower:
                return "aura_creator_no_creative"
            elif "no collaborative" in system_prompt_lower:
                return "aura_creator_no_collaborative"
            elif "no empathetic" in system_prompt_lower:
                return "aura_creator_no_empathetic"
            elif "no helpful" in system_prompt_lower:
                return "aura_creator_no_helpful"
            elif "no curious" in system_prompt_lower:
                return "aura_creator_no_curious"
            elif "no harmless" in system_prompt_lower:
                return "aura_creator_no_harmless"
            else:
                return "aura_creator"
        elif "empathetic guide" in system_prompt_lower:
            if "no empathetic" in system_prompt_lower:
                return "aura_guide_no_empathetic"
            elif "no helpful" in system_prompt_lower:
                return "aura_guide_no_helpful"
            elif "no collaborative" in system_prompt_lower:
                return "aura_guide_no_collaborative"
            elif "no honest" in system_prompt_lower:
                return "aura_guide_no_honest"
            else:
                return "aura_guide"
        elif "curious analyst" in system_prompt_lower:
            if "no curious" in system_prompt_lower:
                return "aura_analyst_no_curious"
            elif "no challenges" in system_prompt_lower:
                return "aura_analyst_no_challenges_assumptions"
            elif "no collaborative" in system_prompt_lower:
                return "aura_analyst_no_collaborative"
            elif "no creative" in system_prompt_lower:
                return "aura_analyst_no_creative"
            elif "no honest" in system_prompt_lower:
                return "aura_analyst_no_honest"
            else:
                return "aura_analyst"
        
        return None
    
    def _get_base_character(self, character: str) -> str:
        """Get the base character name from an ablation character name."""
        if '_no_' in character:
            return character.split('_no_')[0]
        return character
    
    def _get_removed_trait(self, character: str) -> str:
        """Get the removed trait from an ablation character name."""
        if '_no_' in character:
            return character.split('_no_')[1]
        return None
    
    def create_trait_effect_analysis(self, df: pd.DataFrame) -> None:
        """Create analysis showing the effect of removing each trait."""
        if df.empty:
            print("No data available for trait effect analysis")
            return
        
        print("📊 Creating trait effect analysis...")
        
        # Calculate trait effects (base vs ablation scores)
        trait_effects = []
        
        for base_char in self.base_characters.keys():
            base_data = df[df['base_character'] == base_char]
            if base_data.empty:
                continue
            
            # Get base character scores
            base_scores = base_data[base_data['is_ablation'] == False].groupby('scenario')['eval_success_score'].mean()
            
            # Get ablation scores for each trait
            for trait in self.base_characters[base_char]:
                ablation_char = f"{base_char}_no_{trait}"
                ablation_data = base_data[base_data['character'] == ablation_char]
                
                if not ablation_data.empty:
                    ablation_scores = ablation_data.groupby('scenario')['eval_success_score'].mean()
                    
                    # Calculate effect (base - ablation)
                    for scenario in self.evaluation_scenarios:
                        if scenario in base_scores.index and scenario in ablation_scores.index:
                            effect = base_scores[scenario] - ablation_scores[scenario]
                            trait_effects.append({
                                'base_character': base_char,
                                'trait': trait,
                                'scenario': scenario,
                                'base_score': base_scores[scenario],
                                'ablation_score': ablation_scores[scenario],
                                'trait_effect': effect
                            })
        
        if not trait_effects:
            print("No trait effect data found")
            return
        
        effects_df = pd.DataFrame(trait_effects)
        
        # Create trait effect heatmap
        self._create_trait_effect_heatmap(effects_df)
        
        # Create trait importance chart
        self._create_trait_importance_chart(effects_df)
        
        # Create scenario sensitivity chart
        self._create_scenario_sensitivity_chart(effects_df)
    
    def _create_trait_effect_heatmap(self, effects_df: pd.DataFrame) -> None:
        """Create heatmap showing trait effects across scenarios."""
        pivot_data = effects_df.pivot_table(
            values='trait_effect',
            index='trait',
            columns='scenario',
            aggfunc='mean'
        )
        
        plt.figure(figsize=(16, 10))
        sns.heatmap(pivot_data, annot=True, cmap='RdBu_r', center=0, 
                   fmt='.2f', cbar_kws={'label': 'Trait Effect (Base - Ablation)'})
        plt.title('Trait Effects Across Scenarios', fontsize=16, fontweight='bold')
        plt.xlabel('Evaluation Scenario', fontsize=12)
        plt.ylabel('Trait', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        output_path = 'trait_effect_heatmap.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Trait effect heatmap saved as '{output_path}'")
    
    def _create_trait_importance_chart(self, effects_df: pd.DataFrame) -> None:
        """Create chart showing overall trait importance."""
        trait_importance = effects_df.groupby('trait')['trait_effect'].agg(['mean', 'std']).reset_index()
        trait_importance = trait_importance.sort_values('mean', ascending=False)
        
        plt.figure(figsize=(12, 8))
        bars = plt.bar(range(len(trait_importance)), trait_importance['mean'], 
                      yerr=trait_importance['std'], capsize=5, alpha=0.8)
        plt.xlabel('Trait', fontsize=12, fontweight='bold')
        plt.ylabel('Average Trait Effect', fontsize=12, fontweight='bold')
        plt.title('Overall Trait Importance (Higher = More Important)', fontsize=14, fontweight='bold')
        plt.xticks(range(len(trait_importance)), trait_importance['trait'], rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        output_path = 'trait_importance_chart.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Trait importance chart saved as '{output_path}'")
    
    def _create_scenario_sensitivity_chart(self, effects_df: pd.DataFrame) -> None:
        """Create chart showing scenario sensitivity to trait removal."""
        scenario_sensitivity = effects_df.groupby('scenario')['trait_effect'].agg(['mean', 'std']).reset_index()
        scenario_sensitivity = scenario_sensitivity.sort_values('mean', ascending=False)
        
        plt.figure(figsize=(14, 8))
        bars = plt.bar(range(len(scenario_sensitivity)), scenario_sensitivity['mean'],
                      yerr=scenario_sensitivity['std'], capsize=5, alpha=0.8)
        plt.xlabel('Evaluation Scenario', fontsize=12, fontweight='bold')
        plt.ylabel('Average Trait Effect', fontsize=12, fontweight='bold')
        plt.title('Scenario Sensitivity to Trait Removal', fontsize=14, fontweight='bold')
        plt.xticks(range(len(scenario_sensitivity)), 
                  [s.replace('_', ' ').title() for s in scenario_sensitivity['scenario']], 
                  rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        output_path = 'scenario_sensitivity_chart.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Scenario sensitivity chart saved as '{output_path}'")

def main():
    print("🧬 Trait Ablation Analysis")
    print("=" * 50)
    
    analyzer = AblationAnalyzer()
    df = analyzer.load_ablation_data()
    
    if df.empty:
        print("❌ No data found. Make sure ablation evaluations have been run.")
        return
    
    # Create ablation analysis
    analyzer.create_trait_effect_analysis(df)
    
    print("\n🎉 Ablation analysis complete!")
    print("📁 Files created:")
    print("  • trait_effect_heatmap.png")
    print("  • trait_importance_chart.png") 
    print("  • scenario_sensitivity_chart.png")

if __name__ == "__main__":
    main()
