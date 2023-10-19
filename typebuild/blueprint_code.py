"""
Blueprints consist of text and code.  
This file deals with all aspects of code including:

- Generating code from user requirements text
- Modifying code based on requested changes
- Maintaining relationship between code and blueprint text (so that if one is updated, we will know to update the other)
- etc.

blueprint_text.py only deals with creating, editing, and deleting text.  It does not deal with code.
"""

import os
import time
import pandas as pd
import streamlit as st
import session_state_management
session_state_management.main()

import sys
dir_path = os.path.dirname(os.path.realpath(__file__))
plugins_path = os.path.join(dir_path, 'plugins')
sys.path.append(plugins_path)

# Import the plugins
from data_widgets import display_editable_data


# Create a menu to run the app
# create_run_menu()


def select_view():
    """
    Let the user select the view
    """
    #----LET THE USER SELECT THE VIEW TO RUN----

    # Get the file names from the directory
    dir = os.path.join(st.session_state.project_folder, 'views')
    
    # Create directory if it doesn't exist
    if not os.path.exists(dir):
        os.makedirs(dir)
    file_names = os.listdir(dir)
    
    # Ignore files that start with __
    file_names = [i for i in file_names if not i.startswith('__')]
    # Read only files that end with .py
    file_names = [i for i in file_names if i.endswith('.txt')]
    # Remove the .py extension
    file_names = [i.replace('.txt', '') for i in file_names]
    file_names.append('Create new view')
    
    # Create a view number if it doesn't exist
    if 'view_num' not in st.session_state:
        st.session_state.view_num = 0
    # Create a selectbox to select the file
    selected_file = st.sidebar.selectbox(
        label='Views you created', 
        options=file_names, 
        key=f'selected_file_{st.session_state.view_num}', 
        on_change=session_state_management.change_view,
        help="These are the views you created.  Select one to run it.  You can also create a new view."
        )
    
    # Set the file path to the session state
    file_path = os.path.join(dir, selected_file)
    st.session_state.file_path = file_path
    st.session_state.selected_view = selected_file
    
    
    #--------GET A VIEW NAME FOR NEW VIEWS--------
    if selected_file == 'Create new view':
        new_view_name = st.text_input(
            'Enter the name of the new view', 
            key='new_view_name',
            help="Give the chart, table or any analysis you are doing with data a name."
            )
        if not new_view_name:
            st.error('Enter a name for the new view.  You can use this to find your report later in the dropdown on your left.')
            st.stop()
        selected_file = new_view_name.lower().replace(' ', '_')
        st.session_state.selected_view = selected_file
        file_path = os.path.join(dir, selected_file)
        # Save it to the session state
        st.session_state.file_path = file_path
        st.info("If you like the name for this view, save it.  We can then define the requirements and write the code.")
        
        if st.button("Use this name"):
            # Save the view file
            txt_file_name = file_path + '.txt'
            with open(txt_file_name, 'w') as f:
                f.write(f'FUNCTIONAL REQUIREMENT: {new_view_name}\n')
            st.success(f'View name saved as {new_view_name}')
            time.sleep(1)
            st.session_state.view_num += 1
            # Set the view name to the newly created view
            st.session_state[f'selected_file_{st.session_state.view_num}'] = selected_file

            st.rerun()
        st.stop()
    else:
        if st.sidebar.checkbox("Delete selected view", key=f"delete_selected_view_{st.session_state.selected_view}"):
            delete_selected_view()
            st.stop()
        select_data()
        # Show the requirements, if user wants to see it
        if st.sidebar.checkbox("View requirements"):
            # Show the requirements using text area
            txt_file = file_path + '.txt'
            with open(txt_file, 'r') as f:
                requirements = f.read()
            st.sidebar.warning(requirements)    
    return None

