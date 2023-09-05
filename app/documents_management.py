import streamlit as st
from glob import glob
from llama_index import SimpleDirectoryReader
import pandas as pd
import os
from llm_functions import get_llm_output
from streamlit_extras.dataframe_explorer import dataframe_explorer
from streamlit_extras.stateful_button import button
import nest_asyncio
nest_asyncio.apply()


def create_document_chunk_df(documents_folder):

    """
    Select the documents to be used for the analysis and create a dataframe with the text of the chunks of the documents

    Parameters
    ----------
    selected_file: list
        The path to the file selected by the user
    """
    reader = SimpleDirectoryReader(
                    input_dir=documents_folder,
                )
    docs = reader.load_data()
    docs_text = [o.text for o in docs]
    filenames = [o.metadata['file_name'] for o in docs]
    # Convert the list of documents to a dataframe with a column called 'text', add file name, add index
    df_chunks = pd.DataFrame({'text': docs_text, 'filename': filenames})
    return df_chunks