#!/usr/bin/env python3

import asyncio
import json
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

# Import safety-tooling components
import sys
sys.path.append(str(Path(__file__).parent.parent / "safety-tooling"))

from safetytooling.apis.finetuning.openai.run import OpenAIFTConfig, main as openai_main
from safetytooling.apis.finetuning.together.run import TogetherFTConfig, main as together_main
from safetytooling.apis.inference.openai.utils import OAI_FINETUNE_MODELS
from safetytooling.apis.inference.together import TOGETHER_MODELS
from safetytooling.utils import utils

class FinetuningStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class FinetuningProvider(Enum):
    OPENAI = "openai"
    TOGETHER = "together"

@dataclass
class FinetuningJob:
    """Data class for fine-tuning job tracking."""
    id: str
    name: str
    provider: str
    model: str
    train_file: str
    val_file: Optional[str]
    config: Dict[str, Any]
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    fine_tuned_model: Optional[str] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    logs: Optional[List[str]] = None

class FinetuningManager:
    """Manage fine-tuning jobs and integration with conversations_ui."""
    
    def __init__(self, db_path: str = "fine_tuning_jobs.db"):
        self.db_path = db_path
        self.init_db()
        
    def init_db(self):
        """Initialize fine-tuning jobs database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fine_tuning_jobs (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    train_file TEXT NOT NULL,
                    val_file TEXT,
                    config_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    fine_tuned_model TEXT,
                    error_message TEXT,
                    metrics_json TEXT,
                    logs_json TEXT
                )
            """)
            conn.commit()
    
    def save_job(self, job: FinetuningJob):
        """Save fine-tuning job to database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO fine_tuning_jobs 
                (id, name, provider, model, train_file, val_file, config_json, status, 
                 created_at, started_at, completed_at, fine_tuned_model, error_message, 
                 metrics_json, logs_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.id, job.name, job.provider, job.model, job.train_file, job.val_file,
                json.dumps(job.config), job.status, job.created_at, job.started_at,
                job.completed_at, job.fine_tuned_model, job.error_message,
                json.dumps(job.metrics) if job.metrics else None,
                json.dumps(job.logs) if job.logs else None
            ))
            conn.commit()
    
    def get_job(self, job_id: str) -> Optional[FinetuningJob]:
        """Get fine-tuning job by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM fine_tuning_jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            
            if row:
                return FinetuningJob(
                    id=row['id'],
                    name=row['name'],
                    provider=row['provider'],
                    model=row['model'],
                    train_file=row['train_file'],
                    val_file=row['val_file'],
                    config=json.loads(row['config_json']),
                    status=row['status'],
                    created_at=row['created_at'],
                    started_at=row['started_at'],
                    completed_at=row['completed_at'],
                    fine_tuned_model=row['fine_tuned_model'],
                    error_message=row['error_message'],
                    metrics=json.loads(row['metrics_json']) if row['metrics_json'] else None,
                    logs=json.loads(row['logs_json']) if row['logs_json'] else None
                )
        return None
    
    def list_jobs(self, status: Optional[str] = None, provider: Optional[str] = None) -> List[FinetuningJob]:
        """List fine-tuning jobs with optional filtering."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM fine_tuning_jobs"
            params = []
            conditions = []
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            if provider:
                conditions.append("provider = ?")
                params.append(provider)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            jobs = []
            for row in rows:
                jobs.append(FinetuningJob(
                    id=row['id'],
                    name=row['name'],
                    provider=row['provider'],
                    model=row['model'],
                    train_file=row['train_file'],
                    val_file=row['val_file'],
                    config=json.loads(row['config_json']),
                    status=row['status'],
                    created_at=row['created_at'],
                    started_at=row['started_at'],
                    completed_at=row['completed_at'],
                    fine_tuned_model=row['fine_tuned_model'],
                    error_message=row['error_message'],
                    metrics=json.loads(row['metrics_json']) if row['metrics_json'] else None,
                    logs=json.loads(row['logs_json']) if row['logs_json'] else None
                ))
            
            return jobs
    
    def create_openai_job(self, 
                         name: str,
                         model: str,
                         train_file: str,
                         val_file: Optional[str] = None,
                         n_epochs: int = 1,
                         batch_size: Union[int, str] = "auto",
                         learning_rate_multiplier: Union[float, str] = "auto",
                         method: str = "supervised",
                         wandb_project_name: Optional[str] = None,
                         tags: tuple = ("conversations_ui",),
                         save_folder: Optional[str] = None) -> FinetuningJob:
        """Create OpenAI fine-tuning job."""
        
        job_id = str(uuid.uuid4())
        
        config = {
            "model": model,
            "train_file": train_file,
            "val_file": val_file,
            "n_epochs": n_epochs,
            "batch_size": batch_size,
            "learning_rate_multiplier": learning_rate_multiplier,
            "method": method,
            "wandb_project_name": wandb_project_name,
            "tags": tags,
            "save_folder": save_folder,
            "save_config": True,
            "logging_level": "info",
            "dry_run": False,
            "openai_tag": "OPENAI_API_KEY"
        }
        
        job = FinetuningJob(
            id=job_id,
            name=name,
            provider=FinetuningProvider.OPENAI.value,
            model=model,
            train_file=train_file,
            val_file=val_file,
            config=config,
            status=FinetuningStatus.PENDING.value,
            created_at=datetime.now().isoformat()
        )
        
        self.save_job(job)
        return job
    
    def create_together_job(self,
                          name: str,
                          model: str,
                          train_file: str,
                          val_file: Optional[str] = None,
                          n_epochs: int = 1,
                          batch_size: int = 8,
                          learning_rate: float = 1e-5,
                          lora: bool = True,
                          lora_r: int = 64,
                          lora_alpha: Optional[int] = None,
                          wandb_project_name: Optional[str] = None,
                          tags: tuple = ("conversations_ui",),
                          save_folder: Optional[str] = None,
                          suffix: str = "") -> FinetuningJob:
        """Create Together AI fine-tuning job."""
        
        job_id = str(uuid.uuid4())
        
        if lora_alpha is None:
            lora_alpha = lora_r * 2
        
        config = {
            "model": model,
            "train_file": train_file,
            "val_file": val_file,
            "n_epochs": n_epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "lora": lora,
            "lora_r": lora_r,
            "lora_alpha": lora_alpha,
            "lora_trainable_modules": "all-linear",
            "wandb_project_name": wandb_project_name,
            "tags": tags,
            "save_folder": save_folder,
            "save_config": True,
            "logging_level": "info",
            "dry_run": False,
            "suffix": suffix or f"conv_{job_id[:8]}",
            "save_model": True
        }
        
        job = FinetuningJob(
            id=job_id,
            name=name,
            provider=FinetuningProvider.TOGETHER.value,
            model=model,
            train_file=train_file,
            val_file=val_file,
            config=config,
            status=FinetuningStatus.PENDING.value,
            created_at=datetime.now().isoformat()
        )
        
        self.save_job(job)
        return job
    
    async def run_job(self, job_id: str) -> FinetuningJob:
        """Run a fine-tuning job."""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        if job.status != FinetuningStatus.PENDING.value:
            raise ValueError(f"Job {job_id} is not in pending status")
        
        # Update job status
        job.status = FinetuningStatus.RUNNING.value
        job.started_at = datetime.now().isoformat()
        self.save_job(job)
        
        try:
            # Set up environment
            utils.setup_environment()
            
            if job.provider == FinetuningProvider.OPENAI.value:
                await self._run_openai_job(job)
            elif job.provider == FinetuningProvider.TOGETHER.value:
                await self._run_together_job(job)
            else:
                raise ValueError(f"Unsupported provider: {job.provider}")
            
            job.status = FinetuningStatus.COMPLETED.value
            job.completed_at = datetime.now().isoformat()
            
        except Exception as e:
            job.status = FinetuningStatus.FAILED.value
            job.error_message = str(e)
            job.completed_at = datetime.now().isoformat()
            
        self.save_job(job)
        return job
    
    async def _run_openai_job(self, job: FinetuningJob):
        """Run OpenAI fine-tuning job."""
        config = OpenAIFTConfig(
            model=job.config["model"],
            train_file=Path(job.config["train_file"]),
            val_file=Path(job.config["val_file"]) if job.config.get("val_file") else None,
            n_epochs=job.config["n_epochs"],
            batch_size=job.config["batch_size"],
            wandb_project_name=job.config.get("wandb_project_name"),
            tags=job.config.get("tags", ()),
            save_folder=job.config.get("save_folder"),
            save_config=job.config.get("save_config", True),
            logging_level=job.config.get("logging_level", "info"),
            dry_run=job.config.get("dry_run", False),
            openai_tag=job.config.get("openai_tag", "OPENAI_API_KEY"),
            learning_rate_multiplier=job.config.get("learning_rate_multiplier", "auto"),
            method=job.config.get("method", "supervised"),
            beta=job.config.get("beta", "auto")
        )
        
        ft_job, run = await openai_main(config)
        
        # Update job with results
        job.fine_tuned_model = ft_job.fine_tuned_model
        if run:
            job.metrics = {
                "training_loss": getattr(run, 'training_loss', None),
                "validation_loss": getattr(run, 'validation_loss', None),
                "final_loss": getattr(run, 'final_loss', None)
            }
    
    async def _run_together_job(self, job: FinetuningJob):
        """Run Together AI fine-tuning job."""
        config = TogetherFTConfig(
            model=job.config["model"],
            train_file=Path(job.config["train_file"]),
            val_file=Path(job.config["val_file"]) if job.config.get("val_file") else None,
            n_epochs=job.config["n_epochs"],
            batch_size=job.config["batch_size"],
            learning_rate=job.config["learning_rate"],
            lora=job.config.get("lora", True),
            lora_r=job.config.get("lora_r", 64),
            lora_alpha=job.config.get("lora_alpha", 128),
            lora_trainable_modules=job.config.get("lora_trainable_modules", "all-linear"),
            wandb_project_name=job.config.get("wandb_project_name"),
            tags=job.config.get("tags", ()),
            save_folder=job.config.get("save_folder"),
            save_config=job.config.get("save_config", True),
            logging_level=job.config.get("logging_level", "info"),
            dry_run=job.config.get("dry_run", False),
            suffix=job.config.get("suffix", ""),
            save_model=job.config.get("save_model", True)
        )
        
        ft_job = await together_main(config)
        
        # Update job with results
        job.fine_tuned_model = ft_job.output_name
        job.metrics = {
            "job_id": ft_job.id,
            "status": ft_job.status,
            "output_name": ft_job.output_name
        }
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models for fine-tuning by provider."""
        return {
            "openai": list(OAI_FINETUNE_MODELS),
            "together": list(TOGETHER_MODELS) + [
                "google/gemma-3-27b-it",
                "Qwen/Qwen3-32B",
                "Qwen/Qwen3-4B",
                "Qwen/Qwen3-8B",
                "Qwen/Qwen3-1.7B",
                "google/gemma-3-1b-it",
                "google/gemma-3-4b-it",
                "Qwen/Qwen2.5-72B-Instruct",
                "Qwen/Qwen2.5-7B-Instruct",
                "Qwen/Qwen2.5-3B-Instruct",
                "Qwen/Qwen2.5-1.5B-Instruct"
            ]
        }
    
    def get_job_stats(self) -> Dict[str, Any]:
        """Get statistics about fine-tuning jobs."""
        jobs = self.list_jobs()
        
        stats = {
            "total_jobs": len(jobs),
            "by_status": {},
            "by_provider": {},
            "by_model": {},
            "completed_jobs": 0,
            "failed_jobs": 0
        }
        
        for job in jobs:
            # Count by status
            stats["by_status"][job.status] = stats["by_status"].get(job.status, 0) + 1
            
            # Count by provider
            stats["by_provider"][job.provider] = stats["by_provider"].get(job.provider, 0) + 1
            
            # Count by model
            stats["by_model"][job.model] = stats["by_model"].get(job.model, 0) + 1
            
            # Count completed and failed
            if job.status == FinetuningStatus.COMPLETED.value:
                stats["completed_jobs"] += 1
            elif job.status == FinetuningStatus.FAILED.value:
                stats["failed_jobs"] += 1
        
        return stats
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running fine-tuning job."""
        job = self.get_job(job_id)
        if not job:
            return False
        
        if job.status == FinetuningStatus.RUNNING.value:
            job.status = FinetuningStatus.CANCELLED.value
            job.completed_at = datetime.now().isoformat()
            self.save_job(job)
            return True
        
        return False
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a fine-tuning job."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM fine_tuning_jobs WHERE id = ?", (job_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def generate_finetuning_data_from_conversations(self, conversation_db_path: str, 
                                                   output_file: str, 
                                                   system_prompt: str = None,
                                                   max_conversations: int = None) -> str:
        """Generate fine-tuning data from conversation database."""
        try:
            with sqlite3.connect(conversation_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get conversations with their messages
                query = """
                    SELECT c.id, c.system_prompt, c.system_prompt_name, 
                           m.role, m.content, m.message_index
                    FROM conversations c
                    JOIN messages m ON c.id = m.conversation_id
                    ORDER BY c.id, m.message_index
                """
                
                if max_conversations:
                    query += f" LIMIT {max_conversations * 10}"  # Rough estimate
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                # Group messages by conversation
                conversations = {}
                for row in rows:
                    conv_id = row['id']
                    if conv_id not in conversations:
                        conversations[conv_id] = {
                            'system_prompt': row['system_prompt'] or system_prompt,
                            'system_prompt_name': row['system_prompt_name'],
                            'messages': []
                        }
                    
                    conversations[conv_id]['messages'].append({
                        'role': row['role'],
                        'content': row['content'],
                        'message_index': row['message_index']
                    })
                
                # Convert to fine-tuning format
                training_data = []
                for conv_id, conv_data in conversations.items():
                    if len(conv_data['messages']) < 2:
                        continue  # Skip conversations without proper dialogue
                    
                    # Sort messages by index
                    messages = sorted(conv_data['messages'], key=lambda x: x['message_index'])
                    
                    # Create training example
                    training_messages = []
                    
                    # Add system prompt if available
                    if conv_data['system_prompt']:
                        training_messages.append({
                            "role": "system",
                            "content": conv_data['system_prompt']
                        })
                    
                    # Add conversation messages
                    for msg in messages:
                        if msg['role'] in ['user', 'assistant']:
                            training_messages.append({
                                "role": msg['role'],
                                "content": msg['content']
                            })
                    
                    if len(training_messages) >= 2:  # At least system/user + assistant
                        training_data.append({
                            "messages": training_messages
                        })
                    
                    if max_conversations and len(training_data) >= max_conversations:
                        break
                
                # Save to JSONL file
                with open(output_file, 'w') as f:
                    for example in training_data:
                        f.write(json.dumps(example) + '\n')
                
                return f"Generated {len(training_data)} training examples from {len(conversations)} conversations"
                
        except Exception as e:
            return f"Error generating fine-tuning data: {e}"


# Async wrapper functions for use in Streamlit
async def create_and_run_finetuning_job(
    manager: FinetuningManager,
    provider: str,
    model: str,
    train_file: str,
    job_name: str,
    **kwargs
) -> FinetuningJob:
    """Create and run a fine-tuning job."""
    
    if provider == "openai":
        job = manager.create_openai_job(
            name=job_name,
            model=model,
            train_file=train_file,
            **kwargs
        )
    elif provider == "together":
        job = manager.create_together_job(
            name=job_name,
            model=model,
            train_file=train_file,
            **kwargs
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    
    # Run the job
    return await manager.run_job(job.id)


def main():
    """Command-line interface for fine-tuning management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fine-tuning job management")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List jobs command
    list_parser = subparsers.add_parser('list', help='List fine-tuning jobs')
    list_parser.add_argument('--status', help='Filter by status')
    list_parser.add_argument('--provider', help='Filter by provider')
    
    # Create job command
    create_parser = subparsers.add_parser('create', help='Create fine-tuning job')
    create_parser.add_argument('--name', required=True, help='Job name')
    create_parser.add_argument('--provider', choices=['openai', 'together'], required=True, help='Provider')
    create_parser.add_argument('--model', required=True, help='Model to fine-tune')
    create_parser.add_argument('--train-file', required=True, help='Training data file')
    create_parser.add_argument('--val-file', help='Validation data file')
    create_parser.add_argument('--epochs', type=int, default=1, help='Number of epochs')
    
    # Run job command
    run_parser = subparsers.add_parser('run', help='Run fine-tuning job')
    run_parser.add_argument('job_id', help='Job ID to run')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show job statistics')
    
    # Models command
    models_parser = subparsers.add_parser('models', help='List available models')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = FinetuningManager()
    
    if args.command == 'list':
        jobs = manager.list_jobs(status=args.status, provider=args.provider)
        print(f"📋 Found {len(jobs)} jobs:")
        for job in jobs:
            print(f"  {job.id[:8]}... | {job.name} | {job.provider} | {job.status}")
    
    elif args.command == 'create':
        if args.provider == 'openai':
            job = manager.create_openai_job(
                name=args.name,
                model=args.model,
                train_file=args.train_file,
                val_file=args.val_file,
                n_epochs=args.epochs
            )
        else:
            job = manager.create_together_job(
                name=args.name,
                model=args.model,
                train_file=args.train_file,
                val_file=args.val_file,
                n_epochs=args.epochs
            )
        print(f"✅ Created job: {job.id}")
    
    elif args.command == 'run':
        job = asyncio.run(manager.run_job(args.job_id))
        print(f"🚀 Job {args.job_id} finished with status: {job.status}")
        if job.fine_tuned_model:
            print(f"📦 Fine-tuned model: {job.fine_tuned_model}")
    
    elif args.command == 'stats':
        stats = manager.get_job_stats()
        print("📊 Job Statistics:")
        print(f"Total jobs: {stats['total_jobs']}")
        print(f"Completed: {stats['completed_jobs']}")
        print(f"Failed: {stats['failed_jobs']}")
        print(f"By status: {stats['by_status']}")
        print(f"By provider: {stats['by_provider']}")
    
    elif args.command == 'models':
        models = manager.get_available_models()
        print("🤖 Available models:")
        for provider, model_list in models.items():
            print(f"{provider.upper()}:")
            for model in model_list[:5]:  # Show first 5
                print(f"  - {model}")
            if len(model_list) > 5:
                print(f"  ... and {len(model_list) - 5} more")


if __name__ == "__main__":
    main()