import streamlit as st

def test():
    # file = "/home/vivek/.typebuild/users/vivek/data/arxiv_all_confabulation_hallucination_language_models.parquet"
    # display = Display(file)
    dynamic_functions = st.session_state.dynamic_functions
    # Go through all the keys and dynamically call the values
    for key in dynamic_functions:
        the_function = dynamic_functions[key].get('func')
        if the_function:
            the_function()

