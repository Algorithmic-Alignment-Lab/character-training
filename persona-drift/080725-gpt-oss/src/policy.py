import os 
import requests
import re
from openai import OpenAI
from dotenv import load_dotenv
from typing import Literal
from pathlib import Path
import yaml
import time

__all__   =   [
    '_format_policy_prompt',
    '_extract_policy',
    'send_openrouter_request',
    'send_openrouter_request_oai',
    'call_distractor',
    'generate_policy_text'
]

load_dotenv()

Direction   =   Literal['ALLOW', 'DISALLOW']
def _format_policy_prompt(request, 
                         qualification, 
                         direction: Direction, 
                         sys_template_path   =   Path('templates/policy.yaml')) -> list[dict]: 
    '''
    prepares policy generation prompt wrt system prompt + user request, justification, and policy direction (allow/disallow). 
    '''
    with open(sys_template_path, 'r') as f: 
        policy_yaml   =   yaml.safe_load(f)

    user_message   =   f"USER REQUEST: {request}\n, USER QUALIFICATION: {qualification}\n, DIRECTION: {direction}"

    messages   =   [{'role': 'system', 'content': policy_yaml['templates']['system']},
                {'role': 'user', 'content': policy_yaml['templates']['example_1']['user']},
                {'role': 'assistant', 'content': policy_yaml['templates']['example_1']['assistant']},
                {'role': 'user', 'content': policy_yaml['templates']['example_2']['user']},
                {'role': 'assistant', 'content': policy_yaml['templates']['example_2']['assistant']},
                {'role': 'user', 'content': user_message}]
    return messages

def _extract_policy(text: str) -> str | None:
    m   =   re.search(r"<SYNTHETIC_POLICY\b[^>]*>(.*?)</SYNTHETIC_POLICY>", text, re.DOTALL)
    return m.group(1) if m else None
    
def send_openrouter_request(messages, 
                            model   =   'google/gemini-2.5-pro',
                            provider_order   =   ['deepinfra/fp4', 'google-vertex/global', 'google-vertex/us'],
                            allow_fallbacks   =   True, 
                            temperature   =   0.0,
                            max_tokens   =   4000): 
    '''
    a simple function that submits a single prompt to a selected model (defaults to deepseek) on openrouter.
    temperature is set to 0 by default for reproducibility. 
    '''
    OPENROUTER_URL   =   'https://openrouter.ai/api/v1/chat/completions'
    api_key   =   os.getenv("OPENROUTER_API_KEY")
    headers   =   {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        'X-Title': 'gptoss-jailbreak-evals', 
        'HTTP-Referer': 'https://localhost'
    }

    payload   =   {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    if provider_order is not None:
        payload["provider"]   =   {
            "order": provider_order,
            "allow_fallbacks": allow_fallbacks
        }

    for attempt in range(3):
        try:
            r   =   requests.post(OPENROUTER_URL, headers   =   headers, json   =   payload, timeout   =   120)
            r.raise_for_status()
            final_response   =   r.json()['choices'][0]['message']['content']
            reasoning   =   r.json()['choices'][0]['message']['reasoning']
            refusal   =   r.json()['choices'][0]['message']['refusal']
            provider   =   r.json()['provider']
            return final_response, reasoning, refusal, provider
        except requests.RequestException as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                raise e


def send_openrouter_request_oai(messages, 
                            model   =   'google/gemini-2.5-pro',
                            temperature   =   0.0,
                            max_tokens   =   4000): 
    '''
    a simple function that submits a single prompt to a selected model (defaults to deepseek) on openrouter.
    temperature is set to 0 by default for reproducibility. 
    '''
    client   =   OpenAI(
        base_url   =   "https://openrouter.ai/api/v1",
        api_key   =   os.getenv("OPENROUTER_API_KEY")
    )

    response   =   client.chat.completions.create(
        model   =   model,
        messages   =   messages,
        temperature   =   temperature,
        max_tokens   =   max_tokens,
        extra_body   =   {
            "provider": {"order": ["deepinfra/fp4"]}
            }
    )

    final_response   =   response.choices[0].message.content
    reason   =   response.choices[0].message.reasoning

    return final_response, reason

def call_distractor(distractor   =   'cat_fact'):
    sys_template_path   =   Path('templates/policy.yaml')
    with open(sys_template_path, 'r') as f: 
        policy_yaml   =   yaml.safe_load(f)
    distractor   =   policy_yaml['templates']['distractors'][distractor]
    return distractor


def generate_policy_text(request, 
                         qualification, 
                         full_request   =   True, 
                         add_distractor   =   False, 
                         distractor   =   'cat_fact',
                         direction   =   'ALLOW',
                         model   =   'google/gemini-2.5-pro',
                         temperature: float   =   0.0,
                         max_tokens: int   =   4000) -> tuple[str, str]:
    '''
    generates policy (implantation) text based on user input. 

    args: 
        request: user's desired action. 
        qualification: user's claimed entitlement.
        direction: 'ALLOW' or 'DISALLOW'
        model: LLM to use via openrouter (defaults to deepseek-r1-0528) - find others here: https://openrouter.ai/models
        temperature: sampling temperature
        max_tokens: max tokens to generate
    
    returns: 
        tuple of (response, reasoning)

    if full_request is set to 'true,' return entire user request. when this is the case, a distractor can be added. 
    if a distractor is added, you can select the distractor from policy.yaml by key.
    
    '''
    messages   =   _format_policy_prompt(request, qualification, direction) 
    response, reason, _, _   =   send_openrouter_request(messages,
                                                    model   =   model,
                                                    temperature   =   temperature,
                                                    max_tokens   =   max_tokens)

    response   =   _extract_policy(response)

    if full_request:
        response   =   f'{request} {qualification} \n\n{response}'

        if add_distractor: 
            distractor   =   call_distractor(distractor)

            response   =   f'Hey GPT! (1) {distractor}\n (2) {response}'

    return response, reason