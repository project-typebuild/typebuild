import tempfile
import streamlit as st
import os
from llm_access import LLMConfigurator
import session_state_management
import toml
from simple_auth import logout
import openai
import time
import os
from glob import glob
import pandas as pd
from extractors import Extractors

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
    return "import streamlit as st\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nfrom glob import glob\nimport datetime\nimport faker\nfrom faker import Faker, import faker-commerce"

#--------------CODE TO RUN AT THE START OF THE APP----------------
def set_function_calling_availability(toggle=False):
    """
    This sets the function calling availability to the session state.
    If function_call is not in session state, it looks at secrets.

    Args:
    - toggle: bool, whether to toggle the function calling availability.
    """

    # Get the secrets file path
    secrets_file_path = st.session_state.secrets_file_path

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

def search_placeholder():
    """
    This function is a placeholder for the search function. On the menu bar, when the user clicks on the search icon, this function is called and do nothing.
    
    Returns:
        None: If no placeholder is found.
    """
    return None

def google_search_interface_for_menu():
    """
    This function calls the `google_search_interface` function from the `tools.google_search` module.
    It is used to provide a menu interface for performing Google searches.
    """
    from tools.google_search import GoogleSearcher
    google_tool = GoogleSearcher()
    google_tool.google_search_interface()
    return None

def youtube_search_interface_for_menu():
    """
    This function serves as an interface for searching YouTube transcripts.
    It imports the 'youtube_transcript_search' module and calls its 'main' function.
    """
    from tools.youtube_transcript_search import YoutubeSearcher
    youtube_tool = YoutubeSearcher()
    youtube_tool.youtube_search_interface()

    return None

def data_management_interface():
    """
    This function serves as an interface for managing data.
    It imports the 'data_management' module and calls its 'main' function.
    """
    from data_management.uploader import DataUploader
    if 'DataUploader' not in st.session_state:
        data_manager = DataUploader()
        st.session_state.DataUploader = data_manager
    else:
        data_manager = st.session_state.DataUploader
    if st.session_state.selected_node == 'Upload Data':
        data_manager.upload_tabular_data()
    data_manager.upload_document_files()
    
    return None


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
    This function is responsible for running the necessary code at the top of the app.
    
    Steps:
    1. Add all default session states using the `session_state_management.main()` function.
    2. Set or get the LLM keys using the `set_or_get_llm_keys()` function.
    3. Instantiate the `Extractors` class and add it to the session state if it doesn't already exist.
    4. If the selected node in the session state is 'logout', call the `logout()` function.
    5. Set the availability of function calling using the `set_function_calling_availability()` function.
    6. If 'upgrade' is not in the session state, call the `temp_upgrade()` function and set `st.session_state.upgrade` to True.
    
    Returns:
    None
    """
    # Add all default session states
    session_state_management.main()
    if 'llm_configurator' not in st.session_state:
        st.session_state.llm_configurator = LLMConfigurator()
    lc = st.session_state.llm_configurator
    lc.set_or_get_llm_keys()
    
    # Instantiate the Extractors class and add it to the session state
    if 'extractor' not in st.session_state:
        st.session_state.extractor = Extractors()
    
    if st.session_state.selected_node == 'logout':
        logout()
    # create_user_folder()
    set_function_calling_availability()
    if 'upgrade' not in st.session_state:
        temp_upgrade()
        st.session_state.upgrade = True
    return None
    
def temp_upgrade():
    """
    Use this for upgrades
    """
    user_folder = st.session_state.user_folder
    if user_folder.endswith(os.path.sep):
        user_folder = user_folder[:-1]

    projects = glob(os.path.join(user_folder, '**', ''))
     
    for project in projects:
        project_research_file = os.path.join(project, 'research_projects_with_llm.parquet')
        if not os.path.exists(project_research_file):
            create_research_data_file(project)
        else:
            df = pd.read_parquet(project_research_file)
            if 'research_name' not in df.columns:
                create_research_data_file(project)
        

    return None

def x(arr):
    file, col = arr
    file = os.path.basename(file).replace('.parquet', '').replace('_', ' ').title()
    col = col.replace('llm_', '').replace('_', ' ').upper()
    return f"{col} {file}"

def sys_ins_get(row):
    col, file = row
    file = os.path.basename(file).replace('.parquet', '')
    project = os.path.join(*file.split(os.path.sep)[1:-1])
    sys_ins = f"{project}{file}_{col}_sys_ins.txt"
    
    if os.path.exists(sys_ins):
        with open(sys_ins, 'r') as f:
            text = f.read()
    else:
        text = ''
    
    return text

def sys_ins_get(row):
    col, file = row
    file_name = os.path.basename(file)
    file_name_without_extension = os.path.splitext(file_name)[0]
    project_path = os.path.dirname(file_name_without_extension)
    sys_ins = os.path.normpath(os.path.join(project_path, f"{file_name_without_extension}_{col}_sys_ins.txt"))

    if os.path.exists(sys_ins):
        with open(sys_ins, 'r') as f:
            text = f.read()
    else:
        text = ''
    return text


def create_research_data_file(project):
    """
    Create a data model if it does not exist.  Temp upgrade from 0.0.22 to 0.0.23
    """

    data_model = os.path.join(project, 'data_model.parquet')
    
    st.sidebar.warning(f"No data model for {project}")
    if not os.path.exists(data_model):
        return None
    df = pd.read_parquet(data_model)
    
    res_projects = df[df.column_name.str.contains('llm')][['column_name', 'file_name']]
        
    if len(res_projects) == 0:
        res_projects = pd.DataFrame(columns=['research_name', 'project_name', 'file_name', 'input_col', 'output_col', 'word_limit', 'row_by_row', 'system_instruction'])
    else:
        res_projects = res_projects.rename(columns={'column_name': 'output_col'})
        
        res_projects['input_col'] = 'SELECT'
        
        res_projects['research_name'] = res_projects[['file_name', 'output_col']].apply(x, axis=1)

        res_projects['project_name'] = project
        st.sidebar.warning(project)
        res_projects = res_projects.reset_index(drop=True)
        
        res_projects['word_limit'] = 1000

        res_projects['system_instruction'] = ''
        
        res_projects.loc[res_projects.input_col.str.contains('conso'), 'row_by_row'] = True
        
        res_projects.row_by_row = res_projects.row_by_row.fillna(False)
        
        res_projects = res_projects[['project_name', 'research_name', 'file_name', 'input_col', 'output_col', 'word_limit', 'row_by_row', 'system_instruction']]
    
        res_projects['system_instruction'] = res_projects[['output_col', 'file_name']].apply(sys_ins_get, axis=1)
    
    project_research_file = f"{project}research_projects_with_llm.parquet"    
    res_projects.to_parquet(project_research_file, index=False)
    
    return None