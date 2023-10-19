"""
Generating functional and technical requirements 
with the help of LLMs
"""
import inspect
import json
import os
import time
from plugins.llms import get_llm_output
# from llm_functions import get_gpt_output, get_llm_output, gpt_function_calling
import streamlit as st
import prompts
import agents
from agents import *
from helpers import text_areas
from available_functions import funcs_available
import pandas as pd
import re


def get_text_and_code():
    """
    Returns the current requirement text and code
    for the selected view.
    """
    # Get requirements text
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
    return current_code, current_text

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

    # Call the agent coordinator first

    current_code, current_text = get_text_and_code()
    # Generate key from file name, after removing directory and extension
    chat_key = "chat_" + st.session_state.file_path.split('/')[-1].split('.')[0]
    st.session_state.chat_key = chat_key
    
    agents.coordinator(chat_key, current_text=current_text, func_str=current_code)

    # If there is no project description chat in the session state, create one
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # If function calling is not available, the user
    # should tell us if we are working on requirements or code
    if not st.session_state.function_call:
        st.sidebar.radio(
            "Update code or requirements?", 
            ['requirements', 'code'], 
            key=f'current_stage_{st.session_state.stage_num}'
            ) 

    if st.session_state.call_status:
        st.sidebar.header("Call status")
        st.sidebar.info(st.session_state.call_status)
        # st.session_state.chat_status.write("Got some extra information.  Working on it...")
        agents.from_requirements_to_code(
            prompt=st.session_state.call_status,
            current_text=current_text,
            chat_key=chat_key,
            func_str=current_code,
            )
        del st.session_state['call_status']
        st.session_state.ask_llm = True
        
    prompt = st.chat_input("Type here for help", key=f'chat_input_{widget_label}')
    if prompt:
        # Expand the chat window
        st.session_state.chat_status.update(label="Chat", expanded=True)
        # Create the messages from the prompts file
        agents.from_requirements_to_code(
            prompt=prompt,
            current_text=current_text,
            chat_key=chat_key,
            func_str=current_code,
            )
        st.session_state.ask_llm = True

        
    # If there is an error in rendering code,
    # fix it.  No need to wait for user prompt.
    # TODO: Make this an agent
    if 'error' in st.session_state:
        st.error(f"I got this error: {st.session_state.error}")
        if st.button("Fix the error"):
            st.session_state.chat_status.info("I ran into an error.  Fixing it...")
            st.sidebar.warning(chat_key)
            agents.from_requirements_to_code(
                prompt=prompt,
                current_text=current_text,
                chat_key=chat_key,
                func_str=current_code,
            )
            # fix_error_in_code()
            del st.session_state['error']
            st.session_state.ask_llm = True


    if st.session_state.ask_llm:
        # Get the response
        if st.session_state.function_call:    
            content = get_llm_output(
                st.session_state[chat_key], 
                functions=funcs_available(),
                )
        else:
            content = get_llm_output(
                st.session_state[chat_key],
                model='gpt-4',
                )
        
                # Add the response to the chat
        if content:
            st.session_state[chat_key].append(
                {'role': 'assistant', 'content': content}
                )
        st.session_state.ask_llm = False
        if 'error' in st.session_state:
            del st.session_state['error']    

    with st.status("View chat", expanded=True) as st.session_state.chat_status:
        # Create the chat
        chat_container = st.container()

    # TODO: MAKE FUNCTION CALL GENERATE A PROMPT FOR NEXT ROUND.
    # This has to be below the chat container so that the buttons 
    # are displayed below the chat.
    if 'last_function_call' in st.session_state:
        # If there is a function call, run it
        st.session_state.call_status = make_function_call(chat_key)
    

    # Display the messages
    with chat_container:
        display_messages(chat_key)
    if st.session_state.token == 'admin':
        if st.sidebar.checkbox("Show chat messages"):
            st.sidebar.json(st.session_state[chat_key])

    # If there is call status, rerun the app
    if st.session_state.call_status:
        # Delete call status
        del st.session_state['call_status']
        st.rerun()

    # TODO: Move all of this to an agent.
    # If requirements exist, have a button to code
    if st.session_state.file_path:
        button_name = None
        if os.path.exists(st.session_state.file_path + '.txt'):
            with open(st.session_state.file_path + '.txt', 'r') as f:
                requirements = f.read()
            if 'technical requirements' in requirements.lower():
                button_name = ":keyboard: Generate code"
            # Check if the .py file exists
            if os.path.exists(st.session_state.file_path + '.py'):
                # If it does, show the code
                with open(st.session_state.file_path + '.py', 'r') as f:
                    code = f.read()
                button_name = "🔄 Update code"
                            # Give option to delete code
                if st.sidebar.button("❌ Delete code"):
                    os.remove(st.session_state.file_path + '.py')
                    st.session_state.stage_num += 1
                    st.session_state[f"current_stage_{st.session_state.stage_num}"] = 'requirements'
                    st.rerun()

            else:
                code = None
            if 'error' in st.session_state:
                button_name = "🔄 Fix error"
            if button_name:
                if st.button(button_name):
                    sysetm_instruction = agents.get_code_instructions(requirements, code)
                    prompt = "Generate code by following the requirements carefully and completely and return full code only."
                    messages = [
                        {"role": "system", "content": sysetm_instruction},
                        {"role": "user", "content": prompt},
                        ]
                    content = get_llm_output(messages, model='gpt-4')

                    # Add the input to the chat
                    st.session_state[chat_key].append({'role': 'user', 'content': prompt})
                    # Add the response to the chat
                    st.session_state[chat_key].append(
                        {'role': 'assistant', 'content': content}
                        )
                    st.session_state.stage_num += 1
                    st.session_state[f"current_stage_{st.session_state.stage_num}"] = 'code'
                    
                    st.rerun()

    return None


