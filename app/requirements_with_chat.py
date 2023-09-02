"""
Generating functional and technical requirements 
with the help of LLMs
"""
import os
from llm_functions import get_gpt_output, get_llm_output, gpt_function_calling
import streamlit as st
import prompts
from helpers import text_areas

def funcs_available():
    """
    Returns a list of functions available for the user to call.
    """
    f = [
        {
            "name": "save_requirements_to_file",
            "description": "Saves the user requirements to a file, given the file name and the content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "The name of the file to save the requirements to."
                        },
                    "content": {
                        "type": "string",
                        "description": "The content to save to the file."
                        },
                    },
                
                "required": ["file_name", "content"]

            }

        },
        {
            "name": "save_code_to_file",
            "description": "Saves the based on the user requirement to the file.  \nFile name and path is taken from the selected view, and so only \nthe file content is needed.\n\nParameters:\n-----------\ncode_str: str\n    The code based on user requirements to save to the file.\nReturns:\n--------\nSuccess message: str",
            "parameters": {
                "type": "object",
                "properties": {
                    "code_str": {
                        "type": "string",
                        "description": "The code based on user requirements to save to the file."
                    }
            }},
            "required": ["code_str"]
            },
        {
            "name": "send_code_to_llm",
            "description": "Call this to explain or modify the current code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dummy_arg": {
                        "type": "string",
                        "description": "A dummy argument to make the function signature"
                    }
            }},
            "required": []
        }
    ]
    return f


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
    st.header("Technical requirements")
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

    # Create the chat    
    chat_container = st.container()
    prompt = st.chat_input("Discuss requirements here", key=f'chat_input_{widget_label}')
    if prompt:
        # Create the messages from the prompts file
        prompts.blueprint_technical_requirements(
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
        with st.spinner("Getting second response...."):
            prompts.blueprint_technical_requirements(
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
    
    func_name = func_info['name']
    arguments = eval(func_info['arguments'])
    with st.spinner(f'Running {func_name}...'):
        func_res = globals()[func_name](**arguments)
        if func_res:
            # Add the response to the chat
            st.session_state[chat_key].append(
                {'role': 'assistant', 'content': func_res}
                )
        # Remove the function call from the session state
        del st.session_state['function_call']
    return "Done"
        

def save_requirements_to_file(file_name: str, content: str):
    """
    Saves the user requirements to a local file.
    Parameters:
    -----------
    file_name: str
        The name of the file to save the requirements to.
    content: str
        The content to save to the file.
    Returns: 
    --------
    Success message: str
    """
    project_folder = st.session_state.project_folder
    file = f"{project_folder}/test/{file_name}"
    # Create the directory if it does not exist
    directory = os.path.dirname(file)
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    with open(file, 'w') as f:
        f.write(content)
    return f"Saved requirements to {file_name}"

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
    return f"Saved code to {file_path}.  It is ready to use now."

def send_code_to_llm(dummy_arg: str):
    """
    Upon request from the LLM, this
    sends the code to the LLM.

    parameters:
    -----------
    Dummy_arg: str
        A dummy argument to make the function signature
    Returns:
    --------
    Success message: str
    """
    file_name = st.session_state.file_path + '.py'
    if os.path.exists(file_name):
        with open(file_name, 'r') as f:
            code_str = f.read()
        code_str = "This is the current code:\n\n" + code_str + "\n\n"
        st.sidebar.warning("Added the code to the session state")
    else:
        code_str = "No code file exists yet."
        st.sidebar.warning(f"{file_name} does not exist yet.")
    # Add the code to the session state
    st.session_state.code_str = code_str

    return None