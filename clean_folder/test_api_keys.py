#!/usr/bin/env python3
"""
API Key Testing Script

This script tests API completions for OpenRouter, OpenAI, and Anthropic
to verify that API keys are working correctly.

Usage:
    python test_api_keys.py
    python test_api_keys.py --provider openrouter
    python test_api_keys.py --provider openai
    python test_api_keys.py --provider anthropic
    python test_api_keys.py --all
"""

import asyncio
import argparse
import os
import sys
from typing import Dict, List, Optional
from dotenv import load_dotenv
import litellm
from litellm import completion, acompletion

# Load environment variables
load_dotenv()

# Test configurations for each provider
API_TESTS = {
    "openrouter": {
        "models": [
            "openrouter/anthropic/claude-3.5-sonnet",
            "openrouter/meta-llama/llama-3.1-8b-instruct",
            "openrouter/google/gemini-pro-1.5"
        ],
        "api_key": "OPENROUTER_API_KEY",
        "provider": "openrouter"
    },
    "openai": {
        "models": [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo"
        ],
        "api_key": "OPENAI_API_KEY", 
        "provider": "openai"
    },
    "anthropic": {
        "models": [
            "anthropic/claude-sonnet-4-5-20250929
        ],
        "api_key": "ANTHROPIC_API_KEY",
        "provider": "anthropic"
    }
}