def display_messages(chat_key):
    # Display the user and assistant messages
    for i,msg in enumerate(st.session_state[chat_key]):
        if msg['role'] in ['user', 'assistant']:
            the_content = msg['content']
            with st.chat_message(msg['role']):
                st.markdown(the_content)
    return None
    
def make_function_call(chat_key):
    """
    If the llm response includes a 
    function call, do that.
    """
    func_info = st.session_state.last_function_call
    # If func_info is a string, convert it to a dict
    if isinstance(func_info, str):
        func_info = json.loads(func_info)
    
    # Get function name and arguments
    func_name = func_info['name']

    # If function call is returned by openai, the arguments will be a string
    # Convert that to a dict
    if isinstance(func_info['arguments'], str):
        try:
            arguments = eval(func_info['arguments'])
        except:
            arguments = json.loads(func_info['arguments'])
    else:
        arguments = func_info['arguments']

    res = None
    # Ask the user if they want to run the function
    button_label = func_name.replace('_', ' ').upper()
    
    # Do not run the code by default
    run_code = False
    if func_name in ['data_agent']:
        run_code = True
    st.sidebar.info(arguments)
    if not run_code:
        if st.button(f":fire: {button_label} :fire:"):
            run_code = True
    
    if run_code:
        # Run the function
        with st.spinner(f'Running {func_name}...'):
            func = globals()[func_name]
            argspec = inspect.getfullargspec(func)
            # Isolate the arguments that are needed
            arguments = {k: v for k, v in arguments.items() if k in argspec.args}
            func_res = globals()[func_name](**arguments)
            
            # Remove the function call from the session state
            # Note: This may have been deleted already
            if 'last_function_call' in st.session_state:
                del st.session_state['last_function_call']
            if func_res:
                # Add the response to the chat
                st.session_state[chat_key].append(
                    {'role': 'system', 'content': func_res}
                    )
                res = func_res
            st.rerun()
        
    return res

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
    st.toast(f"Saved requirements")
    # Increase stage number to change the widget
    st.session_state.stage_num += 1
    st.session_state[f"current_stage_{st.session_state.stage_num}"] = 'code'
    return f"I saved the requirements.  Can you generate the code now based on the requirements?"

def save_code_to_file(content: str):
    """
    Saves the based on the user requirement to the file.  
    File name and path is taken from the selected view, and so only 
    the file content is needed.
    
    Parameters:
    -----------
    content: str
        The code based on user requirements to save to the file.
    Returns:
    --------
    Success message: str
    """
    # Get the file path
    file_path = st.session_state.file_path + '.py'
    
    # If the main function is called in the start of any line, comment it out
    content_lines = content.split('\n')
    for i, line in enumerate(content_lines):
        if line.strip().startswith('main('):
            content_lines[i] = '# ' + line
        elif "if __name__" in line:
            content_lines[i] = '# ' + line
        else:
            content_lines[i] = line

    # join the lines back into a string
    content = '\n'.join(content_lines)
    
    
    
    # If there is a line with __name__ in it, comment it out
    if "if __name__ == '__main__':" in content:
        content = content.replace("if __name__ == '__main__':", "# if __name__ == '__main__':")


    # Save the code to the file
    with open(file_path, 'w') as f:
        f.write(content)
    # Add the message on saving to the chat and then rerun the app
    st.session_state[st.session_state.chat_key].append(
        {'role': 'user', 'content': f"I saved code to.  Will test it now."}
        )
    st.toast("I updated the code.")
    st.toast("Chat window will close in 2 seconds.")
    # Delete the function call from the session state
    del st.session_state['last_function_call']
    # Delete the error from the session state
    if 'error' in st.session_state:
        del st.session_state['error']
    st.session_state.chat_status.update(label="Expand to view chat", expanded=False)
    time.sleep(2)
    st.rerun()
    # Note the message will not be returned since we are rerunning the app here.
    return None

# TODO: Deprecate this.  We should just call agents.
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
    st.session_state[f"current_stage_{st.session_state.stage_num}"] = stage_name
    if st.session_state.show_developer_options:
        st.sidebar.warning(f"Current stage is {stage_name}")
    return f"We are now focussing on {stage_name} now."

