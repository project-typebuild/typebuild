"""
Generating functional and technical requirements 
with the help of LLMs
"""
import os
from llm_functions import get_llm_output, gpt_function_calling
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
    # Generate key from file name, after removing directory and extension
    chat_key = f'chat_{"test"}'
    # If there is no project description chat in the session state, create one
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []


    # functional_requirement = st.text_input("Enter functional requirement here")
    # # Derive file name from widget label by replacing spaces with underscores
    # file_name = widget_label.replace(' ', '_').lower()
    # # Store the file in views folder in the project folder
    # txt_file = f"{st.session_state.project_folder}/views/{file_name}.txt"    
    # text = text_areas(txt_file, f"text_{file_name}", widget_label)


    
    chat_container = st.container()
    prompt = st.chat_input("Discuss requirements here", key=f'chat_input_{widget_label}')
    if prompt:
        # Create the messages from the prompts file
        prompts.blueprint_technical_requirements(
            prompt=prompt,
            functional_requirement="",
            current_text="",
            chat_key=chat_key,
            )
        with st.spinner('Generating response...'):
            res = gpt_function_calling(
                st.session_state[chat_key], 
                functions=funcs_available(),
                )
            
            # Add the response to the chat
            st.session_state[chat_key].append({'role': 'assistant', 'content': res})
    
    # Display the user and assistant messages
    with chat_container:
        for i,msg in enumerate(st.session_state[chat_key]):
            if msg['role'] in ['user', 'assistant']:
                with st.chat_message(msg['role']):
                    # if st.checkbox("Edit", key=f"edit_{i}"):
                    #     use_editor(msg['content'], i, chat_key)
                    # else:
                    #     st.markdown(msg['content'])
                    st.markdown(msg['content'])
    
    if 'function_response' in st.session_state:
        r = st.session_state.function_response
        if st.checkbox("Show function response"):
            func_info = r['choices'][0]["message"].get('function_call', None)
            st.write(func_info)
            if func_info:
                func_name = func_info['name']
                arguments = eval(func_info['arguments'])
                if st.button("Run function"):
                    globals()[func_name](**arguments)

    return None

def quick_test(n):
    st.success(n)
    st.balloons()


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
    st.success(f"Saved requirements to {file_name}")
    st.balloons()
    return f"Saved requirements to {file_name}"