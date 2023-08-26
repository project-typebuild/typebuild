import streamlit as st
import openai
openai.api_key = st.secrets.openai.key
import os
import re

def get_llm_output(input, max_tokens=800, temperature=0, model='gpt-4'):
    if 'gpt' in model:
        res = get_gpt_output(messages=input, max_tokens=max_tokens, temperature=temperature, model=model)
    else:
        res = "Unknown model"
    return res

def get_gpt_output(messages, model, max_tokens=800, temperature=0):
    """
    Gets the output from GPT-3.5-turbo.  Needs system_instruction as input.
    It derives the messages from the session state, so that the messgaes
    can evolve.
    """

    response = openai.ChatCompletion.create(
                model=model,
                messages = messages,
                max_tokens=max_tokens,
                temperature=temperature,
                n=1
            )
    return response.choices[0].message.content


def get_gpt_output_old(system_instruction, max_tokens=800, temperature=0):
    """
    Gets the output from GPT-3.5-turbo.  Needs system_instruction as input.
    It derives the messages from the session state, so that the messgaes
    can evolve.
    """
    messages = [
        {"role": "system", "content": system_instruction}]

    if st.session_state.messages:
        messages.extend(st.session_state.messages)

    # Get the total length of the message content
    total_length = len(' '.join([m['content'] for m in messages]))
    if total_length > 6000:
        model = 'gpt-3.5-turbo-16k'
    else:
        model = 'gpt-3.5-turbo'
    if st.session_state.use_gpt4:
        model = 'gpt-4'
    response = openai.ChatCompletion.create(
                model=model,
                messages = messages,
                max_tokens=max_tokens,
                temperature=temperature,
                n=1
            )
    return response.choices[0].message.content

def get_gpt_output_static(prompt, system_instruction, max_tokens=200, temperature=0):
    """
    Given the prompt and system_instruction, returns the output from GPT-3.5-turbo.
    This is a static version, so it does not use the session state.
    """    
    response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages =[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                n=1
            )
    return response.choices[0].message.content



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

    pattern = r"\|\|\|([\s\S]*?)\|\|\|"
    matches = re.findall(pattern, response)
    
    return matches
