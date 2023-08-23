import simple_auth
import streamlit as st
# Make it full width
st.set_page_config(layout="wide")
token = simple_auth.simple_auth()

import session_state_management

session_state_management.main()
