import os
import time
import streamlit as st
from home_page import what_can_you_do

from session_state_management import change_ss_for_project_change


def get_project_file_folder():
    """
    Returns the path to the project folder for the current user.
    Projects are folders within the user's folder.
    Project file is the path to the main.py file.
    
    Args:
    - None
    
    Returns:
    - project_file (str): The path to the project file.
    """
    user_folder = st.session_state.user_folder 
    # Get just the directory names, ignore the files
    try:
        project_names = [i for i in os.listdir(user_folder) if os.path.isdir(os.path.join(user_folder, i))]
    except FileNotFoundError as e:
        # Create the folder
        os.makedirs(user_folder)
        project_names = []

    # Ignore pycache
    project_names = [i for i in project_names if not 'pycache' in i]
    # Project names does not start in '.'
    project_names = [i for i in project_names if not i.startswith('.')]
    # Add new create project option
    project_names.append('Create new project')
    # Make the first project the default

    default_index = 0

    # If no project is selected, select the first project
    if 'selected_project' not in st.session_state:
        st.session_state.selected_project = project_names[default_index]
    
    # Project names in menu have "~" in them.
    if "~" in st.session_state.new_menu:
        selected_project = st.session_state.new_menu.split("~")[1]
        # If it is different from the current project, change the project
        # and change session state
        if selected_project != st.session_state.selected_project:
            st.session_state.selected_project = selected_project
            change_ss_for_project_change()
        if selected_project != 'Create new project':
            project_name = selected_project.replace('_', ' ').upper() + ' PROJECT'
            st.header(project_name, divider='rainbow')
            st.info(f"Please go to 'Functionalities' in the menu above and select what you want to do next.  Your options are given below.")
            what_can_you_do()    
    selected_project = st.session_state.selected_project
    if selected_project == 'Create new project':
        create_new_project()        
        st.stop()
    
    project_folder = os.path.join(st.session_state.user_folder, selected_project)
    # Save to session state
    st.session_state.project_folder = project_folder
    
    return None

