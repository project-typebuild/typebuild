import streamlit as st

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
) 

def get_llm_output(messages, max_tokens=3000, temperature=0.4, model='gpt-4', functions=[]):
    """
    This checks if there is a custom_llm.py in the plugins directory 
    If there is, it uses that.
    If not, it uses the openai llm.
    """
    # Check if there is a custom_llm.py in the plugins directory
    # If there is, use that
    try:
        from plugins.custom_llm import get_llm_output
        return get_llm_output(messages, max_tokens, temperature, model, functions)
    except:
        return get_openai_output(messages, max_tokens, temperature, model, functions)
    


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
    content = msg.get('content', None)
    
    if content:
        st.session_state.last_response = response.choices[0].message
    
    # We can get back code or requirements in multiple forms
    # Look for each form and extract the code or requirements

    # Recent GPT models return function_call as a separate json object
    # Look for that first.
    if 'function_call' in msg:
        func_call = msg.get('function_call', None)
        st.session_state.last_function_call = func_call
    else:
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
    return content


