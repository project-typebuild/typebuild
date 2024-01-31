import pandas as pd
import streamlit as st
import re
import os
class Display():

    def __init__(self):
        pass

    def dataframe(self, file_name, columns=[]):
        # TODO: How do we display the data as nicely formatted text
        # given that column names can be different in different files?
        # Use an LLM to create the streamlit output?        
        df = pd.read_parquet(file_name)
        
        # Give the user the option to view as text or as a dataframe
        if columns is None:
            columns = []
        if len(columns) == 1:
            view_text = True
        else:
            view_text = st.checkbox('View as text')
        
            
        if view_text:
            # Select columns in the order you want to display them
            selected_cols = st.multiselect(
                'Select columns to display', 
                df.columns.tolist(),
                default=columns
                )

            text_dict = df[selected_cols].dropna(how='all').to_dict('records')
            all_text = []
            
            for row in text_dict:
                text = ""
                for key in row:
                    value = str(row[key]) \
                        .replace('\\n', '\n') \
                        .replace('\t', '\n')
                    value = re.sub(r'^\s+', '\n', value, flags=re.MULTILINE)
                    text += f"### {key}:\n{value}\n"
                text += "\n---\n"
                all_text.append(text)
            with st.expander("Expand to view the text"):
                num_words = sum([len(t.split()) for t in all_text])
                # If the total words is less than 5000, show all text
                if num_words < 5000:
                    for text in all_text:
                        st.markdown(text)
                # Paginate the text otherwise
                else:
                    show_row = st.number_input('Show row', min_value=0, max_value=len(all_text)-1, value=0)
                    st.markdown(all_text[show_row])
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
    if "/data/" not in file_name:
        file_name = os.path.join(st.session_state.data_folder, file_name)

    display = Display()

    display.dataframe(file_name, columns=columns)

    res_dict = {
        'content': "The dataframe has been displayed.",
        'task_finished': True,
        'ask_llm': False
    }
    return res_dict