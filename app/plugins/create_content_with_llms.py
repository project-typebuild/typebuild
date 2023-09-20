import numpy as np
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
        all_col_info = []
        col_info = {}
        col_info['file_name'] = source_df
        col_info['dataframe_description'] = f'This dataframe has just one row with the consolidated text from the source dataframe {source_df}.'
        col_info['column_name'] = 'text_for_llm'
        col_info['column_type'] = 'str'
        col_info['column_info'] = 'The text to be analyzed by the LLM taken from the source dataframe.'
        all_col_info.append(col_info)
    else:
        id_col = id_col[0]
        df_for_llm = df[[id_col, 'text_for_llm']]
        # Create an id for this dataframe
        dest_id_name = destination_df_name.split('/')[-1].split('.')[0] + '_tbid'
        
        # Col info to save to the data model file

        all_col_info = []
        col_info = {}
        col_info['file_name'] = source_df
        col_info['dataframe_description'] = f'This dataframe has the id column of the source dataframe.'
        col_info['column_name'] = id_col
        col_info['column_type'] = 'int'
        col_info['column_info'] = 'The id column of the source dataframe.'
        all_col_info.append(col_info)
        col_info = {}
        col_info['file_name'] = source_df
        col_info['dataframe_description'] = f'This dataframe has the id column of the dataframe created for LLM analysis.'
        col_info['column_name'] = dest_id_name
        col_info['column_type'] = 'int'
        col_info['column_info'] = 'The id column of the dataframe created for LLM analysis.'
        all_col_info.append(col_info)
        col_info = {}
        col_info['file_name'] = source_df
        col_info['dataframe_description'] = f'This dataframe has the text to be analyzed by the LLM taken from the source dataframe.'
        col_info['column_name'] = 'text_for_llm'
        col_info['column_type'] = 'str'
        col_info['column_info'] = 'The text to be analyzed by the LLM taken from the source dataframe.'
        all_col_info.append(col_info)

    # Get the column information for the dataframe
    col_info_df = pd.DataFrame(all_col_info)

    # Save the destination dataframe
    # Save the source dataframe with the new id column
    if st.button("Save the file"):
        df_for_llm.to_parquet(destination_df_name)
        # Save the col info to the data model file
        write_to_data_model(destination_df_name, col_info_df=col_info_df)

        st.success("I created a new table with this data.  We are ready for the next step.")
        time.sleep(2)
        st.experimental_rerun()
    
    return df_for_llm

def select_output_col(df):
    """
    Allow the user to select the output column.
    Create a new column if it does not exist.

    Args:
        df (pd.DataFrame): The dataframe to use.
    Returns:
        output_col_name (str): The name of the output column.
    """
    columns = df.columns
    # Select the column to write into.  It has to start with llm_
    # Could also be a new column
    llm_cols = [col for col in columns if col.startswith('llm_')]
    # Add a new column option
    llm_cols.append('Add a new column')
    output_col_name = st.selectbox(
        "Select Output Column", 
        llm_cols,
        help="This column will be used to store the output from the LLM."
        )
    
    if output_col_name == 'Add a new column':
        output_col_name = st.text_input(
            "Give the output column a name", 
            key='output_col_name',
            help="A new column will be added to your data to store this result."
            )
        if not output_col_name:
            st.error("The text returned from the LLM will be added to a new table with this name.")
            st.stop()
        else:
            output_col_name = "llm_" + output_col_name.strip()
            st.markdown(f"Will add the output to a new column called **{output_col_name}**")
        # If the output column already exists, ask the user to select a different name
        if output_col_name in df.columns:
            st.error("This column already exists.  Give it a different name, or select it from the drop down to overwrite.")
            st.stop()
        # Create the new column if it does not exist
        if output_col_name not in df.columns:
            df[output_col_name] = np.nan
    
    return output_col_name


def analyze_with_llm():


    data_folder = st.session_state.project_folder + '/data'
    tables = glob(f"{data_folder}/*.parquet")

    c1, c2 = st.columns(2)
    # Select the source dataframe
    selected_table = c1.selectbox("Select the source data", tables)
    
    # Get the column names
    df = pd.read_parquet(selected_table)
    if c1.checkbox("Show input data"):
        st.dataframe(df.head())
    
    with c2:
        # Select the output column
        output_col_name = select_output_col(df)
    if c2.checkbox(
        "New analysis with LLM",
        help="Summarize or extract insights from an input column",  
        ):
        create_llm_output(df, output_col_name, selected_table)
    show_output(df, output_col_name)
    
    return None

