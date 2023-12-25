import streamlit as st
import sys
sys.path.append("..")  # Add the parent directory to the sys.path
from data_management.selector import DataSelector
from plugins.llms import get_llm_output

class DataModelSelectorTool:

    def __init__(self):
        if 'data_selector' not in st.session_state:
            st.session_state.data_selector = DataSelector()
        pass

    def _get_all_available_tabular_data(self):
        """
        Returns a list of all available tabular data files.
        """
        data_selector = st.session_state.data_selector
        return data_selector._get_all_available_tabular_data()

    def interface(self):
        """
        Displays the interface for the Data Selector tool.
        """

        # Get all available tabular data
        tabular_files = self._get_all_available_tabular_data()

        # Get the file name
        file_names = st.multiselect('Please select a file', tabular_files)

        # Get the column names for the file
        data_selector = st.session_state.data_selector

        # Get the column names for the file
        data_dict = data_selector._get_tabular_data_and_col_names(file_names)

        return data_dict


def tool_main(auto_rerun=False):

    """
    This tool will help the user select the data file and column name that they want to use for the task.

    parameters
    ----------
    auto_rerun: bool
        If True, the tool will automatically rerun itself.
    
    returns
    -------
    res_dict: dict
        A dictionary containing the results of the tool.
        
    """
    # Given a user query, the Planner will call this tool to get the file name and column name
    # When this starts, set ask llm to False
    
    data_selector_tool = DataModelSelectorTool()
    data_dict = data_selector_tool.interface()
    if data_dict is None:
        return None
    else:
        return data_dict