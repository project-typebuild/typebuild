import os
import time
import pandas as pd
import streamlit as st
from home_page import what_can_you_do
from session_state_management import change_ss_for_project_change
from project_management.create_new_project import ProjectCreator

# TODO: See where to invoke from.  Add to menu.
class ProjectManagement:
    def __init__(self, user_folder):
        self.user_folder = user_folder
        self.project_folder = None
        self.selected_project = None

    def list_projects_in_user_folder(self):
        """
        Lists project directories in the given user folder.
        
        Returns:
        - project_names (list): List of project directory names.
        """
        try:
            project_names = [i for i in os.listdir(self.user_folder) if os.path.isdir(os.path.join(self.user_folder, i))]
        except FileNotFoundError:
            project_names = []
        return project_names

    def create_user_folder_if_not_exists(self):
        """
        Creates a user folder if it does not exist.
        """
        os.makedirs(self.user_folder, exist_ok=True)

    def filter_project_names(self, project_names):
        """
        Filters out unwanted directory names from the project names list.
        
        Returns:
        - filtered_project_names (list): Filtered list of project directory names.
        """
        project_names = [i for i in project_names if not 'pycache' in i and not i.startswith('.')]
        project_names.append('Create new project')
        return project_names

    def select_project(self, project_names, default_index=0):
        """
        Handles the selection of a project from the project names list.
        
        Returns:
        - selected_project (str): The name of the selected project.
        """
        if self.selected_project is None:
            default_index = 0
        else:
            default_index = project_names.index(self.selected_project)
        
        selected_project = st.selectbox('Select a project', project_names, index=default_index)
        if selected_project == 'Create new project':
            pc = ProjectCreator()
            new_project = pc.create_new_project()
            self.selected_project = new_project
            st.success(f'Created project {new_project}.  Taking you there...')
            time.sleep(2)
            st.rerun()
        else:
            if st.button("Select the project"):
                self.selected_project = selected_project
                self.project_folder = os.path.join(self.user_folder, selected_project)
                change_ss_for_project_change()
                with st.spinner("Selected project"):
                    st.success("You can use it now...")
                    time.sleep(2)
                    st.session_state.activeStep = 'HOME'
                    st.rerun()

        return None


    def get_project_file_folder(self):
        """
        Main function to manage project files in the user's directory.
        """
        project_names = self.list_projects_in_user_folder()

        if not project_names:
            self.create_user_folder_if_not_exists()
            project_names = self.list_projects_in_user_folder()

        project_names = self.filter_project_names(project_names)
        self.select_project(project_names)

        if self.selected_project == 'Create new project':
            cnp = ProjectCreator(self.user_folder)
            cnp.create_new_project()
            st.stop()

        # Additional logic for handling project selection and session state update...
        return None

    def manage_project(self):
        """
        Manages project files in the user's directory by calling relevant functions
        in the correct sequence.
        """
        # Create user folder if it does not exist
        self.create_user_folder_if_not_exists()

        # List projects in the user folder
        project_names = self.list_projects_in_user_folder()

        # Filter and manage project names
        project_names = self.filter_project_names(project_names)

        # Select a project
        self.select_project(project_names)

        

        # Additional logic for handling project selection and session state update...
        return None


    def add_data_model_to_session_state(self):
        """
        Adds the data model to the session state.
        """
        # Get the project folder
        project_folder = self.project_folder
        # If the file called data_model.parquet is missing, toggle the manage project button
        data_model_file = os.path.join(project_folder, 'data_model.parquet')
        if os.path.exists(data_model_file):
            # Add data description to session state
            st.session_state.data_description = pd.read_parquet(data_model_file).to_markdown(index=False)
        return None

    def project_settings(self):
        """
        This function allows the user to manage key aspects of the selected project:
        - Manage data
        - Set / edit project description
        """    
        self.add_data_model_to_session_state()
