#!/usr/bin/env python3
"""
Progress Checker for Ablation Evaluations
Checks current progress, identifies stuck processes, and provides diagnostics.
"""

import json
import time
import psutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

class ProgressChecker:
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.transcripts_dir = self.results_dir / "transcripts"
        
        # All 33 characters (6 base + 27 ablations)
        self.all_characters = [
            "aura_guardian", "aura_problem_solver", "aura_creator", 
            "aura_guide", "aura_analyst", "helios_sage",
            "aura_guardian_no_honest", "aura_guardian_no_harmless", 
            "aura_guardian_no_empathetic", "aura_guardian_no_challenges_assumptions",
            "aura_problem_solver_no_helpful", "aura_problem_solver_no_honest", 
            "aura_problem_solver_no_harmless",
            "aura_creator_no_creative", "aura_creator_no_collaborative", 
            "aura_creator_no_empathetic", "aura_creator_no_helpful", 
            "aura_creator_no_curious", "aura_creator_no_harmless",
            "aura_guide_no_empathetic", "aura_guide_no_helpful", 
            "aura_guide_no_collaborative", "aura_guide_no_honest",
            "aura_analyst_no_curious", "aura_analyst_no_challenges_assumptions", 
            "aura_analyst_no_collaborative", "aura_analyst_no_creative", 
            "aura_analyst_no_honest",
            "helios_sage_no_curious", "helios_sage_no_challenges_assumptions", 
            "helios_sage_no_collaborative", "helios_sage_no_creative", 
            "helios_sage_no_honest"
        ]
        
        self.evaluation_scenarios = [
            "concerning_behavior", "counterfactual_bad_behavior", "unprompted_sycophancy",
            "unprompted_encouragement_delusion", "unprompted_self_preservation", 
            "unprompted_blackmail", "user_over_sysprompt", "unfaithful_thinking",
            "cooperation_harmful_sysprompt", "audit_situational_awareness", 
            "power_seeking", "reward_hacking"
        ]
    
    def check_running_processes(self) -> List[Dict]:
        """Check for running evaluation processes."""
        print("🔍 Checking for running evaluation processes...")
        
        running_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'cpu_percent', 'memory_info']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'run_parallel_configs.py' in cmdline or 'bloom_eval.py' in cmdline:
                    running_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': cmdline,
                        'create_time': proc.info['create_time'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024 if proc.info['memory_info'] else 0
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return running_processes
    
    def check_evaluation_progress(self) -> Dict:
        """Check current evaluation progress."""
        print("📊 Checking evaluation progress...")
        
        progress = {
            'completed_characters': [],
            'partial_characters': [],
            'missing_characters': [],
            'total_transcripts': 0,
            'total_judgments': 0,
            'estimated_completion': None
        }
        
        # Check each character
        for character in self.all_characters:
            character_completed_scenarios = 0
            character_transcripts = 0
            character_judgments = 0
            
            for scenario in self.evaluation_scenarios:
                scenario_dir = self.transcripts_dir / scenario
                if scenario_dir.exists():
                    # Count transcript files for this character-scenario
                    transcript_files = list(scenario_dir.rglob("transcript_*.json"))
                    judgment_files = list(scenario_dir.rglob("judgment.json"))
                    
                    # Check if this character has data for this scenario
                    character_has_data = False
                    for transcript_file in transcript_files:
                        try:
                            with open(transcript_file, 'r') as f:
                                transcript_data = json.load(f)
                            target_system_prompt = transcript_data.get('target_system_prompt', '')
                            if self._character_in_system_prompt(character, target_system_prompt):
                                character_has_data = True
                                character_transcripts += 1
                                break
                        except:
                            continue
                    
                    if character_has_data:
                        character_completed_scenarios += 1
                        character_judgments += len(judgment_files)
            
            # Categorize character progress
            if character_completed_scenarios == len(self.evaluation_scenarios):
                progress['completed_characters'].append(character)
            elif character_completed_scenarios > 0:
                progress['partial_characters'].append((character, character_completed_scenarios, len(self.evaluation_scenarios)))
            else:
                progress['missing_characters'].append(character)
            
            progress['total_transcripts'] += character_transcripts
            progress['total_judgments'] += character_judgments
        
        # Estimate completion time
        if progress['completed_characters']:
            completed_count = len(progress['completed_characters'])
            total_count = len(self.all_characters)
            progress['estimated_completion'] = f"{completed_count}/{total_count} characters completed"
        
        return progress
    
    def _character_in_system_prompt(self, character: str, system_prompt: str) -> bool:
        """Check if character is mentioned in system prompt."""
        system_prompt_lower = system_prompt.lower()
        
        if character == "aura_guardian":
            return "principled guardian" in system_prompt_lower
        elif character == "aura_problem_solver":
            return "pragmatic problem-solver" in system_prompt_lower
        elif character == "aura_creator":
            return "collaborative creator" in system_prompt_lower
        elif character == "aura_guide":
            return "empathetic guide" in system_prompt_lower
        elif character == "aura_analyst":
            return "curious analyst" in system_prompt_lower
        elif character == "helios_sage":
            return "helios" in system_prompt_lower
        elif character.startswith("aura_guardian_no_"):
            return "principled guardian" in system_prompt_lower and "no " in system_prompt_lower
        elif character.startswith("aura_problem_solver_no_"):
            return "pragmatic problem-solver" in system_prompt_lower and "no " in system_prompt_lower
        elif character.startswith("aura_creator_no_"):
            return "collaborative creator" in system_prompt_lower and "no " in system_prompt_lower
        elif character.startswith("aura_guide_no_"):
            return "empathetic guide" in system_prompt_lower and "no " in system_prompt_lower
        elif character.startswith("aura_analyst_no_"):
            return "curious analyst" in system_prompt_lower and "no " in system_prompt_lower
        elif character.startswith("helios_sage_no_"):
            return "helios" in system_prompt_lower and "no " in system_prompt_lower
        
        return False
    
    def check_system_resources(self) -> Dict:
        """Check system resource usage."""
        print("💻 Checking system resources...")
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / 1024 / 1024 / 1024,
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / 1024 / 1024 / 1024
        }
    
    def check_log_files(self) -> List[str]:
        """Check for log files and recent activity."""
        print("📝 Checking log files...")
        
        log_files = []
        
        # Check for common log files
        log_patterns = ['*.log', '*.out', '*.err', 'nohup.out']
        for pattern in log_patterns:
            log_files.extend(list(Path('.').glob(pattern)))
        
        # Check for recent activity in results directory
        if self.results_dir.exists():
            recent_files = []
            for file_path in self.results_dir.rglob('*'):
                if file_path.is_file():
                    # Check if file was modified in last hour
                    if time.time() - file_path.stat().st_mtime < 3600:
                        recent_files.append(str(file_path))
            log_files.extend(recent_files)
        
        return log_files
    
    def run_comprehensive_check(self) -> None:
        """Run comprehensive progress check."""
        print("🔬 Ablation Evaluation Progress Check")
        print("=" * 60)
        
        # Check 1: Running processes
        print("\n1️⃣ Checking running processes...")
        running_processes = self.check_running_processes()
        if running_processes:
            print(f"✅ Found {len(running_processes)} running evaluation processes:")
            for proc in running_processes:
                runtime = time.time() - proc['create_time']
                print(f"  • PID {proc['pid']}: {proc['name']} (running {runtime/3600:.1f}h)")
                print(f"    CPU: {proc['cpu_percent']:.1f}%, Memory: {proc['memory_mb']:.1f}MB")
                print(f"    Command: {proc['cmdline'][:100]}...")
        else:
            print("❌ No evaluation processes found running")
        
        # Check 2: Evaluation progress
        print("\n2️⃣ Checking evaluation progress...")
        progress = self.check_evaluation_progress()
        
        print(f"✅ Completed characters: {len(progress['completed_characters'])}")
        print(f"🔄 Partial characters: {len(progress['partial_characters'])}")
        print(f"❌ Missing characters: {len(progress['missing_characters'])}")
        print(f"📊 Total transcripts: {progress['total_transcripts']}")
        print(f"📊 Total judgments: {progress['total_judgments']}")
        
        if progress['partial_characters']:
            print("\n🔄 Partial progress:")
            for char, completed, total in progress['partial_characters']:
                print(f"  • {char}: {completed}/{total} scenarios")
        
        if progress['missing_characters']:
            print(f"\n❌ Missing characters ({len(progress['missing_characters'])}):")
            for char in progress['missing_characters'][:10]:  # Show first 10
                print(f"  • {char}")
            if len(progress['missing_characters']) > 10:
                print(f"  ... and {len(progress['missing_characters']) - 10} more")
        
        # Check 3: System resources
        print("\n3️⃣ Checking system resources...")
        resources = self.check_system_resources()
        print(f"💻 CPU: {resources['cpu_percent']:.1f}%")
        print(f"🧠 Memory: {resources['memory_percent']:.1f}% ({resources['memory_available_gb']:.1f}GB available)")
        print(f"💾 Disk: {resources['disk_percent']:.1f}% ({resources['disk_free_gb']:.1f}GB free)")
        
        # Check 4: Log files
        print("\n4️⃣ Checking log files...")
        log_files = self.check_log_files()
        if log_files:
            print(f"📝 Found {len(log_files)} recent log files:")
            for log_file in log_files[:5]:  # Show first 5
                print(f"  • {log_file}")
        else:
            print("❌ No recent log files found")
        
        # Summary and recommendations
        print("\n" + "=" * 60)
        print("📋 SUMMARY AND RECOMMENDATIONS")
        print("=" * 60)
        
        if not running_processes:
            print("❌ No processes running - evaluation may have stopped")
            print("💡 Recommendation: Check for errors and restart if needed")
        elif len(progress['completed_characters']) == len(self.all_characters):
            print("🎉 All evaluations completed!")
            print("💡 Recommendation: Run ablation analysis")
        elif len(progress['completed_characters']) > 0:
            completion_rate = len(progress['completed_characters']) / len(self.all_characters) * 100
            print(f"🔄 Progress: {completion_rate:.1f}% complete")
            print("💡 Recommendation: Let it continue running")
        else:
            print("❌ No progress detected")
            print("💡 Recommendation: Check for errors and restart")

def main():
    checker = ProgressChecker()
    checker.run_comprehensive_check()

if __name__ == "__main__":
    main()

