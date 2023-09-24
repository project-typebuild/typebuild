import streamlit as st
import os
from streamlit_ace import st_ace
import toml
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

#--------------CODE TO RUN AT THE START OF THE APP----------------
def set_function_calling_availability(toggle=False):
    """
    This sets the function calling availability to the session state.
    If function_call is not in session state, it looks at secrets.

    Args:
    - toggle: bool, whether to toggle the function calling availability.
    """
    # st.sidebar.warning(st.secrets.function_call_type)
    
    # Get the project folder from the session state
    user_folder = st.session_state.user_folder
    # Create the secrets.toml file if it does not exist
    secrets_file_path = user_folder + '/secrets.toml'

    
    # Look at the secrets if function_call is not in session state
    if 'function_call' not in st.session_state:
        if not os.path.exists(secrets_file_path):
            st.session_state.function_call = False
        else:
            with open(secrets_file_path, 'r') as f:
                config = toml.load(f)
            if config != {}:
                if 'function_call_availabilty' in config:
                    st.session_state.function_call = config['function_call_availabilty']
                else:
                    st.session_state.function_call = False
            else:
                st.session_state.function_call = False

    # Toggle the function calling availability
    if toggle:
        st.session_state.function_call = not st.session_state.function_call

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

def create_user_folder():
    """
    Creates a user folder in the .typebuild folder.
    """
    # Get the user folder from the session state
    if 'user_folder' not in st.session_state:
        home_dir = os.path.expanduser("~")
        st.session_state.user_folder = os.path.join(home_dir, ".typebuild", 'users' ,st.session_state.token)
    
    return None

def starter_code():
    """
    Functions that need to be run at hte top of the app.
    """
    create_user_folder()
    create_secrets_file()
    set_function_calling_availability()

    return None
    
