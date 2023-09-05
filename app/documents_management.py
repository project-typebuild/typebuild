import streamlit as st
from glob import glob
from llama_index import SimpleDirectoryReader
import pandas as pd
import os
from llm_functions import get_llm_output
from streamlit_extras.dataframe_explorer import dataframe_explorer
import nest_asyncio
nest_asyncio.apply()

def create_document_chunk_df():

    """
    Select the documents to be used for the analysis
    """
    if 'project_folder' not in st.session_state:
        st.warning('Please select a project folder first.')
        st.session_state.project_folder = 'users/ranu/nrega'
    project_folder = st.session_state.project_folder
    files = glob(f'{project_folder}/documents/*')
    selected_files = st.sidebar.multiselect('Select the documents to be used for the analysis', files)

    if len(selected_files) == 0:
        st.stop()
    else:
        for selected_file in selected_files:
            reader = SimpleDirectoryReader(
                    input_files=[selected_file],
                )
            docs = reader.load_data()
            docs_text = [o.text for o in docs]
            # Convert the list of documents to a dataframe with a column called 'text', add file name, add index
            docs_text = pd.DataFrame(docs_text, columns=['text'])
            docs_text['file_name'] = selected_file.split('/')[-1]
            docs_text['index'] = docs_text.index
            docs_text = docs_text.set_index('index')
            # Save the dataframe to data folder in parquet format if file doesn't exist
            if not os.path.exists(f'{project_folder}/data/{selected_file.split("/")[-1]}.parquet'):
                docs_text.to_parquet(f'{project_folder}/data/{selected_file.split("/")[-1]}.parquet')
    return docs_text

df = create_document_chunk_df()
st.subheader('Sample data')
filtered_df = dataframe_explorer(df, case=False)
st.dataframe(filtered_df, use_container_width=True)
system_instruction = st.text_area('Enter your requirements here')
if not system_instruction:
    st.error('Please enter your requirements to continue.')
    st.stop()


for index, row in filtered_df.iterrows():
    prompt = row['text']
    messages =[
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt},
    ]
    response = get_llm_output(messages)
    filtered_df.loc[index, 'response'] = response

st.write(filtered_df)