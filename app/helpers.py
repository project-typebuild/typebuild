import streamlit as st
import os
from streamlit_ace import st_ace

def update_text_file(file, value):
    """
    On Change, this saves the current labels to a file called labels.md in the root folder.
    """
    
    with open(file, 'w') as f:
        f.write(value)
    return None


def text_areas(file, key, widget_label):
    """
    We have stored text that the user can edit.  
    Given a file, load the text from the file and display it in a text area.
    On change, save the text to the file.
    """
    # Get the directory and create it if it does not exist
    directory = os.path.dirname(file)
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Load current value from file.  If not create empty file
    if not os.path.exists(file):
        with open(file, 'w') as f:
            f.write('')
    with open(file, 'r') as f:
        value = f.read()
    
    out = st_ace(
        value=value,
        placeholder="Write your requirements here...",
        language="markdown",
        theme="github",
        show_gutter=False,
        font_size=14,
        wrap=True,
        keybinding="vscode",
        key=f"{key}_{st.session_state.project_folder}",
        )
    
    if out != value:
        update_text_file(file, value=out)
    # Add user requirements to session state
    st.session_state.user_requirements = out
    return out

def extract_python_code(text):
    """
    Extracts Python code snippets from within triple backticks in the given text.
    
    Parameters:
    -----------
    text: str
        The text to search for Python code snippets.
    
    Returns:
    --------
    A list of Python code snippets (strings).
    """
    snippets = []
    in_code_block = False
    for line in text.split('\n'):
        if line.strip() == '```python':
            in_code_block = True
            code = ''
        elif line.strip() == '```' and in_code_block:
            in_code_block = False
            snippets.append(code)
        elif in_code_block:
            code += line + '\n'
    
    # Evaluate code snippets and return python objects
    correct_code = []
    for i, snippet in enumerate(snippets):
        try:
            correct_code.append(eval(snippet))
        except:
            pass
    return correct_code

def get_approved_libraries():
    return "import streamlit as st\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nfrom glob import glob\nimport datetime"
