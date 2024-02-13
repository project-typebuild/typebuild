import tempfile
import openai
import anthropic
import streamlit as st
import os
import toml
import time
from upload_custom_llm import upload_custom_llm_file

class LLMConfigurator():
    def __init__(self):
        self.user_folder = st.session_state.user_folder
        self.secrets_file_path = os.path.join(self.user_folder, 'secrets.toml')
        self.ensure_secrets_file_exists()
        self.load_config()

    def ensure_secrets_file_exists(self):
        if not os.path.exists(self.secrets_file_path):
            with open(self.secrets_file_path, 'w') as f:
                f.write('')
        return None

    def load_config(self):
        with open(self.secrets_file_path, 'r') as f:
            config = toml.load(f)
            st.session_state.config = config

    def set_or_get_llm_keys(self):
        api_key = st.session_state.config.get('openai', {}).get('key', '')
        claude_key = st.session_state.config.get('claude', {}).get('key', '')
        if api_key:
            st.session_state.openai_key = api_key
        if claude_key:
            st.session_state.claude_key = claude_key
        return None

    def config_project(self):
        self.load_config()
        self.set_or_get_llm_keys()
        default_index = 0
        
        # Check if the user has a custom_llm.py file in the typebuild_root folder
        if os.path.exists(os.path.join(st.session_state.typebuild_root, 'custom_llm.py')):
            default_index = 1

        llm_selection = st.radio(
            'Select an option',
            ['Set LLM API key', 'Upload Custom LLM'],
            captions=["Set keys for OpenAI or Anthropic", "Access other LLMs"],
            horizontal=True,
            index=default_index
        )

        if llm_selection == 'Upload Custom LLM':
            upload_custom_llm_file()
            st.stop()
        else:
            self.update_llm_keys()

    def update_llm_keys(self):
        api_key = st.text_input(
            'Enter OpenAI key',
            value=st.session_state.config.get('openai', {}).get('key', '')
        )
        claude_key = st.text_input(
            'Enter Claude key',
            value=st.session_state.config.get('claude', {}).get('key', '')
        )
        function_call_availabilty = st.checkbox(
            "(Expert setting) I have access to function calling",
            value=st.session_state.config.get('function_call_availabilty', True),
            help="Do you have access to openai models ending in 0613? they have a feature called function calling."
        )

        if st.button("Submit config"):
            if not api_key:
                st.error('Enter the API key')
                st.stop()
            self.save_llm_keys(api_key, claude_key, function_call_availabilty)
        else:
            st.stop()
            
    def save_llm_keys(self, api_key, claude_key, function_call_availabilty):
        openai.api_key = api_key
        config = {
            'openai': {'key': api_key},
            'claude': {'key': claude_key} if claude_key else {},
            'function_call_availabilty': function_call_availabilty
        }

        with st.spinner('Saving config...'):
            time.sleep(2)

        with open(self.secrets_file_path, 'w') as f:
            toml.dump(config, f)
            time.sleep(.5)
            st.success('Config saved successfully')
        return None

# # # Usage
# # configurator = ProjectConfigurator()
# # configurator.config_project()
# #------------OLD CODE----------------
# def set_or_get_llm_keys():

#     # Check if the user has a secrets file and openai key in the secrets.toml file. if yes, then set the openai key

#     # Get the project folder from the session state
#     user_folder = st.session_state.user_folder
#     # Create the secrets.toml file if it does not exist
#     secrets_file_path = os.path.join(user_folder, 'secrets.toml')
#     if not os.path.exists(secrets_file_path):
#         with open(secrets_file_path, 'w') as f:
#             f.write('')
#         st.session_state.config = {}
#     else:
#         with open(secrets_file_path, 'r') as f:
#             config = toml.load(f)
#             st.session_state.config = config
#     api_key = st.session_state.config.get('openai', {}).get('key', '')
#     claude_key = st.session_state.config.get('claude', {}).get('key', '')
#     if api_key != '':
#         openai.api_key = api_key
#     if claude_key != '':
#         st.session_state.claude_key = claude_key
#     return api_key

# def config_project():
#     """
#     For a new project, there should be a config.json file in the project_settings folder. if not, then this function will create one.
#     this config file should have the following keys:
#     - preferred model (str): The preferred model for the project, e.g. gpt-3.5-turbo-16k, gpt-3.5-turbo, gpt-4, etc.
#     - api key (str): The API key for the openai API, if preferred model is openai's
#     - function_call_availabilty (bool): Does the user have access to the 0613 models of openai?

#     Save the api key to streamlit secrets.toml file
    
#     """
#     # Get the secrets_file_path from the session state
#     secrets_file_path = st.session_state.secrets_file_path
#     with open(secrets_file_path, 'r') as f:
#         config = toml.load(f)
#         st.session_state.config = config

#     # Check if the user wants to upload a custom LLM file or set the openai API key
#     default_index = 0
#     api_key = set_or_get_llm_keys()
#     if os.path.exists(os.path.join(st.session_state.typebuild_root, 'custom_llm.py')):
#         default_index = 1

#     llm_selection = st.radio('Select an option', ['Set OpenAI API key', 'Upload Custom LLM'], horizontal=True, index=default_index)

#     if llm_selection == 'Upload Custom LLM':
#         upload_custom_llm_file()
#         st.stop()
#     else:
#         api_key = st.text_input('Enter OpenAI key', value=st.session_state.config.get('openai', {}).get('key', ''))
#         claude_key = st.text_input('Enter Claude key', value=st.session_state.config.get('claude', {}).get('key', ''))

#         function_call_availabilty = st.checkbox(
#             "(Expert setting) I have access to function calling", 
#             value=st.session_state.config.get('function_call_availabilty', True),
#             help="Do you have access to openai models ending in 0613? they have a feature called function calling.",
#             )
            
#         if st.button("Submit config"):
#             if api_key == '':
#                 st.error('Enter the API key')
#                 st.stop()
#             # Save the config to the config.json file
#             config = {}
#             # set the openai key
#             openai.api_key = api_key
#             # Save the API key in the secrets module
#             config['openai'] = {'key': api_key}
#             if claude_key != '':
#                 config['claude'] = {'key': claude_key}
#             config['function_call_availabilty'] = function_call_availabilty
#             if function_call_availabilty:
#                 st.session_state.function_call_type = 'auto'
#             else:
#                 st.session_state.function_call_type = 'manual'
#             # Save the config to the config.json file
#             with st.spinner('Saving config...'):
#                 time.sleep(2)

#             if not os.path.exists(secrets_file_path):
#                 with open(secrets_file_path, 'w') as f:
#                     f.write('')
#             with open(secrets_file_path, 'r') as f:
#                 config_ = toml.load(f)

#             # Add the API key to the config dictionary
#             config_['openai'] = {'key': api_key}
#             if claude_key != '':
#                 config_['claude'] = {'key': claude_key}
#             config_['function_call_availabilty'] = function_call_availabilty
#             # Save the config to the secrets.toml file
#             with open(secrets_file_path, 'w') as f:
#                 toml.dump(config_, f)
#                 st.toast('Hip!')
#                 time.sleep(.5)
#                 st.success('Config saved successfully')
#         return None
    

