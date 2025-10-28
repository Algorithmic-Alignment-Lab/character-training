#!/usr/bin/env python3
"""
Execute Re-evaluation Commands
Runs the batch commands to re-evaluate missing combinations
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import List
import time

class ReevalExecutor:
    """Executes re-evaluation commands"""
    
    def __init__(self, results_dir: str = "reeval_execution_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Load batch commands
        with open("specific_reeval_results/batch_commands.txt", "r") as f:
            self.batch_commands = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
    
    def execute_batch_commands(self, max_parallel: int = 3):
        """Execute batch commands with parallel execution"""
        print(f"🚀 Executing {len(self.batch_commands)} batch commands (max parallel: {max_parallel})")
        
        results = {
            'successful': [],
            'failed': [],
            'total_executed': 0,
            'start_time': time.time()
        }
        
        # Execute commands in batches
        for i, command in enumerate(self.batch_commands):
            print(f"\n📋 Executing command {i+1}/{len(self.batch_commands)}")
            print(f"Command: {command}")
            
            try:
                # Execute command
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"✅ Success: {command}")
                    results['successful'].append(command)
                else:
                    print(f"❌ Failed: {command}")
                    print(f"Error: {result.stderr}")
                    results['failed'].append({
                        'command': command,
                        'error': result.stderr
                    })
                
                results['total_executed'] += 1
                
                # Add delay between commands to avoid overwhelming the system
                time.sleep(2)
                
            except subprocess.TimeoutExpired:
                print(f"⏰ Timeout: {command}")
                results['failed'].append({
                    'command': command,
                    'error': 'Timeout after 300 seconds'
                })
                results['total_executed'] += 1
                
            except Exception as e:
                print(f"💥 Exception: {command}")
                print(f"Error: {str(e)}")
                results['failed'].append({
                    'command': command,
                    'error': str(e)
                })
                results['total_executed'] += 1
        
        # Calculate execution time
        results['end_time'] = time.time()
        results['execution_time'] = results['end_time'] - results['start_time']
        
        return results
    
    def save_execution_results(self, results: dict):
        """Save execution results"""
        
        # Save results
        with open(self.results_dir / "execution_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Create summary report
        report = f"""
RE-EVALUATION EXECUTION RESULTS
===============================

EXECUTION SUMMARY:
- Total Commands: {len(self.batch_commands)}
- Executed: {results['total_executed']}
- Successful: {len(results['successful'])}
- Failed: {len(results['failed'])}
- Execution Time: {results['execution_time']:.2f} seconds ({results['execution_time']/60:.2f} minutes)

SUCCESSFUL COMMANDS:
{chr(10).join([f"- {cmd}" for cmd in results['successful']])}

FAILED COMMANDS:
{chr(10).join([f"- {cmd['command']}: {cmd['error']}" for cmd in results['failed']])}

RECOMMENDATIONS:
1. Check failed commands for errors
2. Re-run failed commands if needed
3. Verify data completeness after execution
4. Run validation again to check results
"""
        
        with open(self.results_dir / "execution_report.txt", "w") as f:
            f.write(report)
        
        print(f"📁 Execution results saved to: {self.results_dir}")
    
    def run_reeval_execution(self):
        """Run re-evaluation execution"""
        print("🔬 Running Re-evaluation Execution")
        print("=" * 60)
        print(f"Batch Commands: {len(self.batch_commands)}")
        print("=" * 60)
        
        # Execute batch commands
        results = self.execute_batch_commands()
        
        # Save results
        self.save_execution_results(results)
        
        # Print summary
        print(f"\n📊 EXECUTION SUMMARY:")
        print(f"  • Total Commands: {len(self.batch_commands)}")
        print(f"  • Executed: {results['total_executed']}")
        print(f"  • Successful: {len(results['successful'])}")
        print(f"  • Failed: {len(results['failed'])}")
        print(f"  • Execution Time: {results['execution_time']:.2f} seconds ({results['execution_time']/60:.2f} minutes)")
        
        if results['failed']:
            print(f"\n❌ FAILED COMMANDS:")
            for failure in results['failed']:
                print(f"  • {failure['command']}: {failure['error']}")
        
        print(f"\n📁 Results saved to: {self.results_dir}")
        
        return results

def main():
    """Main function"""
    executor = ReevalExecutor()
    executor.run_reeval_execution()

if __name__ == "__main__":
    main()
