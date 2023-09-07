import streamlit as st
from glob import glob
import os
import time
import pandas as pd
from streamlit_extras.dataframe_explorer import dataframe_explorer
from helpers import text_areas
from plugins.llms import get_llm_output

def create_destination_df(destination_df_name, consolidated=False):
    """
    To analyze data with LLM, we need to create a new dataframe
    with the name of the view.
    """
    # Select the source dataframe and column
    st.write("### Select the source data and column(s)")
    data_folder = st.session_state.project_folder + '/data'
    tables = glob(f"{data_folder}/*.parquet")
    st.write(tables)
    # If there is more than one table, allow the user to select the table
    if len(tables) == 0:
        st.error("There should be some uploaded data for this to work.  Please upload some data from the project settings area.")
        st.stop()
    if len(tables) == 1:
        source_df = tables[0]
    else:
        source_df = st.selectbox("Select the source dataframe", tables)
    
    # Read the source dataframe
    df = pd.read_parquet(source_df)

    # Get the column names
    columns = df.columns

    # Select the column to use
    how_to_select = """If more than one column is selected, the text from each column will be 
    appended with paragraphs in-between and used as the input to the LLM.  The sequence
    of the text will be based on the order of the columns selected.
    """

    st.info(how_to_select)
    columns = st.multiselect("Select the column(s) to use", columns)
    if not columns:
        st.error("Please select at least one column.")
        st.stop()
    # Get the text from the columns
    df["text_for_llm"] = df[columns].apply(lambda x: '\n'.join(x), axis=1)

    # Give option to filter the dataframe based on selected files
    if st.checkbox("Filter documents to use for the analysis", help="Use this if you want to analyze something specific."):
        original_len = len(df)
        df = dataframe_explorer(df, case=False)
        filtered_len = len(df)
        # Provide filter information
        st.info(f"Removed {original_len - filtered_len} / {original_len} rows from the dataframe. {filtered_len} rows remain.")


    # Copy the id column (ends with _id) and the text_for_llm column to the destination dataframe
    id_col = [col for col in df.columns if col.endswith('_id')]
    # If there is no id column, create sequential ids starting with 1
    if len(id_col) == 0:
        id_col_name = source_df.split('/')[-1].split('.')[0] + '_tbid'
        df[id_col_name] = range(1, len(df) + 1)
        id_col = [id_col_name]        
        df.to_parquet(source_df)

    if consolidated:
        # If the user is consolidating the data, then there
        # we cannot join with the original dataframe anymore.
        # We will create a df with just one row and the column text_for_llm
        df = pd.DataFrame({'text_for_llm': [df['text_for_llm'].str.cat(sep='\n\n')]})
        col_info = f"""This dataframe has just one row with the consolidated text from the source dataframe {source_df}.
        The column information is as follows:
        - text_for_llm: The text to be analyzed by the LLM taken from the source dataframe.
        """
    else:
        id_col = id_col[0]
        df_for_llm = df[[id_col, 'text_for_llm']]
        # Create an id for this dataframe
        dest_id_name = destination_df_name.split('/')[-1].split('.')[0] + '_tbid'
        
        # Col info to save to the data model file
        col_info = f"""
    - {id_col}: The id column of the dataframe
    - {dest_id_name}: The id column of the dataframe created for LLM analysis
    - text_for_llm: The text to be analyzed by the LLM taken from the source dataframe.
    """
    
    # Save the destination dataframe
    # Save the source dataframe with the new id column
    if st.button("Save the file"):
        df_for_llm.to_parquet(destination_df_name)
        # Save the col info to the data model file
        write_to_data_model(destination_df_name, col_info=col_info)

        st.success("I created a new table with this data.  We are ready for the next step.")
        time.sleep(2)
        st.experimental_rerun()
    
    return None



