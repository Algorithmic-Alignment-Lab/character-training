#!/usr/bin/env python3

import sqlite3
import json
from fine_tuning_manager import FinetuningManager

# Initialize manager
manager = FinetuningManager()

# Get the failed job
job = manager.get_job("d7d9db18-7be8-47ee-bcb5-050beb12e6e4")

if job:
    print("🔍 Job Status Analysis:")
    print(f"Job ID: {job.id}")
    print(f"Name: {job.name}")
    print(f"Status: {job.status}")
    print(f"Error: {job.error_message}")
    print(f"Provider: {job.provider}")
    print(f"Model: {job.model}")
    print(f"Training file: {job.train_file}")
    print(f"Config: {json.dumps(job.config, indent=2)}")
else:
    print("❌ Job not found")