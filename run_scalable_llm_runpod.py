import logging
import json
import os
import asyncio
import aiohttp
import time
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScalingMode(Enum):
    """Different scaling modes for RunPod inference."""
    SERVERLESS = "serverless"  # Auto-scaling serverless endpoints
    DEDICATED = "dedicated"    # Dedicated pods with manual scaling
    HYBRID = "hybrid"         # Mix of both based on load

@dataclass
class RunPodConfig:
    """Configuration for RunPod scaling inference."""
    endpoint_id: str
    api_key: str
    model_name: str = "default"
    scaling_mode: ScalingMode = ScalingMode.SERVERLESS
    max_concurrent_requests: int = 100
    timeout_seconds: int = 300
    min_replicas: int = 0
    max_replicas: int = 10
    scale_up_threshold: float = 0.8  # Scale up when 80% capacity
    scale_down_threshold: float = 0.2  # Scale down when below 20% capacity
    base_url: str = "https://api.runpod.ai/v2"

class RunPodScalableInference:
    """
    Scalable LLM inference system using RunPod with automatic scaling.
    
    This class provides:
    - Automatic scaling based on request load
    - Queue management for high-throughput scenarios  
    - Cost optimization through intelligent resource management
    - Retry mechanisms and error handling
    - Health monitoring and metrics collection
    """
    
    def __init__(self, config: RunPodConfig):
        self.config = config
        self.session = None
        self.active_requests = 0
        self.request_queue = asyncio.Queue()
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0,
            "current_replicas": 0
        }
        self._headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_endpoint_status(self) -> Dict[str, Any]:
        """Get current endpoint status and scaling information."""
        url = f"{self.config.base_url}/{self.config.endpoint_id}/status"
        
        async with self.session.get(url, headers=self._headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Failed to get endpoint status: {response.status}")
                return {}
    
    async def scale_endpoint(self, target_replicas: int) -> bool:
        """Scale the endpoint to target number of replicas."""
        if self.config.scaling_mode == ScalingMode.SERVERLESS:
            # Serverless endpoints scale automatically
            logger.info("Serverless endpoint scales automatically")
            return True
        
        url = f"{self.config.base_url}/{self.config.endpoint_id}/scale"
        payload = {"replicas": target_replicas}
        
        try:
            async with self.session.post(url, headers=self._headers, json=payload) as response:
                if response.status == 200:
                    self.metrics["current_replicas"] = target_replicas
                    logger.info(f"Scaled endpoint to {target_replicas} replicas")
                    return True
                else:
                    logger.error(f"Failed to scale endpoint: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error scaling endpoint: {e}")
            return False
    
    async def check_and_scale(self):
        """Check current load and scale accordingly."""
        if self.config.scaling_mode == ScalingMode.SERVERLESS:
            return  # Serverless handles this automatically
        
        current_load = self.active_requests / self.config.max_concurrent_requests
        current_replicas = self.metrics["current_replicas"]
        
        if current_load > self.config.scale_up_threshold and current_replicas < self.config.max_replicas:
            new_replicas = min(current_replicas + 1, self.config.max_replicas)
            await self.scale_endpoint(new_replicas)
        elif current_load < self.config.scale_down_threshold and current_replicas > self.config.min_replicas:
            new_replicas = max(current_replicas - 1, self.config.min_replicas)
            await self.scale_endpoint(new_replicas)
    
    async def run_inference(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run inference on RunPod with automatic scaling.
        
        Args:
            messages: List of messages for the conversation
            model: Model name to use (optional, uses config default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the model
            
        Returns:
            Dict containing the response and metadata
        """
        start_time = time.time()
        self.active_requests += 1
        self.metrics["total_requests"] += 1
        
        try:
            # Check if we need to scale
            await self.check_and_scale()
            
            # Prepare the request payload
            payload = {
                "input": {
                    "messages": messages,
                    "model": model or self.config.model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }
            }
            
            # Make the request
            url = f"{self.config.base_url}/{self.config.endpoint_id}/run"
            
            async with self.session.post(
                url, 
                headers=self._headers, 
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    self.metrics["successful_requests"] += 1
                    
                    # Update average response time
                    response_time = time.time() - start_time
                    current_avg = self.metrics["average_response_time"]
                    total_successful = self.metrics["successful_requests"]
                    self.metrics["average_response_time"] = (
                        (current_avg * (total_successful - 1) + response_time) / total_successful
                    )
                    
                    return {
                        "success": True,
                        "data": result,
                        "response_time": response_time,
                        "endpoint_id": self.config.endpoint_id
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"RunPod API error {response.status}: {error_text}")
                    self.metrics["failed_requests"] += 1
                    return {
                        "success": False,
                        "error": f"API error {response.status}: {error_text}",
                        "response_time": time.time() - start_time
                    }
                    
        except asyncio.TimeoutError:
            logger.error(f"Request timeout after {self.config.timeout_seconds} seconds")
            self.metrics["failed_requests"] += 1
            return {
                "success": False,
                "error": "Request timeout",
                "response_time": time.time() - start_time
            }
        except Exception as e:
            logger.error(f"Unexpected error during inference: {e}")
            self.metrics["failed_requests"] += 1
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
        finally:
            self.active_requests -= 1
    
    async def batch_inference(
        self,
        batch_requests: List[Dict[str, Any]],
        max_concurrent: int = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple inference requests concurrently.
        
        Args:
            batch_requests: List of request dictionaries
            max_concurrent: Maximum concurrent requests (uses config default if None)
            
        Returns:
            List of response dictionaries
        """
        max_concurrent = max_concurrent or self.config.max_concurrent_requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_request(request_data):
            async with semaphore:
                return await self.run_inference(**request_data)
        
        logger.info(f"Processing batch of {len(batch_requests)} requests")
        tasks = [process_request(req) for req in batch_requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Request {i} failed with exception: {result}")
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "request_index": i
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return {
            **self.metrics,
            "active_requests": self.active_requests,
            "queue_size": self.request_queue.qsize(),
            "success_rate": (
                self.metrics["successful_requests"] / max(1, self.metrics["total_requests"])
            ) * 100,
            "endpoint_id": self.config.endpoint_id,
            "scaling_mode": self.config.scaling_mode.value
        }
    
    async def health_check(self) -> bool:
        """Perform a health check on the endpoint."""
        try:
            status = await self.get_endpoint_status()
            return status.get("status") == "RUNNING"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

# Convenience functions for backward compatibility

async def load_vllm_lora_adapter_scalable(
    adapter_hf_name: str,
    endpoint_id: str = None,
    api_key: str = None
) -> bool:
    """
    Load a LoRA adapter on a scalable RunPod endpoint.
    
    Args:
        adapter_hf_name: Name of the adapter to load
        endpoint_id: RunPod endpoint ID (uses env var if None)
        api_key: RunPod API key (uses env var if None)
        
    Returns:
        True if successful, False otherwise
    """
    endpoint_id = endpoint_id or os.environ.get("RUNPOD_ENDPOINT_ID")
    api_key = api_key or os.environ.get("RUNPOD_API_KEY")
    
    if not endpoint_id or not api_key:
        logger.error("RunPod endpoint ID and API key must be provided")
        return False
    
    config = RunPodConfig(
        endpoint_id=endpoint_id,
        api_key=api_key,
        model_name=adapter_hf_name
    )
    
    async with RunPodScalableInference(config) as inference:
        try:
            # Check if adapter is already loaded
            url = f"{config.base_url}/{endpoint_id}/openai/v1/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            
            async with inference.session.get(url, headers=headers) as response:
                if response.status == 200:
                    models_data = await response.json()
                    model_ids = [model["id"] for model in models_data.get("data", [])]
                    if adapter_hf_name in model_ids:
                        logger.info(f"LoRA adapter {adapter_hf_name} is already loaded")
                        return True
            
            # Load the adapter
            load_url = f"{config.base_url}/{endpoint_id}/openai/v1/load_lora_adapter"
            payload = {"lora_name": adapter_hf_name, "lora_path": adapter_hf_name}
            
            async with inference.session.post(
                load_url, 
                headers=headers, 
                json=payload,
                timeout=aiohttp.ClientTimeout(total=1200)  # 20 minutes
            ) as response:
                
                if response.status == 200:
                    logger.info(f"LoRA adapter {adapter_hf_name} loaded successfully")
                    return True
                elif response.status == 400:
                    response_data = await response.json()
                    if "has already been loaded" in response_data.get("message", ""):
                        logger.info(f"LoRA adapter {adapter_hf_name} was already loaded")
                        return True
                
                logger.error(f"Failed to load adapter: {response.status}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading LoRA adapter: {e}")
            return False

# Example usage and testing
async def example_usage():
    """Example of how to use the scalable RunPod inference system."""
    
    # Configuration
    config = RunPodConfig(
        endpoint_id=os.environ.get("RUNPOD_ENDPOINT_ID", "your-endpoint-id"),
        api_key=os.environ.get("RUNPOD_API_KEY", "your-api-key"),
        model_name="your-model-name",
        scaling_mode=ScalingMode.SERVERLESS,
        max_concurrent_requests=50
    )
    
    # Single inference example
    async with RunPodScalableInference(config) as inference:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ]
        
        result = await inference.run_inference(
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        
        if result["success"]:
            print(f"Response: {result['data']}")
            print(f"Response time: {result['response_time']:.2f}s")
        else:
            print(f"Error: {result['error']}")
        
        # Check metrics
        metrics = inference.get_metrics()
        print(f"Metrics: {json.dumps(metrics, indent=2)}")
    
    # Batch inference example
    batch_requests = [
        {
            "messages": [{"role": "user", "content": f"Count to {i}"}],
            "temperature": 0.5,
            "max_tokens": 50
        }
        for i in range(1, 6)
    ]
    
    async with RunPodScalableInference(config) as inference:
        batch_results = await inference.batch_inference(batch_requests)
        
        for i, result in enumerate(batch_results):
            if result["success"]:
                print(f"Batch request {i} succeeded in {result['response_time']:.2f}s")
            else:
                print(f"Batch request {i} failed: {result['error']}")

if __name__ == "__main__":
    # Run example (requires proper environment variables)
    asyncio.run(example_usage())
