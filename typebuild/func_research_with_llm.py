"""
Chat driven research with LLMs

- New research or do you want to view prior research?
- Select table (by showing the tables in the data folder)
- Select input column (by showing the columns in the table)
- Select output column
- Select if row by row or consolidated
- Write the system instruction
- Sample the output
- Analyze all the rows
"""


import numpy as np
import streamlit as st
from glob import glob
import os
import time
import pandas as pd
from streamlit_extras.dataframe_explorer import dataframe_explorer
from helpers import text_areas
from plugins.llms import get_llm_output

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



def research_with_llm():

    # Create a parquet file to store the research projects and the last session state
    st.session_state.research_projects_with_llm_path = os.path.join(st.session_state.project_folder, 'research_projects_with_llm.parquet')
    if not os.path.exists(st.session_state.research_projects_with_llm_path):
        res_projects = pd.DataFrame(columns=['research_name', 'project_name', 'file_name', 'input_col', 'output_col', 'word_limit', 'row_by_row', 'system_instruction'])
        res_projects.to_parquet(st.session_state.research_projects_with_llm_path, index=False)
        st.rerun()

    res_projects = pd.read_parquet(st.session_state.research_projects_with_llm_path)
    # Select only projects with current project name
    res_projects = res_projects[res_projects['project_name'].str.contains(st.session_state.project_folder.strip())]
    st.session_state.res_projects = res_projects
    # Get all the research projects from the research_projects_with_llm.parquet file
    all_research = res_projects['research_name'].unique().tolist()
    all_research.insert(0, 'New Research')
    # Insert 'SELECT' at the beginning
    all_research.insert(0, 'SELECT')

    default_index = 0
    if 'new_research' in st.session_state:
        default_index = all_research.index(st.session_state.new_research)
        del st.session_state.new_research
    
    research_name = st.selectbox(
        "Select research or create new", 
        all_research,
        index=default_index,
        help="Select new research to create a new research project.  Select view prior research to view prior research projects.",
        key='research_name'
        )

    if research_name == 'SELECT':
        st.error("Please select a research project or create a new one.")
        st.stop()

    if research_name == 'New Research':
        research_name = st.text_input(
            "Give your project a name", 
            key='new_research_name',
            help="Name your reserach so that you can find it later."
            )

        if not research_name:
            st.error("Please give your project a name and click Enter.")
            st.stop()
        elif research_name in all_research:
            st.error("This project name already exists.  Give it a different name.")
            st.stop()
        else:
            if st.button("Set name"):
                tmp_df = pd.DataFrame([{"research_name": research_name}])
                res_projects = pd.concat([res_projects, tmp_df])
                res_projects.to_parquet(st.session_state.research_projects_with_llm_path, index=False)
                st.session_state.new_research = research_name
                st.success("Set the project name")
                time.sleep(1)
                st.rerun()
    # Get the dict for the selected project
    selected_res_project = res_projects[res_projects['research_name'] == research_name].to_dict('records')[0]
    
    create_llm_output(selected_res_project)
    
    return None

