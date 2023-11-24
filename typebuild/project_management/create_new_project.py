import streamlit as st
import os
import streamlit as st
import os


class ProjectCreator:
    def __init__(self):
        self.user_folder = st.session_state.user_folder

    def get_project_name(self):
        """
        Gets the project name from user input.

        Returns:
        - project_name (str): The entered project name.
        """
        project_name = st.text_input("Enter the project name")
        if project_name == '':
            st.warning('Enter a project name')
            st.stop()
        return project_name.lower().replace(' ', '_')

    def create_folder_if_not_exists(self, folder_path):
        """
        Creates a folder if it does not exist.

        Args:
        - folder_path (str): Path of the folder to be created.

        Returns:
        - None
        """
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    def create_subfolders(self, project_folder):
        """
        Creates subfolders within the project folder.

        Args:
        - project_folder (str): Path to the project folder.

        Returns:
        - None
        """
        subfolders = ['data', 'views', 'project_settings']
        for folder in subfolders:
            self.create_folder_if_not_exists(os.path.join(project_folder, folder))

    def create_init_file(self, project_folder):
        """
        Creates an __init__.py file in the project folder.

        Args:
        - project_folder (str): Path to the project folder.

        Returns:
        - None
        """
        init_file = os.path.join(project_folder, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('')

    
    def create_new_project(self):
        """
        Creates a new project folder, main.py file, and __init__.py file.
        """
        project_name = self.get_project_name()

        # Create user folder if it doesn't exist
        self.create_folder_if_not_exists(self.user_folder)

        # Create project folder
        project_folder = os.path.join(self.user_folder, project_name)
        if os.path.exists(project_folder):
            st.write('Project already exists, please rename')
            st.stop()
        self.create_folder_if_not_exists(project_folder)

        # Create subfolders and __init__.py file
        self.create_subfolders(project_folder)
        self.create_init_file(project_folder)

        # Update session state and redirect
        st.session_state.project_folder = project_folder

        return project_name

