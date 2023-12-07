import streamlit as st
import sys
sys.path.append("..")  # Add the parent directory to the sys.path
from data_management.selector import DataSelector
from plugins.llms import get_llm_output

class DataSelectorTool:

    def __init__(self):
        if 'data_selector' not in st.session_state:
            st.session_state.data_selector = DataSelector()
        pass

    def _get_tabular_files(self):
        """
        Returns a list of all available tabular data files.
        """
        data_selector = st.session_state.data_selector
        return data_selector._get_all_available_tabular_data()

    def _get_colnames_for_file(self, file_name):
        """
        Returns a list of column names for the given file.
        """
        data_selector = st.session_state.data_selector
        data_model = data_selector._get_data_model()
        return data_model[data_model['file_name'] == file_name]['colnames'].tolist()[0]

    def interface(self):
        """
        Displays the interface for the Data Selector tool.
        """
        data_selector = st.session_state.data_selector
        file_name, input_column = data_selector.interface()
        
        return file_name, input_column
        
        
def tool_main(auto_rerun=False):

    """
    This tool will help the user select the data file and column name that they want to use for the task.
    """
    # Given a user query, the Planner will call this tool to get the file name and column name
    # When this starts, set ask llm to False
    st.session_state.ask_llm = False
    data_selector_tool = DataSelectorTool()
    file_name, input_column = data_selector_tool.interface()
    if file_name is None or input_column is None:
        st.stop()
    content = f"I selected {file_name} and {input_column} for you.  You can use this for the next steps."
    res_dict = {
        'content': content,
        'file_name': file_name,
        'input_column': input_column,
        'ask_llm': False,
        'task_finished': False,       
    }

    return res_dict



