import hashlib
import os
import pickle as pk
import streamlit as st
import time
import pickle as pk
import extra_streamlit_components as stx
import json
import datetime

# This expander will be invoked right when simple auth is imported into main.py
# putting it here will ensure that auth is right on top.


def create_auth_file():
    profile_dict = {'admin': None}
    with open('profile_dict.pk', 'wb') as f:
        pk.dump(profile_dict, f)
    print("Created profile dict")
    return None

def reset_user_password():

    with open('profile_dict.pk', 'rb') as f:
        p = pk.load(f)
    users = list(p)
    users.remove('admin')
    users.insert(0, 'Select')
    reset_user = st.selectbox('Select user to reset password', users)

    if st.button("Reset this user's password"):
        p[reset_user] = None

        with open('profile_dict.pk', 'wb') as f:
            pk.dump(p, f)
        st.success(f"Reset done. Ask {reset_user} to create a new password")
    return None

def delete_users():
    with open('profile_dict.pk', 'rb') as f:
        p = pk.load(f)
    users = list(p)
    users.remove('admin')
    to_delete = st.multiselect("Delete users", users)
    if to_delete:
        if st.button("Confirm deletion"):
            for t in to_delete:
                del p[t]
            with open('profile_dict.pk', 'wb') as f:
                pk.dump(p, f)
            st.success("Done")
            time.sleep(2)
            st.experimental_rerun()
            
    return None

def get_profile_dict():
    if not os.path.exists('profile_dict.pk'):
        create_auth_file()
    with open('profile_dict.pk', 'rb') as f:
        profile_dict = pk.load(f)
    return profile_dict

def get_key(salt, pwd):
    return hashlib.pbkdf2_hmac('sha256', pwd.encode('utf-8'), salt, 100000)


def set_key(token, pwd):
    salt = os.urandom(32) # A new salt for this user
    key = get_key(salt, pwd)
    profile_dict = get_profile_dict()
    profile_dict[token] = {salt: key}
    with open('profile_dict.pk', 'wb') as f:
        pk.dump(profile_dict, f)
    
    return None

def add_user(user):
    profile_dict = get_profile_dict()
    profile_dict[user] = None
    with open('profile_dict.pk', 'wb') as f:
        pk.dump(profile_dict, f)
    
    return None

def simple_auth():
    '''
    This tries to authenticate first with session state variable,
    next with a cookie and if both fails, it asks for the user to login. 

    It also creates a logout button.
    '''

    
    # Create a logout button right on top.
    if 'new_menu' in st.session_state:
        if st.session_state.new_menu == 'logout':
            st.session_state['logmeout'] = True
    # Default token
    token = None
    # If the logout button was pressed, it will create
    # a session state to log out.  Created this workaround
    # due to the behaviour of the cookie_manager object.
    # If logmeout is there, invoke logout.
    # The user has to close the browser tab to login again.  The new session will not have this variable in session state.
    if 'logmeout' in st.session_state:
        logout()
    # If there is authorization in the system, use it.
    elif 'token' in st.session_state:
        token = st.session_state['token']
    else:
        cookie_manager = stx.CookieManager()
        token = get_cookie_token(cookie_manager)

    # If not authorized in this session, do that.
    if token is None:
        if 'logmeout' not in st.session_state:
            token = get_auth(cookie_manager)
            st.session_state['token'] = token
        else:
            st.warning("You just logged out.  Please close the browser tab. Or refresh the page to login again.")
    if token is None:
        st.stop()        
    if token == 'admin': 
        with st.sidebar.expander("Admin"):
            add_user_if_admin(token)
            use_as_user = st.text_input("View as user")
            if use_as_user != '':
                token = use_as_user
            reset_user_password()
            delete_users()

    return token

def get_cookie_token(cookie_manager):
    token = None
    cookies = cookie_manager.get_all()
    if isinstance(cookies, str):
        cookies = json.loads(cookies)
    cookie_token = None if cookies is None else cookies.get('cookie_token', None)
    profile_dict = get_profile_dict()
    if cookie_token is not None:
        if cookie_token in profile_dict:
            token = cookie_token
            st.session_state['token'] = token    
    return token

def logout():
    cookie_manager = stx.CookieManager()
    try:
        cookie_manager.delete('cookie_token')
    except:
        pass
    return None

# Add user
def add_user_if_admin(token):
    user_name_new = st.sidebar.text_input("Add User name")
    if st.sidebar.button("Add user"):
        add_user(user_name_new)
        st.sidebar.success("Added user")

def get_auth(cookie_manager):
    temp_header = st.empty()
    token = st.text_input('username', autocomplete='first_name').lower()
    pwd = st.text_input("What's the password", type='password')

    if token == '':
        temp_header.error("Please sign in")
        st.stop()

    else:
        profile_dict = get_profile_dict()
        # If there is no user, it'll return None
        if token not in profile_dict:
            st.error("Sorry, you do not have access to the system.  Please write to the admin for access.")
            st.stop()
        # If the user is in the system.
        else:
            salt_key = profile_dict[token]

            # They profile will not have the salt and key if the user has not set a password
            # Ask user to set password        
            if salt_key is None:
                st.error("You have not set a password yet, please set one")
                pwd2 = st.text_input("Please repeat your password", type="password")
                if st.button("Set password"):
                    if pwd == pwd2:
                        set_key(token, pwd)
                        st.success("I've set the password for you.  Please contact admin if you have to reset it")
                        time.sleep(3)
                        st.experimental_rerun()
                    else:
                        st.warning("The two passwords you typed do not match.  Please correct.")
                st.stop()
            # If the user has set a password.
            else:
                salt = list(salt_key.keys())[0]
                orig_key = list(salt_key.values())[0]

                entered_key = get_key(salt, pwd)
                if entered_key != orig_key:
                    dummy = st.button("Submit", key='pwd_dummy')
                    st.error("Please enter the correct password or contact admin to reset")
                    st.stop()
                else:
                    # Not sure why I needed this...so commenting it out.
                    #if isinstance(st.session_state['cookies'], str):
                        #st.session_state['cookies'] = json.loads(st.session_state['cookies'])
                    # Set it to expire in 2 weeks
                    days_from = datetime.datetime.now() + datetime.timedelta(14)
                    cookie_manager.set('cookie_token', token, expires_at=days_from)
    return token