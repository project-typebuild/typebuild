import os
import re
import streamlit as st
import openai
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
) 
dir_path = os.path.dirname(os.path.realpath(__file__))
import json

import sys
sys.path.append(st.session_state.typebuild_root)

def last_few_messages(messages):
    """
    Long messages get rejected by the LLM.  So,
    - Will keep the system message, which is the first message
    - Will keep the last 3 user and system messages
    """
    last_messages = []
    if messages:
        # Get the first message
        last_messages.append(messages[0])
    # Get the last 3 user or assistant messages
    user_assistant_messages = [i for i in messages if i['role'] in ['user', 'assistant']]
    last_messages.extend(user_assistant_messages[-7:])
    return last_messages

def get_llm_output(messages, max_tokens=2500, temperature=0.4, model='gpt-4', functions=[]):
    """
    This checks if there is a custom_llm.py in the plugins directory 
    If there is, it uses that.
    If not, it uses the openai llm.
    """
    # Check if there is a custom_llm.py in the plugins directory
    # If there is, use that
    # Get just the last few messages
    messages = last_few_messages(messages)
    st.session_state.last_request = messages
    typebuild_root = st.session_state.typebuild_root
    if os.path.exists(os.path.join(typebuild_root, 'custom_llm.py')):
        from custom_llm import custom_llm_output

        content = custom_llm_output(messages, max_tokens=max_tokens, temperature=temperature, model=model, functions=functions)
    # If claude is requested and available, use claude
    elif model == 'claude-2' and 'claude_key' in st.session_state:
        content = get_claude_response(messages, max_tokens=max_tokens)
    else:
        msg = get_openai_output(messages, max_tokens=max_tokens, temperature=temperature, model=model, functions=functions)
        content = msg.get('content', None)
        if 'function_call' in msg:
            func_call = msg.get('function_call', None)
            st.session_state.last_function_call = func_call
            st.sidebar.info("Got a function call from LLM")
    
    
    if content:
        st.session_state.last_response = content
    # We can get back code or requirements in multiple forms
    # Look for each form and extract the code or requirements

    # Recent GPT models return function_call as a separate json object
    # Look for that first.
    # If there are triple backticks, we expect code
    
       
    if '```' in str(content) or '|||' in str(content):
        # NOTE: THERE IS AN ASSUMPTION THAT WE CAN'T GET BOTH CODE AND REQUIREMENTS
        extracted, function_name = parse_func_call_info(content)
        func_call = {'name': function_name, 'arguments': {'content':extracted}}
        st.session_state.last_function_call = func_call



    return content


def get_openai_output(messages, max_tokens=3000, temperature=0.4, model='gpt-4', functions=[]):
    """
    Gets the output from GPT models. default is gpt-4. 

    Args:
    - messages (list): A list of messages in the format                 
                messages =[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}],

                system_instruction is the instruction given to the system to generate the response using the prompt.

    - model (str): The model to use.  Default is gpt-4.
    - max_tokens (int): The maximum number of tokens to generate, default 800
    - temperature (float): The temperature for the model. The higher the temperature, the more random the output
    """
    if functions:
        response = openai.ChatCompletion.create(
                    model="gpt-4-0613",
                    messages = messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    n=1,
                    functions=functions,
                )
    else:
        response = openai.ChatCompletion.create(
                    model=model,
                    messages = messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    n=1,
                )
    msg = response.choices[0].message
    
    return msg

def get_claude_response(messages, max_tokens=2000):
    anthropic = Anthropic(
        api_key=st.session_state.claude_key,
    )
    # Since claude has a higher max_tokens, let's increase the limit
    max_tokens = int(max_tokens * 2)
    prompt = ""
    for i in messages:
        if i['role'] == 'assistant':
            prompt += f"{AI_PROMPT} {i['content']}\n\n"
        else:
            prompt += f"{HUMAN_PROMPT} {i['content']}\n\n"

    prompt += AI_PROMPT
    response = anthropic.completions.create(
        prompt=prompt,
        stop_sequences = [anthropic.HUMAN_PROMPT],
        model="claude-2",
        temperature=0.4,
        max_tokens_to_sample=max_tokens,
    )
    return response.completion

