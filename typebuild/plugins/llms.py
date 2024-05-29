import os
import re
import time
import streamlit as st
from openai import OpenAI
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

from extractors import Extractors

def last_few_messages(messages):
    """
    Returns the last few messages from the given list of messages.

    Long messages get rejected by the LLM. So, this function keeps the system message, which is the first message,
    and the last 3 user and system messages.

    Args:
        messages (list): A list of messages.

    Returns:
        list: The last few messages from the given list.
    """
    if not messages:
        messages = []
    last_messages = []
    # Get all system messages
    system_messages = [i for i in messages if i['role'] == 'system']
    last_messages.extend(system_messages)
    # Get the last 7 user or assistant messages
    user_assistant_messages = [i for i in messages if i['role'] in ['user', 'assistant']]
    last_messages.extend(user_assistant_messages[-20:])
    return last_messages

def get_llm_output(messages, max_tokens=2500, temperature=0.4, model='gpt-4', functions=[], json_mode=False):

    """

    This function retrieves the output from the Language Model (LLM) based on the given messages.

    Args:
        messages (list): List of messages exchanged between the user and the LLM.
        max_tokens (int, optional): The maximum number of tokens to generate in the LLM output. Defaults to 2500.
        temperature (float, optional): The temperature parameter for controlling the randomness of the LLM output. 
            Higher values (e.g., 1.0) make the output more random, while lower values (e.g., 0.1) make it more deterministic. 
            Defaults to 0.4.
        model (str, optional): The name of the LLM model to use. Defaults to 'gpt-4'.
        functions (list, optional): List of functions to be used by the LLM. Defaults to an empty list.

    Returns:
        str: The generated output from the LLM.

    Raises:
        None

    Notes:
        - If there is a custom_llm.py file in the plugins directory, it will be used instead of the default LLM.
        - If the 'claude-2' model is requested and available, it will be used instead of the default LLM.
        - The function may return code or requirements in multiple forms, which need to be extracted separately.
        - If a function call is received from the LLM, it will be stored in the session state.
    """
    # Check if there is a custom_llm.py in the plugins directory
    # If there is, use that
    # Get just the last few messages
    messages = last_few_messages(messages)
    # st.session_state.all_messages.extend(messages)
    st.session_state.last_request = messages
    typebuild_root = st.session_state.typebuild_root

    # Make default tool calls as None
    tool_calls = None
    # TODO: ADD JSON MODEL IN CUSTOM LLM
    if os.path.exists(os.path.join(typebuild_root, 'custom_llm.py')):
        from custom_llm import custom_llm_output
        # TODO: ADD TOOL CALLS
        content = custom_llm_output(messages, max_tokens=max_tokens, temperature=temperature, model=model, functions=functions)
    # If claude is requested and available, use claude
    elif model == 'claude-2' and 'claude_key' in st.session_state:
        content = get_claude_response(messages, max_tokens=max_tokens)
    else:
        content, tool_calls = get_openai_output(messages, max_tokens=max_tokens, temperature=temperature, model=model, functions=functions, json_mode=json_mode)
        # content = msg.get('content', None)
        # if 'function_call' in msg:
        #     func_call = msg.get('function_call', None)
        #     st.session_state.last_function_call = func_call
        #     st.sidebar.info("Got a function call from LLM")
    
    
    if content:
        st.session_state.last_response = content
        # st.session_state.all_messages.append({'role': 'assistant', 'content': content})
    # We can get back code or requirements in multiple forms
    # Look for each form and extract the code or requirements


    import time
    st.success(f"Response from LLM: {content}")
    st.session_state.all_messages.append({'role': 'assistant', 'content': content})
    # st.balloons()
    return content, tool_calls


def get_openai_output(messages, max_tokens=3000, temperature=0.4, model='gpt-4', functions=[], json_mode=False):
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
    # Enable adding the key here.
    api_key = st.session_state.openai_key
    client = OpenAI(api_key=api_key)
    if '4' in model:
        model = "gpt-4-turbo-preview"
    params = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "n": 1,
        "messages": messages
    }
    if functions:
        params['functions'] = functions

    if not json_mode:
        # Look for the word "json" in the messages
        for i in messages:
            if "json" in i['content'].lower():
                json_mode = True
                break
    if json_mode:
        params['response_format'] = {"type": "json_object"}

    response = client.chat.completions.create(**params)
    
    msg = response.choices[0].message.content
    tool_calls = response.choices[0].message.function_call
    # If tool_calls is not a list, make it a list
    # This will allow us to make multiple tools calls in one go, if needed
    
    # We are assuming one call at a time
    st.header("Tool calls")
    st.write(tool_calls)
    time.sleep(2)
    tool_call_list = []
    if tool_calls:
        if not isinstance(tool_calls, list):
            tool_calls = [tool_calls]
        for t in tool_calls:
            tool_call = {}
            name = t.name
            arguments = json.loads(t.arguments)
            tool_call['tool_name'] = name
            if 'endpoint_' in name:
                endpoint = name.replace('endpoint_', '/')
                arguments['endpoint'] = endpoint
                tool_call['tool_name'] = 'endpoint'
            tool_call['arguments'] = arguments
                        
            tool_call_list.append(tool_call)
        
        st.session_state.tool_result = tool_calls
    return msg, tool_call_list

def get_claude_response(messages, max_tokens=2000, model='haiku'):
    """
    Generates a response from the Claude model based on the given messages.

    Args:
        messages (list): A list of dictionaries representing the conversation messages.
            Each dictionary should have 'role' and 'content' keys, where 'role' can be
            either 'assistant' or 'human', and 'content' contains the message content.
        max_tokens (int, optional): The maximum number of tokens to generate in the response.
            Defaults to 2000.

    Returns:
        str: The generated response from the Claude model.
    """
    opus = "claude-3-opus-20240229"
    haiku = "claude-3-haiku-20240307"
    if model == 'opus':
        model = opus
    else:
        model = haiku
    ant = Anthropic(
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
    response = ant.completions.create(
        prompt=prompt,
        model=model,
        temperature=0.4,
        max_tokens_to_sample=max_tokens,
    )
    return response.content[0].text