def create_new_project():
    """
    Creates a new project folder, main.py file, and __init__.py file.
    TODO: Need to call this somewhere.
    """
    # Get the project name
    project_name = st.text_input("Enter the project name")
    if project_name == '':
        st.warning('Enter a project name')
        st.stop()
    # Lower case and replace spaces with underscores
    project_name = project_name.lower().replace(' ', '_')
    # Check if the project name already exists
    # token_name = st.session_state.token
    # user_folder = os.path.join('users', token_name)

    # Create the path to the .typebuild directory
    user_folder = st.session_state.user_folder  
    
    # Check if the directory exists
    if not os.path.exists(user_folder):
        # Create the directory if it doesn't exist
        os.makedirs(user_folder)

    # Project folder is project name inside the user folder
    project_folder = os.path.join(user_folder, project_name)

    if os.path.exists(project_folder):
        st.write('Project already exists, please rename')
        st.stop()
    st.session_state.project_folder = project_folder
    # Create the project folder
    if not os.path.exists(project_folder):
        os.makedirs(project_folder)
    data_folder = os.path.join(project_folder, 'data')
    views_folder = os.path.join(project_folder, 'views')
    project_settings_folder = os.path.join(project_folder, 'project_settings')

    # Create these folders if they do not exist
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    if not os.path.exists(views_folder):
        os.makedirs(views_folder)
    if not os.path.exists(project_settings_folder):
            os.makedirs(project_settings_folder)

    # Create the __init__.py file
    init_file = os.path.join(project_folder, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('')
        st.success("Created the project.  Taking you to it now...")
        # Save to session state
        st.session_state.project_folder = project_folder
        # Increment session number
        st.session_state.ss_num += 1
        st.session_state[f'selected_project_{st.session_state.ss_num}'] = project_name
        st.session_state.selected_project = project_name
        time.sleep(2)
        # Take user to project settings
        # TODO: ADD THIS WITH THE NEW MENU SYSTEM.
    return None

# break this down into multiple functions for the menu.
def project_settings():
    """
    This function allows the user to manage key aspects of the selected project:
    - Manage data
    - Set / edit project description
    """    
    
    # Get the project folder
    project_folder = st.session_state.project_folder
    # If the file called data_model.parquet is missing, toggle the manage project button
    data_model_file = os.path.join(project_folder, 'data_model.parquet')
    if os.path.exists(data_model_file):
        # Add data description to session state
        st.session_state.data_description = pd.read_parquet(data_model_file).to_markdown(index=False)
    

    options = [
        'Upload your data',
        'Fetch data',
    ]


    default_index = 0

    selected_option = st.radio(
        "Select an option", 
        options, 
        captions=["CSV, XLSX, TXT, VTT, etc.", "YouTube, Google Search"],
        horizontal=True, 
        index=default_index
        )
    st.markdown("---")
    if selected_option == 'Upload your data':
        file_upload_and_save()
        get_data_model()
        st.stop()

    if selected_option == 'Fetch data':
        if st.checkbox("Get data from YouTube"):
            from tools.yt_search import main as yt_search
            yt_search()
            st.warning("Uncheck get data from YouTube to go to project settings")
        if st.checkbox("Get data from Google"):
            from tools.google_search import main as google_search
            google_search()
            st.warning("Uncheck get data from Google to go to project settings")
        st.stop()

    if selected_option == 'Project description (optional)':
        ideate_project()
        st.stop()
    
    return None

# TODO: Move to a separate file
def ideate_project():
    """
    This stores the user requirement for the given view,
    based on the selected menu. 
    """
    file_path = os.path.join(st.session_state.project_folder, 'project_settings', 'project_description.txt')
    key = 'Project Description'
    widget_label = 'Project Description'
    st.subheader('Ideate')
    project_description = text_areas(file=file_path, key=key, widget_label=widget_label)
    # Save to session state
    st.session_state.project_description = project_description

    ideation_chat()
    return None


def ideation_chat():
    """
    A chat on the project description.
    That could be exported to the project description file.
    """
    # If there is no project description chat in the session state, create one
    if 'ideation_chat' not in st.session_state:
        st.session_state.ideation_chat = []
    
    chat_container = st.container()
    prompt = st.chat_input("Enter your message", key='project_description_chat_input')
    if prompt:
        # Create the messages from the prompts file
        prompts.blueprint_prompt_structure(prompt=prompt)
        with st.spinner('Generating response...'):
            res = get_llm_output(
                st.session_state.ideation_chat, 
                model='gpt-3.5-turbo-16k'
                )
            # Add the response to the chat
            st.session_state.ideation_chat.append({'role': 'assistant', 'content': res})
    
    # Display the user and assistant messages
    with chat_container:
        for msg in st.session_state.ideation_chat:
            if msg['role'] in ['user', 'assistant']:
                with st.chat_message(msg['role']):
                    st.markdown(msg['content'])

    return None

# TODO: Move to a separate file
def set_user_requirements():
    """
    This stores the user requirement for the given view,
    based on the selected menu. 
    """
    file_path = os.path.join(st.session_state.project_folder, 'project_settings', 'user_requirements.txt')
    key = 'User Requirements'
    widget_label = 'User Requirements'
    st.subheader('User requirements')
    user_requirements = text_areas(file=file_path, key=key, widget_label=widget_label)
    # Save to session state
    st.session_state.user_requirements = user_requirements

    user_requirements_chat()
    st.stop()
    return None

def user_requirements_chat():

    """
    A chat on the user requirements.
    That could be exported to the user requirements file.
    """
    # If there is no user requirements chat in the session state, create one
    if 'user_requirements_chat' not in st.session_state:
        st.session_state.user_requirements_chat = []
    
    chat_container = st.container()
    prompt = st.chat_input("Enter your message", key='user_requirements_chat_input')
    if prompt:
        # Create the messages from the prompts file
        prompts.blueprint_prompt_structure(prompt=prompt)
        with st.spinner('Generating response...'):
            res = get_llm_output(st.session_state.user_requirements_chat, model='gpt-3.5-turbo-16k')
            # Add the response to the chat
            st.session_state.user_requirements_chat.append({'role': 'assistant', 'content': res})
    
    # Display the user and assistant messages
    with chat_container:
        for msg in st.session_state.user_requirements_chat:
            if msg['role'] in ['user', 'assistant']:
                with st.chat_message(msg['role']):
                    st.markdown(msg['content'])

    return None