def analyze_with_llm(consolidated=False):

    # Name the destination dataframe is view_name.parquet
    view_name = st.text_input(
        "Give the output table a name", 
        key='view_name',
        help="If you do row by row analysis, you will be able to compare the original data with the LLM output."
        )
    if not view_name:
        st.error("The text returned from the LLM will be added to a new table with this name.")
        st.stop()

    data_folder = st.session_state.project_folder + '/data'
    destination_df_name = f"{data_folder}/{view_name}.parquet"

    # Create the destination dataframe if it doesn't exist
    if not os.path.exists(destination_df_name):
        create_destination_df(destination_df_name, consolidated)
    else:
        df = pd.read_parquet(destination_df_name)
    

    st.header("Row by row analysis")
    step1_desc = """On most occasions, you will want to analyze the data row by row to start with.  Even if you are creating a summary of the entire data, it is useful to get a row by row summary first since language models can only deal with limited amount of text at a time.

    - In the box below, tell the LLM what you would like it to do in each row of data (see examples below).
    - View sample output from the LLM for the 5 randomly selected rows.  If that makes sense, ask the LLM to analyze the entire data.
    - When the LLM is done, you can move to the next step to consolidate the results.

    **If you do not want row by row analysis, you can skip this step and move to the next step.**
    """
    # Replace indents in each line (indents will introduce code blocks when streamlit displays the text)
    step1_desc = '\n'.join([line.strip() for line in step1_desc.split('\n')])    
    st.markdown(step1_desc)

    # Get the system instruction
    txt_file = destination_df_name.replace('.parquet', '_row_by_row.txt')
    # Save this as the system instruction path
    st.session_state.system_instruction_path = txt_file
    system_instruction = text_areas(
        file=txt_file,
        key='system_instruction_step_by_step',
        widget_label='What would you like the LLM to do in each row?'
        )

    if len(system_instruction) < 20:
        st.error(f"Please enter at leat 20 characters. {20-len(system_instruction)} more characters needed.")
        st.stop()

    # Give option to reset prior analysis
    if st.sidebar.checkbox("Reset prior analysis"):
        st.info("This will remove prior analysis and start over.")
        # Ask for a confirmation
        if st.sidebar.button("Reset"):
            df['row_by_row_analysis'] = ''
    # Sample or full run
    sample_or_full = st.radio("Sample or full run?", ['Sample', 'Full run'])
    # If row_by_row_analysis column does not exist, create it
    if 'row_by_row_analysis' not in df.columns:
        df['row_by_row_analysis'] = ''
    if sample_or_full == 'Sample':
        # Get a sample of 3 rows, if there are at least 5 rows
        if len(df) > 3:
            sample = df.sample(3)
        else:
            sample = df
        if st.button("Reset & Analyze the sample"):
            # Remove prior analysis
            df['row_by_row_analysis'] = ''
            # Save the dataframe to the destination dataframe
            # Add row by row analysis to the sample
            with st.spinner("Analyzing the sample data..."):
                sample['row_by_row_analysis'] = sample['text_for_llm'].apply(lambda x: row_by_row_llm_res(x, system_instruction))
                # Update the dataframe and save the sample.
                df.update(sample)
                df.to_parquet(destination_df_name)
        st.dataframe(sample)

    if sample_or_full == 'Full run':
        remaining_rows = len(df[df.row_by_row_analysis == ''])
        if remaining_rows == 0:
            st.success("All rows have been analyzed.")
        else:
            st.info(f"There are {remaining_rows} rows remaining to be analyzed.")
            if st.button("Analyze rest of the data"):
                # Keep sample analysis and run on the rest of the data
                with st.spinner("Analyzing the rest of the data..."):
                    df.loc[df.row_by_row_analysis == '', 'row_by_row_analysis'] = df.loc[df.row_by_row_analysis == '', 'text_for_llm'].apply(lambda x: row_by_row_llm_res(x, system_instruction))

    # Show the input and output in two columns
    for row in df[df.row_by_row_analysis != ''].itertuples():
        c1, c2 = st.columns(2)
        c1.subheader("Input text")
        c1.markdown(row.text_for_llm, unsafe_allow_html=True)
        c2.subheader("LLM output")
        c2.markdown(row.row_by_row_analysis, unsafe_allow_html=True)
    
    return None
def row_by_row_llm_res(text, system_instruction, sample=True):
    # Chunk the text by 10k characters
    chunks = chunk_text(text, max_chars=10000)
    output = ""
    if sample:
        chunks = chunks[:2]
    
    for chunk in chunks:
        max_tokens = chunk/3
        messages =[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": chunk}]
        res = get_llm_output(
            input=messages,
            max_tokens=max_tokens,
            model='gpt-3.5-turbo-16k'
            )
        output += res + '\n\n'
    return output

def chunk_text(text, max_chars=None, model_name='gpt-3.5-turbo'):
    """
    Chunk text into chunks of max_chars.
    """
    # Set max chars, not setting token length as per openai here.
    max_chars_by_model = {
        'gpt-3.5-turbo': 5000,
        'gpt-3.5-turbo-16k': 48000,
        'gpt-4': 45000,
        'claude': 150000
    }
    if max_chars is None:
        max_chars = max_chars_by_model[model_name]
    chunks = []
    chunk = ''
    # Split the text into sentences
    sentences = text.split('.')
    # Remove empty sentences
    sentences = [s for s in sentences if s.strip()]
    # Chunk the sentences        
    for s in sentences:
        if len(chunk) + len(s) < max_chars:
            chunk += f"{s}."
        else:
            chunks.append(chunk)
            chunk = f"{s}."
    chunks.append(chunk)
    return chunks

def write_to_data_model(file_name, col_info):
    """
    Write the file information to the llm augmented data model.
    Note: All LLM generated text will have the same column names and so 
    they do not mean much.  It's critical to have the system instruction
    as a part of the data model.  In this approach, we will be able to do it.
    """
    system_instruction_path = st.session_state.system_instruction_path
    data_model_file = st.session_state.project_folder + '/llm_data_model.pk'
    import pickle as pk
    if not os.path.exists(data_model_file):
        with open(data_model_file, 'wb') as f:
            pk.dump({}, f)
    with open(data_model_file, 'rb') as f:
        data_model = pk.load(f)

    # Add the file name and system_instruction path to the data model
    data_model[file_name] = {
        'system_instruction_path': system_instruction_path,
        'col_info': col_info
        }

    # Save the data model
    with open(data_model_file, 'wb') as f:
        pk.dump(data_model, f)

    return None

def add_data_with_llm():
    """
    This function allows the user to extract insights 
    from existing data using an LLM.  It can be used to
    summarize, classify, answer questions, or to extract specific information
    from a given column of the source dataframe.

    The results will be written to a new dataframe that 
    will connect to the primary key of the source dataframe.

    Args:
    None: User will select the source dataframe and column(s) to use with widgets.

    Returns:
    None    

    """
    
    step = st.radio(
        "How would you like to analyze",
        ['Row by row', 'Consolidated', 'Results'],
        horizontal = True
        )

    if step == 'Row by row':
        analyze_with_llm(consolidated=False)
    
    if step == 'Consolidated':
        analyze_with_llm(consolidated=True)

    return None