def create_llm_output(selected_res_project):
    data_folder = os.path.join(st.session_state.project_folder, 'data')
    tables = glob(os.path.join(data_folder, '*.parquet'))
    # Get just the file name
    tables = [os.path.basename(table) for table in tables]
    # Remove .parquet
    tables = [os.path.splitext(table)[0] for table in tables]
    # Add SELECT to the tables
    tables.insert(0, 'SELECT')
    # Default table should be the one in the project
    default_index = 0
    expanded = True
    project_table = selected_res_project['file_name']
    # Split the file name and get just the name
    project_table = os.path.splitext(project_table)[0].split('/')[-1]
    if project_table in tables:
        default_index = tables.index(project_table)
        expanded = False

    with st.expander("Select input and output columns", expanded=expanded):
        # Select the source dataframe
        selected_table = st.selectbox(
            "Select the source data", 
            tables, 
            index=default_index,
            key=f'{st.session_state.research_name}input_table_name')

        if selected_table == 'SELECT':
            st.error("Please select a table.")
            st.stop()    
        # Get full file name
        selected_table = os.path.join(data_folder, selected_table + '.parquet')
        
        st.session_state.file_name = selected_table
        # Get the column names
        df = pd.read_parquet(selected_table)
        c1, c2 = st.columns(2)
        if st.checkbox("Show input data"):
            st.dataframe(df.head())


        columns = df.columns.to_list()
        # Select the output column
        c1, c2 = st.columns(2)


        # If consolidated, see if there is a column called consolidated_text_for_llm

        res_projects = st.session_state.res_projects
        selected_research = res_projects[res_projects['research_name'] == st.session_state.research_name].to_dict('records')[0]
        # Get all the details for this project to pre-populate the widgets
        default_output_col_name = selected_research.get('output_col', 'SELECT')
        default_input_col_name = selected_research.get('input_col', 'SELECT')
        if default_input_col_name == 'SELECT':
            if 'transcript' in columns:
                default_input_col_name = 'transcript'
            elif 'text_for_llm' in columns:
                default_input_col_name = 'text_for_llm'
            elif 'text_content' in columns:
                default_input_col_name = 'text_content'
            else:
                pass
        default_word_limit = selected_research.get('word_limit', 100)
        default_row_by_row = selected_research.get('row_by_row', True)
        st.session_state.default_row_by_row = default_row_by_row
        
        # Add SELECT to the columns
        columns = ['SELECT'] + columns
        # Default column should be text_for_llm, if it exists
        if default_input_col_name in columns:
            default_index = columns.index(default_input_col_name)
        else:
            default_index = 0
        # Select the column to use
        with c1:
            selected_column = st.selectbox(
                "Select Input Column", 
                columns,
                index=default_index,
                help="This column will be used as the input to the LLM",
                key=f'{st.session_state.research_name}input_col'
                )
            if selected_column == 'SELECT':
                st.error("Please select a column.")
                st.stop()
        with c2:
            output_col_name = select_output_col(df)        
        # Get the system instruction
        input_table_name = os.path.splitext(os.path.basename(selected_table))[0]
        txt_file = os.path.join(st.session_state.project_folder, f"{input_table_name}_{output_col_name}_sys_ins.txt")
        # Check if this file exists (old system path), else, create with the new sysetm path
        if not os.path.exists(txt_file):
            txt_file = os.path.join(st.session_state.project_folder, f"{st.session_state.input_table_name}_{output_col_name}_sys_ins.txt")
            
            
        
            
        if st.checkbox("Show input and output cols"):
            st.markdown("*Input and output colums*")
            st.dataframe(df[[selected_column, output_col_name]])

        consolidated = row_by_row()
        
        # If row_by_row_analysis column does not exist, create it
        if output_col_name not in df.columns:
            df[output_col_name] = np.nan
        
        # Ask the user to set a fraction value on how far to reduce the text
        c1, c2, c3 = st.columns(3)

        if not default_word_limit:
            default_word_limit = 100
        
        word_limit = c1.number_input(
            "What's the word limit for the response?",
            min_value=100,
            max_value=6000,
            value=int(default_word_limit),
            step=500,
            help="This will be set as max tokens for the LLM."
            )
        
    # Save this as the system instruction path
    st.session_state.system_instruction_path = txt_file
    st.subheader("Instructions for the LLM")
    st.info("Tell the LLM what you would like to do with the data we are passing from the input column.")
    system_instruction = text_areas(
        file=txt_file,
        key=f'step_by_step_{txt_file}',
        widget_label='What would you like the LLM to do in each row?'
        )

    if len(system_instruction) < 20:
        st.error(f"Please enter at leat 20 characters. {20-len(system_instruction)} more characters needed.")
        st.stop()

    col_info = f"""This column contains the output from the LLM based on the column {selected_column}.  
    The LLM was asked to do the following:
    {system_instruction}
    """
    c1, c2, c3, c4, c5 = st.columns(5)
    num_to_be_analyzed = len(df[df[output_col_name].isna()])
    num_analyzed = len(df) - num_to_be_analyzed

    if num_analyzed > 0:
        # Give option to reset prior analysis
        if st.checkbox("Delete current analysis"):
            st.info("This will remove current analysis")
            # Ask for a confirmation
            if st.button("Confirm deletion"):
                df[output_col_name] = np.nan
                st.sidebar.success("Prior analysis has been removed.")
                # Save the data
                df.to_parquet(selected_table, index=False)
    if num_to_be_analyzed > 0:
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
                sample[output_col_name] = sample[selected_column].apply(lambda x: row_by_row_llm_res(x, system_instruction, word_limit=word_limit))
                
                # Show input and output to the user
                for row in sample[[selected_column, output_col_name]].values:
                    c1, c2 = st.columns(2)
                    c1.subheader("Input text")
                    c1.markdown(row[0], unsafe_allow_html=True)
                    c2.subheader("LLM output")
                    c2.markdown(row[1], unsafe_allow_html=True)
                    st.markdown("---")

        remaining_rows = len(df[df[output_col_name].isna()])
        if remaining_rows == 0:
            st.success("All rows have been analyzed.")
        else:
            st.warning(f"There are {remaining_rows} rows remaining to be analyzed.")
            # Show input and output cols
        if c2.button("💯 Analyze all the rows", help="This will run the LLM on rows where the output is empty."):
                tmp_dict = {}
                tmp_dict['research_name'] = st.session_state.research_name
                tmp_dict['project_name'] = st.session_state.project_folder
                tmp_dict['file_name'] = st.session_state.file_name
                tmp_dict['input_col'] = selected_column
                tmp_dict['output_col'] = output_col_name
                tmp_dict['word_limit'] = word_limit
                tmp_dict['row_by_row'] = consolidated
                tmp_dict['system_instruction'] = system_instruction
                res_projects = st.session_state.res_projects
                # Filter the DataFrame to select the row(s) where 'project_name' matches the value
                update_cols = [
                    'research_name',
                    'project_name',
                    'file_name',
                    'input_col',
                    'output_col',
                    'word_limit',
                    'row_by_row',
                    'system_instruction'
                ]

                update_values = [tmp_dict[col] for col in update_cols]
                res_projects.loc[
                    (res_projects['research_name'] == st.session_state.research_name) &
                    (res_projects['project_name'] == st.session_state.project_folder), 
                    update_cols 
                    ] = update_values

                res_projects.to_parquet(st.session_state.research_projects_with_llm_path, index=False)

                
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
                        
                        res_text = row_by_row_llm_res(full_text, system_instruction, frac=frac, model='gpt-3.5-turbo-16k')
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
    show_output(df, output_col_name)

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
    
    # Allow users to download csv file
    if st.sidebar.download_button(
        label="Download full table as TSV",
        data=df.to_csv(index=False, sep='\t'),
        file_name=f"{output_col_name}.tsv",
        mime="text/plain",
        ):
        st.success("Downloaded tsv file.")
    st.subheader("Output from the LLM")
    
    st.markdown(clean_markdown(buf))
    # Allow users to download markdown file
    if st.sidebar.download_button(
        label="Download markdown file",
        data=buf,
        file_name=f"{output_col_name}.md",
        mime="text/plain",
        ):
        st.success("Downloaded markdown file.")
    
    
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
    data_model_file = os.path.join(st.session_state.project_folder, 'data_model.parquet')
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
        chunks = chunk_text(text, max_chars=8000)
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
                messages,
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
    data_model_file = os.path.join(st.session_state.project_folder, 'data_model.parquet')
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
    
    default_row_by_row_bool = st.session_state.default_row_by_row
    if default_row_by_row_bool:
        default_index = 1
    else:
        default_index = 0

    step = st.radio(
        "How would you like to analyze",
        ['Row by row', 'Consolidated'],
        index = default_index,
        horizontal=True,
        help=row_by_row_desc,
        )

    if step == 'Row by row':
        return False
    
    if step == 'Consolidated':
        return True