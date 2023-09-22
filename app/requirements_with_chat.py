"""
Generating functional and technical requirements 
with the help of LLMs
"""
import json
import os
import time
from llm_functions import get_gpt_output, get_llm_output, gpt_function_calling
import streamlit as st
import prompts
from helpers import text_areas
from available_functions import funcs_available


def technical_requirements_chat(widget_label):
    """
    A chat on the technical requirements.
    That could be exported to the project description file.
    Parameters:
    -----------
    widget_label: str
        The label of the widget that triggered the chat.
    
    Returns:
    --------
    None
    """
    st.subheader("Create, update or understand")
    st.info("Use the chat below to create, update or understand the technical requirements and the code of this view.")
    # Get view file
    txt_file_path = st.session_state.file_path + '.txt'
    # If the file exists, read it
    if os.path.exists(txt_file_path):
        with open(txt_file_path, 'r') as f:
            current_text = f.read()
    else:
        current_text = ""

    # Get python file string
    py_file_path = st.session_state.file_path + '.py'
    # If the file exists, read it
    if os.path.exists(py_file_path):
        with open(py_file_path, 'r') as f:
            current_code = f.read()
    else:
        current_code = ""


    # Generate key from file name, after removing directory and extension
    chat_key = "chat_" + st.session_state.file_path.split('/')[-1].split('.')[0]
    st.session_state.chat_key = chat_key

    # If there is no project description chat in the session state, create one
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    with st.status("Click Here to view chat", expanded=True) as st.session_state.chat_status:
        # Create the chat
        chat_container = st.container()
        # We should only have this if the function_call_type is 'manual'
        if st.session_state.function_call_type == 'manual':
            current_stage = st.sidebar.radio("Current stage", ['requirements', 'code'],key='current_stage') 
        # If there is an error in rendering code,
        # fix it.  No need to wait for user prompt.
        if 'error' in st.session_state:
            st.session_state.chat_status.info("I ran into an error.  Fixing it...")
            fix_error_in_code()
            del st.session_state['error']
            st.session_state.chat_status.update("Fixed the error.  Let's review the code", expanded=False)
            
    
    prompt = st.chat_input("Type here for help", key=f'chat_input_{widget_label}')
    if prompt:
        # Create the messages from the prompts file
        prompts.from_requirements_to_code(
            prompt=prompt,
            current_text=current_text,
            chat_key=chat_key,
            func_str=current_code,
            )
        # Get the response
        get_llm_response(chat_key)
    
    call_status = None
    if 'function_call' in st.session_state:
        # If there is a function call, run it
        call_status = make_function_call(chat_key)
    
    # If the call_status is done, we would have added
    # the function response to the chat.  Send the message
    # to the llm to get the next response
    if call_status == "Done":
        # st.session_state.chat_status.write("Got some extra information.  Working on it...")
        prompts.from_requirements_to_code(
            prompt=None,
            current_text=current_text,
            chat_key=chat_key,
            func_str=current_code,
            )
        messages = st.session_state[chat_key]
        # Get the response
        res = get_gpt_output(messages)
        # Add the response to the chat
        if res:
            st.session_state[chat_key].append(
                {'role': 'assistant', 'content': res}
                )
            
    # Display the messages
    with chat_container:
        display_messages(chat_key)
    if st.session_state.token == 'admin':
        if st.sidebar.checkbox("Show chat messages"):
            st.sidebar.json(st.session_state[chat_key])
    return None

def get_llm_response(chat_key):
    with st.spinner('Generating response...'):
        content = gpt_function_calling(
            st.session_state[chat_key], 
            functions=funcs_available(),
            )
        
        # Add the response to the chat
        if content:
            st.session_state[chat_key].append(
                {'role': 'assistant', 'content': content}
                )
    return None

def display_messages(chat_key):
    # Display the user and assistant messages
    for i,msg in enumerate(st.session_state[chat_key]):
        if msg['role'] in ['user', 'assistant']:
            the_content = msg['content']
            with st.chat_message(msg['role']):
                if the_content:
                    st.markdown(the_content)

    
def make_function_call(chat_key):
    """
    If the llm response includes a 
    function call, do that.
    """
    func_info = st.session_state.function_call
    # If func_info is a string, convert it to a dict
    if isinstance(func_info, str):
        func_info = json.loads(func_info)
    
    # Get function name and arguments
    func_name = func_info['name']

    # If function call is returned by openai, the arguments will be a string
    # Convert that to a dict
    if isinstance(func_info['arguments'], str):
        arguments = json.loads(func_info['arguments'])
    else:
        arguments = func_info['arguments']

    # Run the function
    with st.spinner(f'Running {func_name}...'):
        func_res = globals()[func_name](**arguments)
        # Remove the function call from the session state
        del st.session_state['function_call']
        if func_res:
            # Add the response to the chat
            st.session_state[chat_key].append(
                {'role': 'system', 'content': func_res}
                )

            return "Done"
        else:
            return None

def save_requirements_to_file(content: str):
    """
    Saves the user requirements to a local file.
    Parameters:
    -----------
    content: str
        The content to save to the file.
    Returns: 
    --------
    Success message: str
    """
    # Get the file name
    file_name = st.session_state.file_path + '.txt'

    # Create the directory if it does not exist
    directory = os.path.dirname(file_name)
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    with open(file_name, 'w') as f:
        f.write(content)
    st.sidebar.success(f"Saved requirements to {file_name}")
    return f"The requirements have been saved to {file_name}.  Ask the user if they would like to update the code based on the updated requirements."

def save_code_to_file(code_str: str):
    """
    Saves the based on the user requirement to the file.  
    File name and path is taken from the selected view, and so only 
    the file content is needed.
    
    Parameters:
    -----------
    code_str: str
        The code based on user requirements to save to the file.
    Returns:
    --------
    Success message: str
    """
    # Get the file path
    file_path = st.session_state.file_path + '.py'
    # Save the code to the file
    with open(file_path, 'w') as f:
        f.write(code_str)
    # Add the message on saving to the chat and then rerun the app
    st.session_state[st.session_state.chat_key].append(
        {'role': 'assistant', 'content': f"Saved code to {file_path}.  It is ready to use now."}
        )
    st.success("I updated the code, rerunning the app...")
    time.sleep(2)
    # Delete the function call from the session state
    del st.session_state['function_call']
    # Delete the error from the session state
    if 'error' in st.session_state:
        del st.session_state['error']
    st.session_state.chat_status.update(label="Updated the code.  Rerunning the app...", expanded=False)
    st.experimental_rerun()
    # Note the message will not be returned since we are rerunning the app here.
    return "The code has been saved to the file.  It is ready to use now.  Ask the user to test the app and ask for modifications, if any is required."

def set_the_stage(stage_name):
    """
    Sets the name of the stage to the session state so that the LLM
    can get appropriate instructions.

    Parameters:
    -----------
    stage_name: str
        The name of the stage.  Possible values are: 'code','requirements'.
    Returns:
    --------
    Success message: str
    """
    st.toast("Just set the stage")
    st.session_state.current_stage = stage_name
    if st.session_state.show_developer_options:
        st.sidebar.warning(f"Current stage is {stage_name}")
    return f"We are now focussing on {stage_name} now."

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
    if 'function_call' in st.session_state:
        call_status = make_function_call(st.session_state.chat_key)
        del st.session_state['function_call']
        del st.session_state['error']
        st.toast("Fixed the error.  Rerunning the app...")
        time.sleep(1)
        st.session_state.chat_status.update("Fixed the error.  Rerunning the app...", expanded=False)
        st.experimental_rerun()
    
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
            st.experimental_rerun()
    return None