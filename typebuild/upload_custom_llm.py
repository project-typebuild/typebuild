import streamlit as st
import os
import tempfile
import time
import ast

def upload_file():
    """
    This function handles the file uploading process.
    Returns the uploaded file and its extension.
    """
    uploaded_file = st.file_uploader("Upload a file", type=['py'])
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1]
        return uploaded_file, file_extension
    return None, None

def verify_functions(file_path, function_dict):
    """
    Verifies the functions in the uploaded file.
    Returns True if verification is successful, False otherwise.
    """
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append({'function_name': node.name, 'args': [arg.arg for arg in node.args.args]})

    custom_llm_output = next((func for func in functions if func['function_name'] == 'custom_llm_output'), None)
    if not custom_llm_output or set(custom_llm_output['args']) != set(function_dict['args']):
        return False
    return True

def save_file(uploaded_file, file_path):
    """
    Saves the uploaded file to the specified path.
    """
    if st.button('Save Custom LLM', key='save_custom_llm'):
        success_message = st.empty()
        # Get the typebuild root directory from the session state
        typebuild_root = st.session_state.typebuild_root
        file_path = os.path.join(typebuild_root, 'custom_llm.py')

        # if the file already exists, ask the user if they want to overwrite it or not
        if os.path.exists(file_path):
            overwrite = st.radio('File already exists, do you want to overwrite it?', ['Yes', 'No'], index=1)
            if overwrite == 'Yes':
                with st.spinner('Saving file...'):
                    time.sleep(2)
                    # Save the file to the data folder
                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    st.success(f'File saved successfully')
            else:
                st.warning('File not saved')
        else:
            # Save the file to the data folder
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            st.success(f'File saved successfully')

    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())

def upload_custom_llm_file():
    """
    Main function to upload a custom LLM file.
    Calls other functions to handle specific parts of the process.
    """
    uploaded_file, file_extension = upload_file()
    if uploaded_file is not None:
        with tempfile.TemporaryDirectory() as tmp_folder:
            tmp_file_path = os.path.join(tmp_folder, uploaded_file.name)
            if verify_functions(tmp_file_path, {'function_name': 'custom_llm_output', 'args': ['input', 'max_tokens', 'temperature', 'model', 'functions']}):
                success_message = st.empty()
                success_message.success('Functions verified successfully.')
                # File saving logic
                save_file(uploaded_file, tmp_file_path)
            else:
                st.error('Function verification failed.')
    return None