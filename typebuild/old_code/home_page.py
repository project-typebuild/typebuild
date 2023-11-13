"""
Home page of the app.  There's a home page for logged in users 
and a home page for non-logged in users.

Currently focusing on the home page for logged in users.
"""
import streamlit as st
from menu import reset_menu
import os
from PIL import Image

def home_page():
    st.header("What you can do with TypeBuild", divider='rainbow')
    st.info("""**Click Functionalities in the menu on top to access the functionalities discussed below.**""")
    what_can_you_do()

def what_can_you_do():
    dir_path = st.session_state.dir_path
    c1, c2 = st.columns([1, 1])
    with c1:
        image_path = os.path.join(dir_path, 'images', 'upload_data.png')
        st.image(image=Image.open(image_path), output_format='PNG', use_column_width=True)
        caption='''**DATA**: Upload your own data or fetch data from the web.
            ***You should have some data to use other functionalities.***
            '''
        st.warning(caption)
    
    with c2:
        image_path = os.path.join(dir_path, 'images', 'ideate.png')
        st.image(image=Image.open(image_path), output_format='PNG', use_column_width=True)
        caption='''**IDEATE**: Ideate using the language model.  Useful to identify personas and to create user journeys'''
        st.warning(caption) 

    c1, c2 = st.columns([1, 1])
    # Add a button to go to the ideate page
    with c2:
        image_path = os.path.join(dir_path, 'images', 'llm.png')
        st.image(image=Image.open(image_path), output_format='PNG', use_column_width=True)
        caption='''**LLM ANALYSIS**: Analyze your data using a language model.  
            Useful to synthesize research, categorize data, and to extract specific insights from documents.
            '''
        st.warning(caption)

    with c1:
        # Build mini-apps, forms, and data analysis
        image_path = os.path.join(dir_path, 'images', 'build.png')
        st.image(image=Image.open(image_path), output_format='PNG', use_column_width=True)
        caption='''**APPS & ANALYSIS**: Build mini-apps, create forms, or analyze data using natural language.
            This is great for creating prototypes, simple workflows, and to analyze data.
            '''
        st.warning(caption)