def delete_selected_view():
    """
    Delete the requirement
    """
    # Add a warning
    st.sidebar.warning("Are you sure you want to delete this view?  This action cannot be undone.")
    project_folder = st.session_state.project_folder
    selected_view = st.session_state.selected_view
    views_folder = os.path.join(project_folder, 'views')
    view_file = os.path.join(views_folder, selected_view + '.txt')
    py_file = os.path.join(views_folder, selected_view + '.py')
    pkl_file = os.path.join(views_folder, selected_view + '_meta.pkl')
    if st.sidebar.button("Delete"):
        if os.path.exists(view_file):
            os.remove(view_file)
            st.success(f"View {selected_view} deleted!")
        # Remove the py file
        if os.path.exists(py_file):
            os.remove(py_file)
        # Remove the pkl file
        if os.path.exists(pkl_file):
            os.remove(pkl_file)
        # Also remove chat_key
        chat_key = st.session_state.chat_key
        del st.session_state[chat_key]
        st.sidebar.warning("View deleted!")
        time.sleep(1)
        st.rerun()

    return None

def save_selected_data():
    """
    On change, save the selected data to the view meta file
    """
    project_folder = st.session_state.project_folder
    selected_view = st.session_state.selected_view
    views_folder = os.path.join(project_folder, 'views')
    key = f"selected_tables_{selected_view}"
    selected_data = st.session_state[key]
    view_meta_file = os.path.join(views_folder, selected_view + '_meta.pkl')
    # Open the view meta file to read the data
    if os.path.exists(view_meta_file):
        with open(view_meta_file, 'rb') as f:
            view_meta = pd.read_pickle(f)
    else:
        view_meta = {}


    view_meta['selected_data'] = selected_data
    with open(view_meta_file, 'wb') as f:
        pd.to_pickle(view_meta, f)
    return None


def select_data():
    """
    If there are more than three tables, the data models gets large,
    and we hit context limits often.  So, we will ask the user to select
    relevant tables.  
    
    TODO: we should have a special agent that can
    do the selection for us.
    """
    project_folder = st.session_state.project_folder
    selected_view = st.session_state.selected_view
    data_description_for_view = f"data_description_{selected_view}"
    views_folder = os.path.join(project_folder, 'views')
    key = f"selected_tables_{selected_view}"
    # Check if there is a pickle file for the selected view
    # called view meta
    view_meta_file = os.path.join(views_folder, selected_view + '_meta.pkl')
    # Define the data folder
    data_folder = os.path.join(project_folder, 'data')

    # Get a list of all data files in the data folder
    data_files = [f for f in os.listdir(data_folder) if f.endswith('.parquet')]

    # If the selected data is not in the session state,
    # then get the default value for the widget
    if key not in st.session_state:
        if os.path.exists(view_meta_file):
            # Load the pickle file
            with open(view_meta_file, 'rb') as f:
                view_meta = pd.read_pickle(f)
            default = view_meta.get('selected_data', [])
        elif len(data_files) == 0:
            st.warning("There are no data files in the data folder.  Please add data files.")
            st.stop()
        # If there is just one file, show it without selection
        elif len(data_files) < 4:
            default = data_files

        else:
            default = []
        
        st.session_state[key] = default

    # Allow the user to select multiple data files
    selected_files = st.multiselect(
        'Select data files', 
        data_files, 
        key=key, 
        on_change=save_selected_data
        )

    if not selected_files:
        st.error("Please select at least one data file that you will use for analysis.")
        st.session_state[data_description_for_view] = None
    else:
        data_model_file = os.path.join(project_folder, 'data_model.parquet')
        data_description = pd.read_parquet(data_model_file)
        # Get the description of the selected files
        # Add data directory to the file names
        selected_files = [os.path.join(data_folder, i) for i in selected_files]
        selected_description = data_description[data_description['file_name'].isin(selected_files)].to_markdown()

        st.session_state[data_description_for_view] = selected_description

        if st.checkbox("Show sample data"):
            # Show a sample of 5 rows for each selected file
            for file in selected_files:
                file_path = os.path.join(data_folder, file)
                df = pd.read_parquet(file_path)
                st.write(f'Sample data from {file}:')
                st.dataframe(df.head(5))

    return None

