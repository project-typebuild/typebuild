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
import chardet


def create_document_chunk_df(documents_folder):

    """
    Select the documents to be used for the analysis and create a dataframe with the text of the chunks of the documents

    Parameters
    ----------
    documents_folder : str
        The path to the folder with the documents
    """
    available_documents = glob(f'{documents_folder}/*')
    # read all text files in the folder
    documents = []
    for document in available_documents:
        tmp_dict = {}
        with open(document, 'r') as f:
            contents = f.read()
            encoding = chardet.detect(contents)['encoding']
            contents = contents.decode(encoding)
            tmp_dict['text'] = contents

        tmp_dict['filename'] = document.split('/')[-1]
        documents.append(tmp_dict)
    
    return pd.DataFrame(documents)