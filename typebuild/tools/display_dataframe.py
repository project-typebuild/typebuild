import pandas as pd
import streamlit as st


class Display():

    def __init__(self):
        pass

    def dataframe(self, file_name):
        
        df = pd.read_parquet(file_name)

        st.dataframe(df)

        return None



def tool_main(file_name, auto_rerun=True):
    """
    Given a file name, this tool will display the dataframe.

    Args:
        file_name (str): The name of the file to display.

    Returns:
        None
    """
    display = Display()

    display.dataframe(file_name)

    res_dict = {
        'content': "The dataframe has been displayed.",
        'task_finished': True,
        'ask_llm': False
    }
    return res_dict