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

def fix_error_in_code():
    """
    Sends the error and the current code to the LLM to fix the error
    """
    prompts.get_prompt_to_fix_error()
    messages = st.session_state.error_messages
    with st.spinner('Fixing an error I ran into...'):
        st.error(f"I got this error: {st.session_state.error}")
        response = gpt_function_calling(messages, functions=funcs_available())

    # If there is a function call, run it first
    if 'last_function_call' in st.session_state:
        call_status = make_function_call(st.session_state.chat_key)
        del st.session_state['last_function_call']
        del st.session_state['error']
        st.toast("Fixed the error.  Rerunning the app...")
        time.sleep(1)
        st.session_state.chat_status.update("Fixed the error.  Rerunning the app...", expanded=False)
        st.rerun()
    
    # If there is a response, add it to the chat
    if response:
        st.session_state[st.session_state.chat_key].append(
            {'role': 'assistant', 'content': response}
            )
        # Also append it to error messages
        st.session_state.error_messages.append(
            {'role': 'assistant', 'content': response}
            )
        error_prompt = st.chat_input("Type your response to error resolution", key='error_prompt')
        if error_prompt:
            st.session_state[st.session_state.error_messages].append(
                {'role': 'user', 'content': error_prompt}
                )
            # Restart the process that will invoke this function again
            st.rerun()
    return None


# From llm_functions.py
def get_llm_output(input, max_tokens=800, temperature=0.4, model='gpt-4', functions=[]):

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
def gpt_function_calling(messages, model='gpt-4', max_tokens=3000, temperature=0.4, functions=[]):
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

# From blueprint_code.py
def generate_code_from_user_requirements(df=None, mod_requirements=None, current_code=None, confirmed=False):

    """
    The function that generates code from user requirements. 

    Args:
    - df: A pandas dataframe with sample data (optional, default None)

    Returns:
    - None

    """

    # Define the prompt
    st.header("Your requirements")
    user_requirements = user_requirement_for_view()
    
    if st.button("Generate the view"):
        get_code(user_requirements=user_requirements, mod_requirements=mod_requirements, current_code=current_code)
        st.rerun()
    return None

def get_code(user_requirements="", mod_requirements=None, current_code=None):

    # Get data description
    data_model_file = st.session_state.project_folder + '/data_model.txt'
    with open(data_model_file, 'r') as f:
        data_model = f.read()


    messages = get_prompt_to_code(
        user_requirements,
        data_description=data_model,
        mod_requirements=mod_requirements,
        current_code=current_code,
        )
    with st.spinner('Generating code...'):
        response = get_llm_output(messages)
    
    st.session_state.response = response
    st.session_state.user_requirements = user_requirements
    st.session_state.messages = messages
    st.session_state.code = '\n\n'.join(parse_code_from_response(response))
    
    return None

def modify_code():
    """
    The function that modifies code based on user requirements.

    Args:
    - user_requirements: initial user requirements. 
    - all_function_descriptions: descriptions of all the functions available
    - df: A pandas dataframe with sample data (optional, default None)

    Returns:
    - None

    """

    # Get the current code from the current file
    file = st.session_state.file_path + '.py'
    with open(file, 'r') as f:
        current_code = f.read()
    # Define the prompt
    st.header("Modify requirements")
    user_requirements = user_requirement_for_view()
    st.info("If requirements are correct but the output is not as expected, tell us what changes you want to make to the function.")
    change_requested = st.text_area("What changes do you want to make to the function?")
    if st.button("Modify"):
        get_code(mod_requirements=change_requested, current_code=current_code)
    return None


def create_secrets_file():
    """
    If the secrets file does not exist, create it.
    """
    # Create directory if it doesn't exist
    if not os.path.exists('.streamlit'):
        os.makedirs('.streamlit')
    if not os.path.exists('.streamlit/secrets.toml'):
        with open('.streamlit/secrets.toml', 'w') as f:
            f.write('')
    return None


def get_llm_key_or_function():
    """
    For this system to work, we need LLM keys or functions.
    """
    # Check if openai key is in secrets
    if 'openai' not in st.secrets:
        st.warning("Please add your OpenAI key to secrets.toml")
        st.stop()