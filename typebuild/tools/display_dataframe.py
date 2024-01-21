import pandas as pd
import streamlit as st
import re

class Display():

    def __init__(self):
        pass

    def dataframe(self, file_name, columns=None):
        # TODO: How do we display the data as nicely formatted text
        # given that column names can be different in different files?
        # Use an LLM to create the streamlit output?        
        df = pd.read_parquet(file_name)
        if columns:
            df = df[columns]
        # Give the user the option to view as text or as a dataframe
        if len(df.columns) == 1:
            view_text = True
        else:
            view_text = st.checkbox('View as text')
        if view_text:
            text = df.to_string(index=False)
            # For every line break, add a divider
            # text = text.replace('\n', '\n---\n\n')
            # line breaks could be escaped.  Remove the escape characters.
            text = text.replace('\\n', '\n')
            # convert tab characters
            text = text.replace('\t', '\n')
            # remove line indents with regex
            text = re.sub(r'^\s+', '\n', text, flags=re.MULTILINE)
            with st.expander("Expand to view the text"):
                st.markdown(text)
        else:
            st.dataframe(df)

        return None



def tool_main(file_name, columns=None, auto_rerun=True):
    """
    Given a file name, this tool will display the dataframe.

    Args:
        file_name (str): The name of the file to display.
        columns (list, optional): The columns to display. If None, all columns will be displayed. Defaults to None.
    Returns:
        None
    """
    display = Display()

    display.dataframe(file_name, columns=columns)

    res_dict = {
        'content': "The dataframe has been displayed.",
        'task_finished': True,
        'ask_llm': False
    }
    return res_dict