class APITester:
    """Test API completions for different providers."""
    
    def __init__(self):
        self.results = {}
        self.test_message = "Hello! Please respond with 'API test successful' to confirm this API key is working."
        
    def check_api_key(self, provider: str) -> bool:
        """Check if API key is present for a provider."""
        api_key_name = API_TESTS[provider]["api_key"]
        api_key = os.getenv(api_key_name)
        
        if not api_key:
            print(f"❌ {provider.upper()}: No API key found ({api_key_name})")
            return False
        
        # Check if key looks valid (basic format check)
        if provider == "openrouter" and not api_key.startswith("sk-or-"):
            print(f"⚠️  {provider.upper()}: API key format may be incorrect (should start with 'sk-or-')")
        elif provider == "openai" and not api_key.startswith("sk-"):
            print(f"⚠️  {provider.upper()}: API key format may be incorrect (should start with 'sk-')")
        elif provider == "anthropic" and not api_key.startswith("sk-ant-"):
            print(f"⚠️  {provider.upper()}: API key format may be incorrect (should start with 'sk-ant-')")
        
        print(f"✅ {provider.upper()}: API key found ({api_key[:10]}...)")
        return True
    
    async def test_model(self, provider: str, model: str) -> Dict:
        """Test a specific model with async completion."""
        result = {
            "provider": provider,
            "model": model,
            "success": False,
            "response": None,
            "error": None,
            "latency": None
        }
        
        try:
            import time
            start_time = time.time()
            
            response = await acompletion(
                model=model,
                messages=[{"role": "user", "content": self.test_message}],
                max_tokens=50,
                temperature=0.1
            )
            
            end_time = time.time()
            result["latency"] = round(end_time - start_time, 2)
            result["response"] = response.choices[0].message.content.strip()
            result["success"] = True
            
            print(f"✅ {provider.upper()}/{model}: Success ({result['latency']}s)")
            print(f"   Response: {result['response'][:100]}...")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ {provider.upper()}/{model}: Failed - {e}")
            
        return result
    
    def test_model_sync(self, provider: str, model: str) -> Dict:
        """Test a specific model with sync completion."""
        result = {
            "provider": provider,
            "model": model,
            "success": False,
            "response": None,
            "error": None,
            "latency": None
        }
        
        try:
            import time
            start_time = time.time()
            
            response = completion(
                model=model,
                messages=[{"role": "user", "content": self.test_message}],
                max_tokens=50,
                temperature=0.1
            )
            
            end_time = time.time()
            result["latency"] = round(end_time - start_time, 2)
            result["response"] = response.choices[0].message.content.strip()
            result["success"] = True
            
            print(f"✅ {provider.upper()}/{model}: Success ({result['latency']}s)")
            print(f"   Response: {result['response'][:100]}...")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ {provider.upper()}/{model}: Failed - {e}")
            
        return result
    
    async def test_provider(self, provider: str) -> Dict:
        """Test all models for a specific provider."""
        print(f"\n🔍 Testing {provider.upper()}...")
        print("=" * 50)
        
        if not self.check_api_key(provider):
            return {"provider": provider, "success": False, "error": "No API key"}
        
        provider_results = {
            "provider": provider,
            "success": False,
            "models": [],
            "total_tests": 0,
            "successful_tests": 0
        }
        
        models = API_TESTS[provider]["models"]
        provider_results["total_tests"] = len(models)
        
        for model in models:
            result = await self.test_model(provider, model)
            provider_results["models"].append(result)
            
            if result["success"]:
                provider_results["successful_tests"] += 1
        
        provider_results["success"] = provider_results["successful_tests"] > 0
        
        print(f"\n📊 {provider.upper()} Summary:")
        print(f"   Successful: {provider_results['successful_tests']}/{provider_results['total_tests']}")
        
        return provider_results
    
    def test_provider_sync(self, provider: str) -> Dict:
        """Test all models for a specific provider (sync version)."""
        print(f"\n🔍 Testing {provider.upper()}...")
        print("=" * 50)
        
        if not self.check_api_key(provider):
            return {"provider": provider, "success": False, "error": "No API key"}
        
        provider_results = {
            "provider": provider,
            "success": False,
            "models": [],
            "total_tests": 0,
            "successful_tests": 0
        }
        
        models = API_TESTS[provider]["models"]
        provider_results["total_tests"] = len(models)
        
        for model in models:
            result = self.test_model_sync(provider, model)
            provider_results["models"].append(result)
            
            if result["success"]:
                provider_results["successful_tests"] += 1
        
        provider_results["success"] = provider_results["successful_tests"] > 0
        
        print(f"\n📊 {provider.upper()} Summary:")
        print(f"   Successful: {provider_results['successful_tests']}/{provider_results['total_tests']}")
        
        return provider_results
    
    async def test_all_providers(self) -> Dict:
        """Test all providers."""
        print("🚀 Testing All API Providers")
        print("=" * 50)
        
        all_results = {
            "total_providers": 0,
            "successful_providers": 0,
            "providers": []
        }
        
        for provider in API_TESTS.keys():
            all_results["total_providers"] += 1
            result = await self.test_provider(provider)
            all_results["providers"].append(result)
            
            if result["success"]:
                all_results["successful_providers"] += 1
        
        return all_results
    
    def test_all_providers_sync(self) -> Dict:
        """Test all providers (sync version)."""
        print("🚀 Testing All API Providers")
        print("=" * 50)
        
        all_results = {
            "total_providers": 0,
            "successful_providers": 0,
            "providers": []
        }
        
        for provider in API_TESTS.keys():
            all_results["total_providers"] += 1
            result = self.test_provider_sync(provider)
            all_results["providers"].append(result)
            
            if result["success"]:
                all_results["successful_providers"] += 1
        
        return all_results
    
    def print_summary(self, results: Dict):
        """Print a summary of test results."""
        print("\n" + "=" * 60)
        print("📋 API TEST SUMMARY")
        print("=" * 60)
        
        if "providers" in results:
            # All providers test
            print(f"Total Providers: {results['total_providers']}")
            print(f"Successful Providers: {results['successful_providers']}")
            print()
            
            for provider_result in results["providers"]:
                provider = provider_result["provider"].upper()
                if provider_result["success"]:
                    print(f"✅ {provider}: {provider_result['successful_tests']}/{provider_result['total_tests']} models working")
                else:
                    print(f"❌ {provider}: No models working")
                    
                    # Show specific errors
                    for model_result in provider_result["models"]:
                        if not model_result["success"] and model_result["error"]:
                            print(f"   - {model_result['model']}: {model_result['error']}")
        else:
            # Single provider test
            provider = results["provider"].upper()
            if results["success"]:
                print(f"✅ {provider}: {results['successful_tests']}/{results['total_tests']} models working")
            else:
                print(f"❌ {provider}: No models working")
                
                # Show specific errors
                for model_result in results["models"]:
                    if not model_result["success"] and model_result["error"]:
                        print(f"   - {model_result['model']}: {model_result['error']}")
        
        print("\n💡 Tips:")
        print("   - Check your .env file for correct API keys")
        print("   - Verify API key formats and permissions")
        print("   - Check your account balance/credits")
        print("   - Ensure you're using the correct model names")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test API keys for different providers")
    parser.add_argument("--provider", choices=["openrouter", "openai", "anthropic"], 
                       help="Test specific provider")
    parser.add_argument("--all", action="store_true", help="Test all providers")
    parser.add_argument("--sync", action="store_true", help="Use sync instead of async")
    
    args = parser.parse_args()
    
    tester = APITester()
    
    if args.all:
        if args.sync:
            results = tester.test_all_providers_sync()
        else:
            results = asyncio.run(tester.test_all_providers())
        tester.print_summary(results)
    elif args.provider:
        if args.sync:
            results = tester.test_provider_sync(args.provider)
        else:
            results = asyncio.run(tester.test_provider(args.provider))
        tester.print_summary(results)
    else:
        # Default: test all providers
        if args.sync:
            results = tester.test_all_providers_sync()
        else:
            results = asyncio.run(tester.test_all_providers())
        tester.print_summary(results)

if __name__ == "__main__":
    main()
