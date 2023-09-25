import os
import re
import streamlit as st

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
) 
dir_path = os.path.dirname(os.path.realpath(__file__))

def get_llm_output(messages, max_tokens=3000, temperature=0.4, model='gpt-4', functions=[]):
    """
    This checks if there is a custom_llm.py in the plugins directory 
    If there is, it uses that.
    If not, it uses the openai llm.
    """
    # Check if there is a custom_llm.py in the plugins directory
    # If there is, use that
    progress_status = st.sidebar.empty()
    # progress_status.warning('Generating response from LLM...')
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if os.path.exists(f'{dir_path}/custom_llm.py'):
        from plugins.custom_llm import custom_llm_output
        content = custom_llm_output(messages, max_tokens=max_tokens, temperature=temperature, model=model, functions=functions)
    else:
        msg = get_openai_output(messages, max_tokens=max_tokens, temperature=temperature, model=model, functions=functions)
        content = msg.get('content', None)
        if 'function_call' in msg:
            func_call = msg.get('function_call', None)
            st.session_state.last_function_call = func_call
    
    progress_status.info("Extracting information from response...")
    if content:
        st.session_state.last_response = content
    # We can get back code or requirements in multiple forms
    # Look for each form and extract the code or requirements

    # Recent GPT models return function_call as a separate json object
    # Look for that first.
    # If there are triple backticks, we expect code
    if '```' in str(content) or '|||' in str(content):
        # NOTE: THERE IS AN ASSUMPTION THAT WE CAN'T GET BOTH CODE AND REQUIREMENTS
        extracted, code_or_requirement = parse_code_or_requirements_from_response(content)
        
        if code_or_requirement == 'code':
            my_func = 'save_code_to_file'
            func_call = {'name': my_func, 'arguments': {'code_str':extracted}}
            st.session_state.last_function_call = func_call
        
        if code_or_requirement == 'requirements':
            my_func = 'save_requirements_to_file'
            func_call = {'name': my_func, 'arguments': {'content':extracted}}
            st.session_state.last_function_call = func_call

    # Stop ask llm
    st.session_state.ask_llm = False
    # progress_status.success('Response generated!')
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
    import openai
    openai.key = st.secrets.openai.key
    st.session_state.last_request = messages
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
    
    # Stop ask llm
    st.session_state.ask_llm = False    
    return msg


def parse_code_or_requirements_from_response(response):
    """
    The LLM can return code or requirements in the content.  
    Ideally, requirements come in triple pipe delimiters, 
    but sometimes they come in triple backticks.

    Figure out which one it is and return the extracted code or requirements.
    """
    # If there are ```, it could be code or requirements
    code_or_requirement = None
    if '```' in response:
        # If it's python code, it should have at least one function in it
        if 'def ' in response:
            extracted = parse_code_from_response(response)
            code_or_requirement = 'code'
        # If it's not python code, it's probably requirements
        else:
            extracted = parse_modified_user_requirements_from_response(response)
            code_or_requirement = 'requirements'
    # If there are |||, it's probably requirements
    elif '|||' in response:
        extracted = parse_modified_user_requirements_from_response(response)
        code_or_requirement = 'requirements'
    else:
        extracted = None
    return extracted, code_or_requirement
            



def parse_code_from_response(response):

    """
    Returns the code from the response from LLM.
    In the prompt to code, we have asked the LLM to return the code inside triple backticks.

    Args:
    - response (str): The response from LLM

    Returns:
    - matches (list): A list of strings with the code

    """

    pattern = r"```python([\s\S]*?)```"
    matches = re.findall(pattern, response)
    if len(matches) > 0:
        matches = '\n'.join(matches)
    else:
        matches = matches[0]
    return matches

def parse_modified_user_requirements_from_response(response):
    
    """
    Returns the modified user requirements from the response from LLM. 
    In the prompt to modify, we have asked the LLM to return the modified user requirements inside triple pipe delimiters.

    Args:
    - response (str): The response from LLM

    Returns:
    - matches (list): A list of strings with the modified user requirements

    """
    if '|||' in response:
        pattern = r"\|\|\|([\s\S]*?)\|\|\|"
    if '```' in response:
        # It shouldnt have ```python in it
        pattern = r"```([\s\S]*?)```"

    matches = re.findall(pattern, response)
    # if there are multiple matches, join by new line
    if len(matches) > 0:
        matches = '\n'.join(matches)
    else:
        matches = matches[0]
    return matches
