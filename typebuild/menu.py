import os
import streamlit as st
import hydralit_components as hc
import pickle as pk

def get_menu_data():
    """
    Creates a the data for a hydralit menu.
    The menu element is a dictionary with the following keys:
    - id: the id of the menu item
    - icon: the icon of the menu item, based on emojis
    - label: the label of the menu item
    - ttip: the tooltip of the menu item
    - submenu: the submenu of the menu item (optional)
    """
    # Close menu object to be used in dropdown menus
    close_menu = {'id':'close','icon': "fa fa-window-close", 'label':"Close menu"}
    
    # A container for the menu data
    menu_data = []

    # List of available projects
    # Get the user folder from the session state
    if 'user_folder' not in st.session_state:
        home_dir = os.path.expanduser("~")
        st.session_state.user_folder = os.path.join(home_dir, ".typebuild", 'users' ,st.session_state.token)
        
    user_folder = st.session_state.user_folder
    # If the user folder does not exist, create it
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    

    # Get just the directory names, ignore the files
    project_names = [i for i in os.listdir(user_folder) if os.path.isdir(os.path.join(user_folder, i))]


    # Ignore pycache
    project_names = [i for i in project_names if not 'pycache' in i]
    # Project names does not start in '.'
    project_names = [i for i in project_names if not i.startswith('.')]
    # Add new create project option
    project_names.append('Create new project')

    project_menu = {
        "id": "project_menu",
        "icon": "🗂️",
        "label": "Projects",
        "ttip": "Select project or create new",
        "submenu": [{"label": i, "id": f"project~{i}"} for i in project_names],
    }

    # Add the close menu option to project submenu
    project_menu['submenu'].append(close_menu)

    # Add the project menu to the menu data
    menu_data.append(project_menu)

    # Logout
    logout = {'id':'logout', 'icon': "🚪", 'label':"Logout"}
    
    
    developer_options = {"label": "Toggle developer options", "id": "toggle_developer_options", "icon": "🛠️"}
    function_calling_mode = {"label": "Toggle function calling mode", "id": "toggle_function_calling_mode", "icon": "🛠️"}
    
    settings = {
        'id': 'settings',
        'icon': "⚙️",
        'label': "Settings",
        'ttip': "Adding openai key, upload custom llm",
        'submenu': [
            {"label": "LLM Access", "id": "llm_access"},
            developer_options,
            function_calling_mode,
            logout,
            close_menu
        ]
    }
    data = {
        "id": "data",
        "icon": "📊",
        "label": "Data",
        "ttip": "Upload or import data",
    }

    ideate = {
        "id": "ideate",
        "icon": "🧠",
        "label": "Ideate",
        "ttip": "Ideate",
    }

    apps_analysis = {
        "id": "apps_analysis",
        "icon": "💻",
        "label": "Apps & analysis",
        "ttip": "Forms, mini-apps, data analysis",
    }
    llm_analysis = {
        "id": "llm_analysis",
        "icon": "🤖",
        "label": "LLM Analysis",
        "ttip": "Analyze data with LLM",
    }

    research = {
        "id": "research",
        "icon": "🔍",
        "label": "Research",
        "ttip": "Research",
    }

    functionalities = {
        "id": "functionalities",
        "icon": "📌",
        "label": "Functionalities",
        "ttip": "Add functionalities",
        "submenu": [
            data,
            ideate,
            apps_analysis,
            llm_analysis,
            research,
        ],
    }


    menu_data.append(functionalities)
    menu_data.append(settings)

    if 'user_type' not in st.session_state:
        st.session_state.user_type = 'developer'

    return menu_data

def get_theme():
    return {
    'txc_inactive': '#FFFFFF',
    'menu_background':'purple',
    'txc_active':'purple',
    'option_active':'white'
    }


def get_menu():
    if 'old_menu' not in st.session_state:
        st.session_state['old_menu'] = None
    
    if 'new_menu' not in st.session_state:
        st.session_state['new_menu'] = None

    new_menu = hc.nav_bar(
        menu_definition=get_menu_data(),
        home_name='Home',
        sticky_mode = 'sticky',
        sticky_nav=False,
        hide_streamlit_markers=False,
        override_theme=get_theme(),
        key = f"nav_bar_{st.session_state.menu_id}"
    )
    
    st.session_state.new_menu = new_menu

    return None

def reset_menu(save_header_state=True, new_menu=None):
    st.session_state['old_menu'] = st.session_state.new_menu
    st.session_state.new_menu = new_menu
    st.session_state.menu_id += 1
    rerun_app(save_header_state)
    return None

def rerun_app(save_header_state=True):
    if save_header_state:
        save_the_header_state()
        st.session_state.reset_session_state = True
    st.rerun()
    return None

def save_the_header_state():
    header_states = {k:st.session_state[k] for k in st.session_state if 'mytags_' in k}
    # Create the folder if it does not exist
    if not os.path.exists('session_states'):
        os.makedirs('session_states')
    # First save the key session states
    with open(os.path.join('session_states', f'{st.session_state.token}.pk'), 'wb') as f:
        pk.dump(header_states, f)
    return None

def load_header_states():
    """
    Load the header states and add them to session state
    if variables do not exist
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file = os.path.join(dir_path, 'session_states', f'{st.session_state.token}.pk')

    if os.path.exists(file):
        with open(file, 'rb') as f:
            header_states = pk.load(f)
        for key in header_states:
            if key not in st.session_state:
                st.session_state[key] = header_states[key]
    return None