#!/usr/bin/env python3
"""
Test script for OpenAI API with fine-tuned model.
Tests the API key and the specified fine-tuned model.
"""

import os
import sys
from dotenv import load_dotenv
import openai
from openai import OpenAI

def load_environment():
    """Load environment variables from .env file."""
    load_dotenv()
    
    # Check if API key is loaded
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please make sure you have a .env file with OPENAI_API_KEY set")
        return None
    
    print(f"✅ API key loaded successfully (starts with: {api_key[:10]}...)")
    return api_key

def test_openai_api(api_key, model_name):
    """Test the OpenAI API with the specified model."""
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        print(f"\n🧪 Testing OpenAI API with model: {model_name}")
        print("=" * 60)
        
        # Test with a simple completion
        test_prompt = "Hello, can you help me with a customer service question?"
        
        print(f"📝 Test prompt: {test_prompt}")
        print("\n⏳ Sending request to OpenAI...")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful customer service assistant."},
                {"role": "user", "content": test_prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        # Extract and display the response
        if response.choices and len(response.choices) > 0:
            assistant_message = response.choices[0].message.content
            print(f"\n✅ API call successful!")
            print(f"📊 Model: {response.model}")
            print(f"🔢 Tokens used: {response.usage.total_tokens if response.usage else 'N/A'}")
            print(f"💬 Response: {assistant_message}")
            
            return True
        else:
            print("❌ No response received from the API")
            return False
            
    except openai.AuthenticationError as e:
        print(f"❌ Authentication Error: {e}")
        print("Please check your API key")
        return False
        
    except openai.PermissionDeniedError as e:
        print(f"❌ Permission Denied: {e}")
        print("You may not have access to this fine-tuned model")
        return False
        
    except openai.NotFoundError as e:
        print(f"❌ Model Not Found: {e}")
        print("The specified model may not exist or may not be accessible")
        return False
        
    except openai.RateLimitError as e:
        print(f"❌ Rate Limit Error: {e}")
        print("You may have exceeded your API rate limits")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def main():
    """Main function to run the API test."""
    print("🚀 OpenAI API Test Script")
    print("=" * 40)
    
    # Load environment variables
    api_key = load_environment()
    if not api_key:
        sys.exit(1)
    
    # Define the model to test
    model_name = "ft:gpt-4.1-mini-2025-04-14:scale-safety-research-1:customer-service-eval-20250927:CKQkJ8NI"
    
    # Test the API
    success = test_openai_api(api_key, model_name)
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("Your OpenAI API key and fine-tuned model are working correctly.")
    else:
        print("\n💥 Test failed!")
        print("Please check the error messages above and verify your setup.")
        sys.exit(1)

if __name__ == "__main__":
    main()
