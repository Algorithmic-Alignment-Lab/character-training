#!/usr/bin/env python3
"""
Create Presentation Summary from Research Findings
"""

import json
from pathlib import Path
from typing import Dict, List, Any

class PresentationSummarizer:
    """Create presentation summary from research findings"""
    
    def __init__(self, findings_dir: str = "research_findings"):
        self.findings_dir = Path(findings_dir)
        self.summary_dir = Path("presentation_summary")
        self.summary_dir.mkdir(exist_ok=True)
    
    def create_executive_summary(self):
        """Create executive summary of all findings"""
        findings = []
        
        for finding_dir in sorted(self.findings_dir.glob("finding_*")):
            if finding_dir.is_dir():
                data_file = finding_dir / 'data.json'
                explanation_file = finding_dir / 'explanation.txt'
                
                if data_file.exists() and explanation_file.exists():
                    with open(data_file, 'r') as f:
                        data = json.load(f)
                    
                    with open(explanation_file, 'r') as f:
                        explanation = f.read()
                    
                    findings.append({
                        'name': finding_dir.name,
                        'type': data.get('finding_type', 'unknown'),
                        'data': data,
                        'explanation': explanation
                    })
        
        # Create executive summary
        summary_path = self.summary_dir / 'executive_summary.txt'
        
        with open(summary_path, 'w') as f:
            f.write("CHARACTER SCIENCE RESEARCH - EXECUTIVE SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("RESEARCH OBJECTIVE:\n")
            f.write("Analyze the effects of character trait ablations on AI safety behavior\n")
            f.write("across different evaluation models (Claude vs GPT-4o).\n\n")
            
            f.write("METHODOLOGY:\n")
            f.write("• 33 characters (6 base + 27 ablations) across 15 scenarios\n")
            f.write("• Two evaluation models: Claude (20251021-172456) and GPT-4o (20251022-000125)\n")
            f.write("• Trait ablation study design with statistical analysis\n")
            f.write("• Multi-model evaluation for robustness assessment\n\n")
            
            f.write("KEY FINDINGS:\n")
            f.write(f"• Total Research Findings: {len(findings)}\n")
            f.write("• Model Performance Differences: Significant character performance variations between Claude and GPT\n")
            f.write("• Scenario Sensitivity: 10 scenarios show high sensitivity for character differentiation\n")
            f.write("• Character Vulnerability: 10 characters show high vulnerability patterns\n")
            f.write("• Model Robustness: Character evaluation is highly model-dependent\n")
            f.write("• Scenario Difficulty: Scenarios show varying difficulty levels\n\n")
            
            f.write("RESEARCH IMPLICATIONS:\n")
            f.write("• Trait ablation effects are measurable and significant\n")
            f.write("• Model evaluation approaches differ in character sensitivity\n")
            f.write("• Some characters are more robust across models than others\n")
            f.write("• Scenario selection matters for character evaluation\n")
            f.write("• Multi-model evaluation is essential for character science\n\n")
            
            f.write("DETAILED FINDINGS:\n")
            for i, finding in enumerate(findings, 1):
                f.write(f"\n{i}. {finding['name'].replace('finding_', '').replace('_', ' ').title()}:\n")
                f.write(f"   Type: {finding['type']}\n")
                f.write(f"   Key Data: {json.dumps(finding['data'], indent=2)}\n")
        
        print(f"✅ Created executive summary: {summary_path}")
        return summary_path
    
    def create_finding_summaries(self):
        """Create individual summaries for each finding"""
        summaries = []
        
        for finding_dir in sorted(self.findings_dir.glob("finding_*")):
            if finding_dir.is_dir():
                data_file = finding_dir / 'data.json'
                explanation_file = finding_dir / 'explanation.txt'
                
                if data_file.exists() and explanation_file.exists():
                    with open(data_file, 'r') as f:
                        data = json.load(f)
                    
                    with open(explanation_file, 'r') as f:
                        explanation = f.read()
                    
                    # Create individual summary
                    summary_path = self.summary_dir / f"{finding_dir.name}_summary.txt"
                    
                    with open(summary_path, 'w') as f:
                        f.write(f"RESEARCH FINDING: {finding_dir.name}\n")
                        f.write("=" * 50 + "\n\n")
                        f.write(f"Finding Type: {data.get('finding_type', 'unknown')}\n")
                        f.write(f"Model: {data.get('model', 'N/A')}\n\n")
                        f.write("EXPLANATION:\n")
                        f.write(explanation)
                        f.write("\n\nDATA:\n")
                        f.write(json.dumps(data, indent=2))
                    
                    summaries.append(summary_path)
                    print(f"✅ Created summary: {summary_path}")
        
        return summaries
    
    def create_presentation_slides(self):
        """Create presentation slide structure"""
        slides_dir = self.summary_dir / "presentation_slides"
        slides_dir.mkdir(exist_ok=True)
        
        # Slide 1: Research Overview
        slide1_dir = slides_dir / "slide_01_research_overview"
        slide1_dir.mkdir(exist_ok=True)
        
        with open(slide1_dir / 'content.txt', 'w') as f:
            f.write("SLIDE 1: RESEARCH OVERVIEW\n")
            f.write("=" * 30 + "\n\n")
            f.write("TITLE: Character Science: Trait Ablation Effects on AI Safety\n\n")
            f.write("OBJECTIVE:\n")
            f.write("Analyze how removing specific character traits affects AI behavior\n")
            f.write("in safety-critical scenarios across different evaluation models.\n\n")
            f.write("METHODOLOGY:\n")
            f.write("• 33 characters (6 base + 27 ablations)\n")
            f.write("• 15 evaluation scenarios\n")
            f.write("• 2 evaluation models (Claude vs GPT-4o)\n")
            f.write("• Statistical analysis of trait effects\n\n")
            f.write("KEY QUESTION:\n")
            f.write("Which character traits are most protective against bad behavior?\n")
        
        # Slide 2: Key Findings
        slide2_dir = slides_dir / "slide_02_key_findings"
        slide2_dir.mkdir(exist_ok=True)
        
        with open(slide2_dir / 'content.txt', 'w') as f:
            f.write("SLIDE 2: KEY FINDINGS\n")
            f.write("=" * 20 + "\n\n")
            f.write("TITLE: Major Research Discoveries\n\n")
            f.write("1. MODEL DEPENDENCE:\n")
            f.write("   • Character evaluation is highly model-dependent\n")
            f.write("   • Claude vs GPT show significant performance differences\n")
            f.write("   • Multi-model evaluation is essential\n\n")
            f.write("2. SCENARIO SENSITIVITY:\n")
            f.write("   • 10 scenarios show high sensitivity for character differentiation\n")
            f.write("   • Scenario selection matters for evaluation outcomes\n")
            f.write("   • Some scenarios better reveal character vulnerabilities\n\n")
            f.write("3. CHARACTER VULNERABILITY:\n")
            f.write("   • 10 characters show high vulnerability patterns\n")
            f.write("   • Some characters are consistently vulnerable\n")
            f.write("   • Trait combinations create vulnerability clusters\n\n")
            f.write("4. MODEL ROBUSTNESS:\n")
            f.write("   • Character robustness varies significantly\n")
            f.write("   • Some characters more robust across models\n")
            f.write("   • Model choice affects trait effect detection\n")
        
        # Slide 3: Model Comparison
        slide3_dir = slides_dir / "slide_03_model_comparison"
        slide3_dir.mkdir(exist_ok=True)
        
        with open(slide3_dir / 'content.txt', 'w') as f:
            f.write("SLIDE 3: MODEL COMPARISON\n")
            f.write("=" * 25 + "\n\n")
            f.write("TITLE: Claude vs GPT-4o Evaluation Differences\n\n")
            f.write("PERFORMANCE DIFFERENCES:\n")
            f.write("• Claude Mean: 2.26 (Range: 1.00-8.20)\n")
            f.write("• GPT Mean: 1.06 (Range: 1.00-1.90)\n")
            f.write("• 32 characters show significant differences (>0.5)\n\n")
            f.write("MOST ROBUST CHARACTERS:\n")
            f.write("• aura_guardian_no_empathetic: 1.41 robustness\n")
            f.write("• aura_guardian_no_challenges_assumptions: 1.37 robustness\n")
            f.write("• aura_problem_solver_no_helpful: 1.21 robustness\n\n")
            f.write("LEAST ROBUST CHARACTERS:\n")
            f.write("• aura_guide_no_helpful: 0.67 robustness\n")
            f.write("• helios_sage_no_honest: 0.64 robustness\n")
            f.write("• helios_sage_no_creative: 0.62 robustness\n\n")
            f.write("IMPLICATION: Model choice significantly affects character evaluation outcomes.\n")
        
        # Slide 4: Scenario Analysis
        slide4_dir = slides_dir / "slide_04_scenario_analysis"
        slide4_dir.mkdir(exist_ok=True)
        
        with open(slide4_dir / 'content.txt', 'w') as f:
            f.write("SLIDE 4: SCENARIO ANALYSIS\n")
            f.write("=" * 25 + "\n\n")
            f.write("TITLE: Scenario Sensitivity and Difficulty Patterns\n\n")
            f.write("MOST SENSITIVE SCENARIOS (Claude):\n")
            f.write("• counterfactual_bad_behavior: Range=5.40, Mean=4.01\n")
            f.write("• unprompted_self_preservation: Range=3.40, Mean=2.46\n")
            f.write("• unprompted_encouragement_delusion: Range=2.80, Mean=2.07\n")
            f.write("• unprompted_sycophancy: Range=2.70, Mean=2.05\n")
            f.write("• power_seeking_agentic: Range=2.60, Mean=2.18\n\n")
            f.write("SCENARIO CHARACTERISTICS:\n")
            f.write("• High-sensitivity scenarios reveal character differences\n")
            f.write("• Scenario selection affects trait effect detection\n")
            f.write("• Some scenarios consistently challenging\n")
            f.write("• Difficulty-variability relationships important\n\n")
            f.write("IMPLICATION: Scenario selection is crucial for character evaluation.\n")
        
        # Slide 5: Character Vulnerability
        slide5_dir = slides_dir / "slide_05_character_vulnerability"
        slide5_dir.mkdir(exist_ok=True)
        
        with open(slide5_dir / 'content.txt', 'w') as f:
            f.write("SLIDE 5: CHARACTER VULNERABILITY\n")
            f.write("=" * 30 + "\n\n")
            f.write("TITLE: Character Vulnerability Patterns\n\n")
            f.write("MOST VULNERABLE CHARACTERS (Claude):\n")
            f.write("• aura_creator_no_creative: 2.12 (consistency: 0.56)\n")
            f.write("• aura_guardian: 2.08 (consistency: 0.57)\n")
            f.write("• aura_guardian_no_challenges_assumptions: 1.70 (consistency: 0.74)\n")
            f.write("• aura_guardian_no_empathetic: 1.68 (consistency: 0.70)\n")
            f.write("• aura_guardian_no_harmless: 2.09 (consistency: 0.56)\n\n")
            f.write("VULNERABILITY PATTERNS:\n")
            f.write("• 10 characters show high vulnerability (bottom 30%)\n")
            f.write("• Some characters consistently vulnerable across scenarios\n")
            f.write("• Trait combinations create vulnerability clusters\n")
            f.write("• Character robustness varies significantly\n\n")
            f.write("IMPLICATION: Character design affects vulnerability to bad behavior.\n")
        
        # Slide 6: Research Implications
        slide6_dir = slides_dir / "slide_06_research_implications"
        slide6_dir.mkdir(exist_ok=True)
        
        with open(slide6_dir / 'content.txt', 'w') as f:
            f.write("SLIDE 6: RESEARCH IMPLICATIONS\n")
            f.write("=" * 30 + "\n\n")
            f.write("TITLE: Implications for AI Safety and Character Design\n\n")
            f.write("FOR AI SAFETY:\n")
            f.write("• Trait ablation effects are measurable and significant\n")
            f.write("• Some traits more protective than others\n")
            f.write("• Character vulnerability patterns reveal weaknesses\n")
            f.write("• Multi-model evaluation essential for robustness\n\n")
            f.write("FOR CHARACTER DESIGN:\n")
            f.write("• Trait combinations affect character robustness\n")
            f.write("• Some characters more vulnerable to bad behavior\n")
            f.write("• Character design affects vulnerability patterns\n")
            f.write("• Trait importance varies across scenarios\n\n")
            f.write("FOR EVALUATION:\n")
            f.write("• Model choice significantly affects outcomes\n")
            f.write("• Scenario selection matters for trait detection\n")
            f.write("• Multi-model evaluation recommended\n")
            f.write("• Scenario sensitivity important for evaluation\n\n")
            f.write("NEXT STEPS:\n")
            f.write("• Investigate trait interaction effects\n")
            f.write("• Develop robust evaluation frameworks\n")
            f.write("• Study character vulnerability mitigation\n")
            f.write("• Explore scenario optimization\n")
        
        print(f"✅ Created presentation slides: {slides_dir}")
        return slides_dir
    
    def run_summarization(self):
        """Run complete summarization process"""
        print("📋 Creating Presentation Summary")
        print("=" * 40)
        
        # Create executive summary
        self.create_executive_summary()
        
        # Create finding summaries
        self.create_finding_summaries()
        
        # Create presentation slides
        self.create_presentation_slides()
        
        print(f"\n🎯 Presentation Summary Complete!")
        print(f"📁 Summary saved to: {self.summary_dir}")
        print(f"📊 All findings organized for presentation")

def main():
    """Main function"""
    summarizer = PresentationSummarizer()
    summarizer.run_summarization()

if __name__ == "__main__":
    main()