def create_llm_output(df, output_col_name, selected_table):


    # If consolidated, see if there is a column called consolidated_text_for_llm
    columns = df.columns.to_list()

    # Add SELECT to the columns
    columns = ['SELECT'] + columns
    # Default column should be text_for_llm, if it exists
    if 'text_for_llm' in columns:
        default_index = columns.index('text_for_llm')
    else:
        default_index = 0
    # Select the column to use
    selected_column = st.selectbox(
        "Select Input Column", 
        columns,
        index=default_index,
        help="This column will be used as the input to the LLM."
        )
    if selected_column == 'SELECT':
        st.error("Please select a column.")
        st.stop()
        
    # Get the system instruction
    txt_file = f"{st.session_state.project_folder}/{output_col_name}_system_instruction.txt"
    
    # Save this as the system instruction path
    st.session_state.system_instruction_path = txt_file
    system_instruction = text_areas(
        file=txt_file,
        key=f'step_by_step_{txt_file}',
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
            df[output_col_name] = np.nan
            st.sidebar.success("Prior analysis has been removed.")
            # Save the data
            df.to_parquet(selected_table, index=False)
    
    col_info = f"""This column contains the output from the LLM based on the column {selected_column}.  
    The LLM was asked to do the following:
    {system_instruction}
    """
    if st.checkbox("Show input and output cols"):
        st.markdown("*Input and output colums*")
        st.dataframe(df[[selected_column, output_col_name]])

    consolidated = row_by_row()
    
    # If row_by_row_analysis column does not exist, create it
    if output_col_name not in df.columns:
        df[output_col_name] = np.nan
    
    # Ask the user to set a fraction value on how far to reduce the text

    frac = st.number_input(
        "How big should your output be compared to input",
        min_value=0.1,
        max_value=1.0,
        value=0.3,
        step=0.1,
        help="This will be set as max tokens for the LLM."
        )
    
    c1, c2 = st.columns(2)
    # Sample or full run
    if c1.button(
        "🌓 Run a sample analysis 🌓",
        help="This will run the LLM on a sample of 3 rows.  Use this to test the LLM.",
        ):
        # Get a sample of 3 rows, if there are at least 5 rows
        if len(df) > 3:
            sample = df.sample(3)
        else:
            sample = df
        update_data_model(
            file_name=selected_table, 
            column_name=output_col_name, 
            column_type='str', 
            column_info=col_info,
            )
        # Remove prior analysis
        df[output_col_name] = np.nan
        # Save the dataframe to the destination dataframe
        # Add row by row analysis to the sample
        with st.spinner("Analyzing the sample data..."):
            sample[output_col_name] = sample[selected_column].apply(lambda x: row_by_row_llm_res(x, system_instruction, frac=frac))
            
            # Show input and output to the user
            for row in sample[[selected_column, output_col_name]].values:
                c1, c2 = st.columns(2)
                c1.subheader("Input text")
                c1.markdown(row[0], unsafe_allow_html=True)
                c2.subheader("LLM output")
                c2.markdown(row[1], unsafe_allow_html=True)
                st.markdown("---")

    if c2.button("💯 Analyze all the rows", help="This will run the LLM on rows where the output is empty."):
        remaining_rows = len(df[df[output_col_name].isna()])
        if remaining_rows == 0:
            st.success("All rows have been analyzed.")
        else:
            st.warning(f"There are {remaining_rows} rows remaining to be analyzed.")
            # Show input and output cols

            update_data_model(
                file_name=selected_table, 
                column_name=output_col_name, 
                column_type='str', 
                column_info=col_info,
            )
            # Keep sample analysis and run on the rest of the data
            with st.spinner("Analyzing the rest of the data..."):
                if consolidated:
                    # Get the full text and the res for it.  Add it to the first row.
                    full_text = df[selected_column].str.cat(sep='\n\n')
                    res_text = row_by_row_llm_res(full_text, system_instruction, frac=frac, model='gpt-3.5-turbo')
                    # res_text = '\n\n'.join(res)
                    df.iloc[0, df.columns.get_loc(output_col_name)] = res_text
                else:
                    data = df.loc[df[output_col_name].isna(), selected_column].to_list()
                    output = []
                    for row in data:
                        try:
                            res = row_by_row_llm_res(row, system_instruction, frac=frac)
                        except:
                            res = np.nan
                        output.append(res)
                    # Add the output to the dataframe
                    df.loc[df[output_col_name].isna(), output_col_name] = output

                # Save the data
                df.to_parquet(selected_table, index=False)
                st.dataframe(df[[selected_column, output_col_name]])            
    return None

def show_output(df, output_col_name):
    """
    Given the output column name, show the output
    from the LLM in markdown format.
    """

    # Show the output
    output = df[~df[output_col_name].isna()][output_col_name].to_list()
    if not output:
        st.warning("There is no output to show.  Run the analysis first.")
        st.stop()
    buf = ""
    for row in output:
        buf += row + '\n'
        # add a separator
        buf += '\n---\n'
    
    st.subheader("Output from the LLM")
    st.info(f"This information is saved in the *{output_col_name}* column.")
    st.markdown(clean_markdown(buf))
    return None

def update_data_model(file_name, column_name, column_type, column_info):
    """
    Update the data model with information about a column.

    Args:
        file_name (str): The name of the file that the column belongs to.
        column_name (str): The name of the column.
        column_type (str): The type of the column.
        column_info (str): Information about the column.
    Returns:
        None
    """
    # If the data model file exists, read it
    data_model_file = st.session_state.project_folder + '/data_model.parquet'
    if os.path.exists(data_model_file):
        data_model = pd.read_parquet(data_model_file)
    else:
        data_model = pd.DataFrame(
            columns=[
                'file_name',
                'column_name',
                'column_type',
                'column_info'
                ]
            )
    # Add the column information to the data model
    col_info = {}
    col_info['file_name'] = file_name
    col_info['column_name'] = column_name
    col_info['column_type'] = column_type
    col_info['column_info'] = column_info
    
    # Concat the data model with the col_info_df
    data_model = pd.concat([data_model, pd.DataFrame([col_info])])

    # Drop duplicates based on file name and column name, keeping the last one
    data_model = data_model.drop_duplicates(subset=['file_name', 'column_name'], keep='last')

    # Save the data model
    data_model.to_parquet(data_model_file, index=False)
    return None

def clean_markdown(text):
    """
    Remove indents and escape special markdown characters.
    """
    import re
    # Remove indents at the beginning of each line
    # Escape special characters such as $
    # text = text.replace('$', '\$')
    return text


def row_by_row_llm_res(text_or_list, system_instruction, sample=True, frac=0.3, model='gpt-3.5-turbo-16k'):

    if isinstance(text_or_list, str):
        text = text_or_list
    elif text_or_list is None:
        text = ''
    else:
        text = '\n\n'.join([str(i) for i in text_or_list])

    # Chunk the text by 10k characters
    st.session_state.last_sample = []
    if not text:
        return ""
    else:
        chunks = chunk_text(text, max_chars=20000)
        output = []
        if sample:
            chunks = chunks[:2]
        
        for chunk in chunks:
            max_tokens = len(chunk) * frac / 3
            max_tokens = int(max_tokens)
            # If max tokens is too small, make it 800
            if max_tokens < 500:
                max_tokens = 500
            messages =[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": chunk}]
            res = get_llm_output(
                input=messages,
                max_tokens=max_tokens,
                model=model
                )        
            output.append(res)
            # Add chunk and response to the last sample
            st.session_state.last_sample.append([chunk, res])
    time.sleep(3)
    return "\n".join(output)

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

def write_to_data_model(file_name, col_info_df):
    """
    Write the file information to the llm augmented data model.
    Note: All LLM generated text will have the same column names and so 
    they do not mean much.  It's critical to have the system instruction
    as a part of the data model.  In this approach, we will be able to do it.
    """
    system_instruction_path = st.session_state.system_instruction_path
    data_model_file = st.session_state.project_folder + '/data_model.parquet'
    # If the data model file exists, read it
    if os.path.exists(data_model_file):
        data_model = pd.read_parquet(data_model_file)
    else:
        data_model = pd.DataFrame(
            columns=[
                'file_name',
                'dataframe_description',
                'column_name',
                'column_type',
                'column_info'
                ]
            )

    # Add the file information to the data model
    # concat the data model with the col_info_df
    data_model = pd.concat([data_model, col_info_df])
    # Save the data model
    data_model.to_parquet(data_model_file, index=False)
    return None

def row_by_row():
    """
    Finds if the user wishes to analyze row by row or consolidated.

    Returns:
        True if row by row analysis is selected.
    """
    row_by_row_desc = """**Row by row analysis** will analyze each row separately.  This is useful if you want to summarize or extract insights from each row.
    and the output will be saved to the same row in a new column.  Use this to extract topics, specific insights, or to categorize.
    
    **In consolidated analysis**, the text from all rows will be combined and analyzed as one document.
    """
# Replace indents in each line (indents will introduce code blocks when streamlit displays the text)
    row_by_row_desc = '\n'.join([line.strip() for line in row_by_row_desc.split('\n')])    
  
    step = st.radio(
        "How would you like to analyze",
        ['Row by row', 'Consolidated'],
        
        horizontal=True,
        help=row_by_row_desc,
        )

    if step == 'Row by row':
        return False
    
    if step == 'Consolidated':
        return True