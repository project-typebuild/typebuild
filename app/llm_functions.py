import streamlit as st
import openai
openai.api_key = st.secrets.openai.key
import os
import re
import time
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
) 
def get_llm_output(input, max_tokens=800, temperature=0.4, model='gpt-4'):

    """
    Given an input, get the output from the LLM.  Default is openai's gpt-4.

    Args:
    - input (list): A list of messages in the format                 
                messages =[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}],

                system_instruction is the instruction given to the system to generate the response using the prompt.
                prompt is the input given by the user.

    - model (str): The model to use.  Default is gpt-4.
    - max_tokens (int): The maximum number of tokens to generate, default 800
    - temperature (float): The temperature for the model. The higher the temperature, the more random the output

    """
    if 'gpt' in model:
        res = get_gpt_output(
            messages=input, 
            max_tokens=max_tokens, 
            temperature=temperature, 
            model=model
            )
    else:
        res = "Unknown model"
    return res

# @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def get_gpt_output(messages, model='gpt-4', max_tokens=800, temperature=0.4):
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



    st.session_state.last_request = messages
    response = openai.ChatCompletion.create(
                model=model,
                messages = messages,
                max_tokens=max_tokens,
                temperature=temperature,
                n=1
            )
    st.session_state.last_response = response.choices[0].message
    return response.choices[0].message.content

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def gpt_function_calling(messages, model='gpt-4-0613', max_tokens=3000, temperature=0.4, functions=[]):
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
                    model="gpt-4",
                    messages = messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    n=1,
                )
    msg = response.choices[0].message
    content = msg.get('content', None)
    
    if content:
        st.session_state.last_response = response.choices[0].message
    # Get the function_call_type from session state
    if 'function_call_type' in st.session_state:
        function_call_type = st.session_state.function_call_type
    else:
        function_call_type = 'auto'

    if function_call_type == 'auto':
        func_call = msg.get('function_call', None)
        if func_call:
            # Save to session state
            st.session_state.function_call = func_call
            st.session_state.last_function_call = func_call

    if function_call_type == 'manual':
        if '```' in str(content):
            current_stage = st.session_state.current_stage
            if current_stage == 'code':
                extracted_code = parse_code_from_response(content)
                my_func = 'save_code_to_file'
                func_call = {'name': my_func, 'arguments': {'code_str':extracted_code}}
            elif current_stage == 'requirements':
                extracted_requirements = parse_modified_user_requirements_from_response(content)
                my_func = 'save_requirements_to_file'
                func_call = {'name': my_func, 'arguments': {'content':extracted_requirements}}
            st.session_state.function_call = func_call
            st.session_state.last_function_call = func_call
    return content

#----------FUNCTIONS TO GENERATE PROMPTS----------------


def col_names_and_types(df):
    """Given a df, it returns a string with the column names and types"""
    col_names = df.columns
    col_types = df.dtypes
    col_names_and_types = []
    for col_name, col_type in zip(col_names, col_types):
        col_names_and_types.append(f"{col_name}: {col_type}")
    col_names = '\n- '.join(col_names_and_types)
    buf = f"""The Dataframe has the following columns: 
    
    - {col_names}"""
    return buf

def get_sample_data_as_markdown(df):
    """
    Gets a sample of 5 lines, if there are at least 3 lines.
    Else, gets the whole thing.
    """
    if len(df) > 5:
        buf = df.head(5).to_markdown(index=False)
    else:
        buf = df.to_markdown(index=False)
    return buf

def get_function_prompt(df, default=None):
    """Returns a prompt for GPT-3"""
    
    prompt_for_table = ''
    
    if st.sidebar.checkbox(f"Show sample data", value=False):
        st.dataframe(df.sample(5))
    prompt_for_table += col_names_and_types(df) + '\n'
    buf = get_sample_data_as_markdown(df)
    prompt_for_table += f"\nHERE IS SOME SAMPLE DATA:\n{buf}\n"
    if not default:
        default = ""
    label = 'I want to'
    if 'i_want_to' in st.session_state:
        if st.session_state.i_want_to:
            label = st.session_state.i_want_to
        
    i_want_to = st.text_area(label, value=default)

    # Check if there is a the_func in the session state
    # with the name my_func.  If yes, add this as context.
    func_prompt = ''
    if 'the_func' in st.session_state:
        if 'my_func' in st.session_state.the_func:
            func_prompt = f"FYI: This is the function I am trying to modify: {st.session_state.the_func}"

    prompt = f"""
    I am working on a dataframe named df.  

    {prompt_for_table}

    {func_prompt}
    
    I WANT TO: {i_want_to}

    """

    return prompt

def create_new_function_with_llm(system_message, prompt):
    """
    This helps create a new function based on 
    natural language description of what the function should do.

    The function can be saved to views.py for later use.
    """

    info_state = st.empty()
    if st.button("Go GPT!", key='main button'):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        info_state.info("Getting response from GPT")
        response = get_gpt_output(system_message)
        st.session_state.response = response
        info_state.warning("Response received from GPT")    
        func_found = parse_function_from_response()
        if func_found:
            info_state.success("Extracted function from response")
            st.code(st.session_state.the_func, language='python')
        else:
            info_state.error("Could not extract function from response")
            st.code(response, language='python')
    return None

def clean_function(the_func):
    """
    Cleans the function in a number of ways.
    """
    # Remove the first line if just mentions the language
    if the_func.startswith('python'):
        the_func = '\n'.join(the_func.split('\n')[1:])
    
    # Remove import statements
    revised_func = ''
    for line in the_func.split('\n'):
        if  line.startswith('import'):
            pass
        # If it's a function def, add it
        elif line.startswith('def'):
            revised_func += line + '\n'
        # If it's calling my_func, pass
        elif 'my_func' in line:
            pass
        else:
            revised_func += line + '\n'

    st.session_state.the_func = revised_func
    return revised_func

def parse_function_from_response():
    
    # If there are triple backticks, get the function

    # the_func is the first thing between triple backticks, if any
    # If the func is a list, take the first one
    if "```" in st.session_state.response:
        the_func = st.session_state.response.split('```')
        func_found = True
        the_func = the_func[1].strip()
        the_func = clean_function(the_func)
        
    # If we get a response with backticks but has the function
    elif 'my_func' in st.session_state.response:
        func_found = True
        the_func = st.session_state.response.strip()
        the_func = clean_function(the_func)
    else:
        the_func = "None"
        func_found = False
    
    return func_found

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

    # pattern = r"\|\|\|([\s\S]*?)\|\|\|"
    # It shouldnt have ```python in it
    pattern = r"```([\s\S]*?)```"
    matches = re.findall(pattern, response)
    # if there are multiple matches, join by new line
    if len(matches) > 0:
        matches = '\n'.join(matches)
    else:
        matches = matches[0]
    return matches
