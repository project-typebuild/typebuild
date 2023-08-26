import simple_auth
import streamlit as st
# Make it full width
st.set_page_config(layout="wide")
# token = simple_auth.simple_auth()
token = 'ranu'
st.session_state.token = token

import session_state_management

session_state_management.main()

from project_management import get_project_file_folder, get_project_df
from function_management import create_run_menu


if st.sidebar.checkbox('Show session state'):
    st.write(st.session_state)

# Create a menu to run the app
get_project_file_folder()
if 'df' not in st.session_state:
    get_project_df()

create_run_menu()
if 'last_request' in st.session_state:
    if st.sidebar.checkbox("Show latest request"):
        st.write(st.session_state.last_request)