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
sys.path.append(dir_path + '/plugins')

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
    dir = st.session_state.project_folder + '/views'
    
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
    if st.checkbox("View sample data"):
        show_sample_data()
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
        # Show the requirements, if user wants to see it
        if st.sidebar.checkbox("View requirements"):
            # Show the requirements using text area
            txt_file = file_path + '.txt'
            with open(txt_file, 'r') as f:
                requirements = f.read()
            st.sidebar.warning(requirements)    
    return None

def show_sample_data():
    """
    This function allows the user to select multiple data files from a data folder and shows
    a sample of 5 rows for each selected file.
    """
    # Define the data folder
    data_folder = st.session_state.project_folder + '/data'

    # Get a list of all data files in the data folder
    data_files = [f for f in os.listdir(data_folder) if f.endswith('.parquet')]

    if len(data_files) == 0:
        st.warning("There are no data files in the data folder.  Please add data files.")
        st.stop()
    # If there is just one file, show it without selection
    elif len(data_files) == 1:
        file_path = os.path.join(data_folder, data_files[0])
        df = pd.read_parquet(file_path)
        st.write(f'Sample data from {data_files[0]}:')
        st.dataframe(df.head(5))

    else:
        # Allow the user to select multiple data files
        selected_files = st.multiselect('Select data files', data_files)

        # Show a sample of 5 rows for each selected file
        for file in selected_files:
            file_path = os.path.join(data_folder, file)
            df = pd.read_parquet(file_path)
            st.write(f'Sample data from {file}:')
            st.dataframe(df.head(5))