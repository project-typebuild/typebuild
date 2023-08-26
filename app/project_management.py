"""
Create projects, upload files, fetch file names in the project
and other aspects of understanding and manageing assets in the project folder
"""

from glob import glob
import os
from session_state_management import change_project
import streamlit as st
import pandas as pd

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
    token_name = st.session_state.token
    user_folder = os.path.join('users', token_name)
    # Get just the directory names, ignore the files
    try:
        project_names = [i for i in os.listdir(user_folder) if os.path.isdir(os.path.join(user_folder, i))]
    except FileNotFoundError as e:
        # Create the folder
        os.makedirs(user_folder)
        project_names = []

    # Ignore pycache
    project_names = [i for i in project_names if not 'pycache' in i]
    # Add new create project option
    project_names.append('Create new project')
    # Make the first project the default

    default_index = 0
    selected_project = st.sidebar.selectbox(
        "Select project", 
        project_names, 
        index=default_index,
        key='selected_project',
        on_change=change_project
        )
    if selected_project == 'Create new project':
        create_new_project()
        st.stop()
        
    project_folder = os.path.join(user_folder, selected_project)

    # Save to session state
    st.session_state.project_folder = project_folder

    # # Get the project file path
    # project_main_file = os.path.join(project_folder, 'main.py')
    # # Create the file if it does not exist
    # create_main_file_if_not_exists(project_main_file)
    # # Save to session state
    # st.session_state.project_main_file = project_main_file

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
    token_name = st.session_state.token
    user_folder = os.path.join('users', token_name)

    # Create the user folder if it does not exist
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    
    project_folder = os.path.join(user_folder, project_name)
    if os.path.exists(project_folder):
        st.write('Project already exists, please rename')
        st.stop()

    # Create the project folder
    project_folder = os.path.join(user_folder, project_name)
    if not os.path.exists(project_folder):
        os.makedirs(project_folder)
    
    # Create the __init__.py file
    init_file = os.path.join(project_folder, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('')
    # Save to session state
    st.session_state.project_folder = project_folder
    # st.session_state.project_main_file = project_main_file
    return None


def get_project_df():

    """

    This function gets the project dataframe from the project folder.

    """

    files = glob(f'{st.session_state.project_folder}/*.csv')

    if files:
        df = pd.read_csv(files[0])
        st.session_state.df = df
    else:
        st.session_state.df = None

def file_upload_and_save():
    """
    This function allows the user to upload a file and save it to the current folder. 
    It also allows the user to process the data and save it to a new file.
    You can upload a CSV or JSON file.

    TODO: Add support for other file types: Parquet, Excel, etc.

    """

    # Create a file uploader
    uploaded_file = st.sidebar.file_uploader("Choose a CSV or a JSON file")

    # Check if a file was uploaded
    if uploaded_file is not None:
        # Get the file name
        file_name = uploaded_file.name

        file_path = os.path.join(st.session_state.project_folder, file_name)
        # Save the file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Display a success message
        st.success(f"File '{file_name}' uploaded and saved successfully!")

        # Check if the uploaded file is a CSV file
        if file_name.endswith('.csv'):
            # Load the CSV file into a pandas DataFrame
            df = pd.read_csv(file_path)

            # Do some data processing here...

            # Save the processed data to a new CSV file
            df.to_csv(file_path, index=False)

            # Display a success message
            st.success(f"Processed data saved to '{file_name}' successfully!")
        
        # Check if the uploaded file is a JSON file
        elif file_name.endswith('.json'):
            # Load the JSON file into a pandas DataFrame
            df = pd.read_json(file_path)

            # Do some data processing here...

            # Save the processed data to a new JSON file
            df.to_json(file_path)

            # Display a success message
            st.success(f"Processed data saved to '{file_name}' successfully!")

        # Check if the uploaded file is a Parquet file
        elif file_name.endswith('.parquet'):
            # Load the Parquet file into a pandas DataFrame
            df = pd.read_parquet(file_path)

            # Do some data processing here...

            # Save the processed data to a new Parquet file
            df.to_parquet(file_path)

            # Display a success message
            st.success(f"Processed data saved to '{file_name}' successfully!")

        # Check if the uploaded file is an Excel file
        elif file_name.endswith('.xlsx'):
            # Load the Excel file into a pandas DataFrame
            df = pd.read_excel(file_path)

            # Do some data processing here...

            # Save the processed data to a new Excel file
            df.to_excel(file_path)

            # Display a success message
            st.success(f"Processed data saved to '{file_name}' successfully!")

        # Check if the uploaded file is a Pickle file
        elif file_name.endswith('.pkl'):
            # Load the Pickle file into a pandas DataFrame
            df = pd.read_pickle(file_path)

            # Do some data processing here...

            # Save the processed data to a new Pickle file
            df.to_pickle(file_path)

            # Display a success message
            st.success(f"Processed data saved to '{file_name}' successfully!")
        st.session_state['file_uploaded'] = True
    return None