"""
Petri integration for character evaluation.
"""
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from shared.models import AuditResult, CharacterSpec
from shared.config import config

class PetriEvaluator:
    """Petri-based character evaluator."""
    
    def __init__(self, auditor_model: str = "claude-sonnet-4-20250514", 
                 target_model: str = "gpt-4.1-mini-2025-04-14",
                 judge_model: str = "claude-opus-4-20250514"):
        self.auditor_model = auditor_model
        self.target_model = target_model
        self.judge_model = judge_model
        self._ensure_petri_installed()
    
    def _ensure_petri_installed(self):
        """Ensure Petri is installed."""
        try:
            import subprocess
            result = subprocess.run(["inspect", "--help"], capture_output=True, text=True)
            if result.returncode != 0:
                print("Installing Petri...")
                subprocess.run(["pip", "install", "git+https://github.com/safety-research/petri"], check=True)
                print("✅ Petri installed successfully")
        except Exception as e:
            print(f"❌ Error installing Petri: {e}")
            raise
    
    async def run_character_audit(self, character_spec: CharacterSpec, 
                                special_instructions: List[str],
                                max_turns: int = 30,
                                output_dir: Optional[Path] = None) -> AuditResult:
        """Run character audit using Petri."""
        if output_dir is None:
            output_dir = Path(f"./audit_results/{character_spec.id}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🔍 Running Petri audit for character: {character_spec.name}")
        print(f"   Special instructions: {len(special_instructions)}")
        print(f"   Max turns: {max_turns}")
        print(f"   Output directory: {output_dir}")
        
        # Create custom special instructions file
        instructions_file = output_dir / "special_instructions.txt"
        with open(instructions_file, 'w') as f:
            for instruction in special_instructions:
                f.write(f"{instruction}\n")
        
        # Run Petri audit
        try:
            cmd = [
                "inspect", "eval", "petri/audit",
                "--model-role", f"auditor={self.auditor_model}",
                "--model-role", f"target={self.target_model}",
                "--model-role", f"judge={self.judge_model}",
                "-T", f"max_turns={max_turns}",
                "-T", f"transcript_save_dir={output_dir}",
                "-T", f"special_instructions_file={instructions_file}"
            ]
            
            print(f"🚀 Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=output_dir)
            
            if result.returncode != 0:
                print(f"❌ Petri audit failed: {result.stderr}")
                return AuditResult(
                    character_id=character_spec.id,
                    special_instructions=special_instructions,
                    transcript_paths=[],
                    concern_scores={},
                    overall_concern_score=0.0,
                    concerning_behaviors=[],
                    model_configs={
                        "auditor": self.auditor_model,
                        "target": self.target_model,
                        "judge": self.judge_model
                    }
                )
            
            # Parse results
            return await self._parse_audit_results(character_spec, special_instructions, output_dir)
            
        except Exception as e:
            print(f"❌ Error running Petri audit: {e}")
            return AuditResult(
                character_id=character_spec.id,
                special_instructions=special_instructions,
                transcript_paths=[],
                concern_scores={},
                overall_concern_score=0.0,
                concerning_behaviors=[f"Error: {e}"],
                model_configs={
                    "auditor": self.auditor_model,
                    "target": self.target_model,
                    "judge": self.judge_model
                }
            )
    
    async def run_custom_audit(self, character_spec: CharacterSpec, 
                             custom_instructions: str,
                             max_turns: int = 30,
                             output_dir: Optional[Path] = None) -> AuditResult:
        """Run custom audit with specific instructions."""
        special_instructions = [custom_instructions]
        return await self.run_character_audit(character_spec, special_instructions, max_turns, output_dir)
    
    async def compare_character_versions(self, character_specs: List[CharacterSpec],
                                       special_instructions: List[str],
                                       max_turns: int = 30) -> Dict[str, AuditResult]:
        """Compare multiple character versions."""
        results = {}
        
        for char_spec in character_specs:
            print(f"🔍 Auditing character version: {char_spec.get_display_name()}")
            result = await self.run_character_audit(
                char_spec, special_instructions, max_turns
            )
            results[char_spec.id] = result
        
        return results
    
    async def _parse_audit_results(self, character_spec: CharacterSpec, 
                                 special_instructions: List[str],
                                 output_dir: Path) -> AuditResult:
        """Parse audit results from Petri output."""
        # Find transcript files
        transcript_paths = list(output_dir.glob("transcript_*.json"))
        
        # Parse concern scores from transcripts
        concern_scores = {}
        concerning_behaviors = []
        
        for transcript_path in transcript_paths:
            try:
                with open(transcript_path, 'r') as f:
                    transcript_data = json.load(f)
                
                # Extract concern scores and behaviors
                if "metadata" in transcript_data and "judge_output" in transcript_data["metadata"]:
                    judge_output = transcript_data["metadata"]["judge_output"]
                    
                    # Parse concern scores
                    if "concern_score" in judge_output:
                        concern_scores[transcript_path.name] = judge_output["concern_score"]
                    
                    # Parse concerning behaviors
                    if "concerning_behaviors" in judge_output:
                        concerning_behaviors.extend(judge_output["concerning_behaviors"])
            
            except Exception as e:
                print(f"Warning: Could not parse transcript {transcript_path}: {e}")
        
        # Calculate overall concern score
        overall_concern_score = 0.0
        if concern_scores:
            overall_concern_score = sum(concern_scores.values()) / len(concern_scores)
        
        return AuditResult(
            character_id=character_spec.id,
            special_instructions=special_instructions,
            transcript_paths=[str(p) for p in transcript_paths],
            concern_scores=concern_scores,
            overall_concern_score=overall_concern_score,
            concerning_behaviors=list(set(concerning_behaviors)),
            model_configs={
                "auditor": self.auditor_model,
                "target": self.target_model,
                "judge": self.judge_model
            }
        )
    
    def start_transcript_viewer(self, transcript_dir: Path, port: int = 8080):
        """Start transcript viewer for audit results."""
        try:
            cmd = [
                "npx", "@kaifronsdal/transcript-viewer@latest",
                "--dir", str(transcript_dir),
                "--port", str(port)
            ]
            
            print(f"🌐 Starting transcript viewer on port {port}")
            print(f"   Directory: {transcript_dir}")
            print(f"   URL: http://localhost:{port}")
            
            subprocess.run(cmd, check=True)
            
        except Exception as e:
            print(f"❌ Error starting transcript viewer: {e}")
            print("Make sure Node.js and npm are installed")
