import streamlit as st
import os
import pandas as pd
import numpy as np
import time
from helpers import text_areas
import pandas as pd
import numpy as np
import streamlit as st
import os
from tqdm import tqdm
from glob import glob
from helpers import text_areas
from plugins.llms import get_llm_output

class LLMResearch:
    
    def __init__(self):
        self.project_folder = st.session_state.project_folder
        self.research_projects_with_llm_path = os.path.join(self.project_folder, 'data', 'research_projects_with_llm.parquet')
        self.res_projects = None
        self.research_name = None
        self.file_name = None
        self.default_row_by_row = None
        self.system_instruction_path = None

    def select_output_col(self, df, default_output_col_name):
        """
        Allow the user to select the output column.
        Create a new column if it does not exist.

        Args:
            df (pd.DataFrame): The dataframe to use.
        Returns:
            output_col_name (str): The name of the output column.
        """
        columns = df.columns.to_list()
        if default_output_col_name in columns:
            default_index = columns.index(default_output_col_name)
        else:
            default_index = 0
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

    def research_with_llm(self):
        self.load_research_projects()
        self.select_research_project()
        self.create_llm_output()

    def load_research_projects(self):
        if not os.path.exists(self.research_projects_with_llm_path):
            res_projects = pd.DataFrame(columns=['research_name', 'project_name', 'file_name', 'input_col', 'output_col', 'word_limit', 'row_by_row', 'system_instruction'])
            res_projects.to_parquet(self.research_projects_with_llm_path, index=False)
            st.rerun()

        res_projects = pd.read_parquet(self.research_projects_with_llm_path)
        all_research = []
        if len(res_projects) > 0:
            # Select only projects with the current project name
            res_projects = res_projects[res_projects['project_name'] == self.project_folder.strip()]
            self.res_projects = res_projects

            # Check if 'research_name' exists in the DataFrame and contains valid data
            if 'research_name' in res_projects:
                all_research = res_projects['research_name'].unique().tolist()

        all_research.insert(0, 'New Research')
        # Insert 'SELECT' at the beginning
        all_research.insert(0, 'SELECT')

        default_index = 0
        if 'new_research' in st.session_state:
            default_index = all_research.index(st.session_state.new_research)
            del st.session_state.new_research

        self.research_name = st.selectbox(
            "Select research or create new",
            all_research,
            index=default_index,
            help="Select new research to create a new research project.  Select view prior research to view prior research projects.",
            key='research_name'
        )

        if self.research_name == 'SELECT':
            st.error("Please select a research project or create a new one.")
            st.stop()

        if self.research_name == 'New Research':
            self.create_new_research_project()

    def create_new_research_project(self):
        research_name = st.text_input(
            "Give your project a name",
            key='new_research_name',
            help="Name your research so that you can find it later."
        )

        if not research_name:
            st.error("Please give your project a name and click Enter.")
            st.stop()
        elif research_name in self.res_projects['research_name'].tolist():
            st.error("This project name already exists.  Give it a different name.")
            st.stop()
        else:
            if st.button("Set name"):
                tmp_df = pd.DataFrame([
                    {
                        "research_name": research_name,
                        "project_name": self.project_folder,
                    }])
                self.res_projects = pd.concat([self.res_projects, tmp_df])
                self.res_projects.to_parquet(self.research_projects_with_llm_path, index=False)
                st.session_state.new_research = research_name
                st.success("Set the project name")
                time.sleep(1)
                st.rerun()
            else:
                st.stop()

    def select_research_project(self):
        # Get the dict for the selected project
        selected_res_project = self.res_projects[self.res_projects['research_name'] == self.research_name].to_dict('records')[0]
        self.create_llm_output(selected_res_project)

    def select_table(self, selected_res_project=None):
        data_folder = os.path.join(self.project_folder, 'data')
        tables = glob(os.path.join(data_folder, '*.parquet'))
        tables = [os.path.splitext(os.path.basename(table))[0] for table in tables]
        tables.insert(0, 'SELECT')
        default_index = 0
        project_table = selected_res_project['file_name']
        if project_table:
            project_table = os.path.splitext(os.path.basename(project_table))[0]
            if project_table in tables:
                default_index = tables.index(project_table)
                expanded = False
        selected_table = st.selectbox(
            "Select the source data",
            tables,
            index=default_index,
            key=f'{self.research_name}input_table_name')
        if selected_table == 'SELECT':
            st.error("Please select a table.")
            st.stop()
        selected_table = os.path.join(data_folder, selected_table + '.parquet')
        self.file_name = selected_table
        return selected_table

    def select_columns(self, df, selected_res_project):
        columns = df.columns.to_list()
        c1, c2 = st.columns(2)
        selected_research = self.res_projects[self.res_projects['research_name'] == self.research_name].to_dict('records')[0]
        default_output_col_name = selected_research.get('output_col', 'SELECT')
        default_input_col_name = selected_research.get('input_col', 'SELECT')
        if default_input_col_name is None:
            default_input_col_name = 'SELECT'
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
        self.default_word_limit = default_word_limit

        default_row_by_row = selected_research.get('row_by_row', True)
        self.default_row_by_row = default_row_by_row

        columns = ['SELECT'] + columns
        if default_input_col_name in columns:
            default_index = columns.index(default_input_col_name)
        else:
            default_index = 0
        with c1:
            selected_column = st.selectbox(
                "Select Input Column",
                columns,
                index=default_index,
                help="This column will be used as the input to the LLM",
                key=f'{self.research_name}input_col'
            )
            if selected_column == 'SELECT':
                st.error("Please select an input column.")
                st.stop()
        with c2:
            output_col_name = self.select_output_col(df, default_output_col_name)
        return selected_column, output_col_name

    def get_system_instruction(self, df, selected_table, output_col_name):
        input_table_name = os.path.splitext(os.path.basename(selected_table))[0]
        txt_file = os.path.join(self.project_folder, f"{input_table_name}_{output_col_name}_sys_ins.txt")
        if not os.path.exists(txt_file):
            txt_file = os.path.join(self.project_folder, f"{input_table_name}_{output_col_name}_sys_ins.txt")
        consolidated = self.row_by_row()
        if output_col_name not in df.columns:
            df[output_col_name] = np.nan
        c1, c2, c3 = st.columns(3)

        default_word_limit = self.default_word_limit
        if pd.isna(default_word_limit):
            default_word_limit = 200
        if not default_word_limit:
            default_word_limit = 200
        word_limit = c1.number_input(
            "What's the word limit for the response?",
            min_value=100,
            max_value=8000,
            value=int(default_word_limit),
            step=500,
            help="This will be set as max tokens for the LLM."
        )
        self.system_instruction_path = txt_file
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
        return system_instruction, word_limit

    def run_analysis(self, df, selected_table, selected_column, output_col_name, system_instruction, word_limit):
        col_info = f"""This column contains the output from the LLM based on the column {selected_column}.  
        The LLM was asked to do the following:
        {system_instruction}
        """
        c1, c2, c3, c4, c5 = st.columns(5)
        num_to_be_analyzed = len(df[df[output_col_name].isna()])
        num_analyzed = len(df) - num_to_be_analyzed
        if num_analyzed > 0:
            if st.checkbox("Delete current analysis"):
                st.info("This will remove current analysis")
                if st.button("Confirm deletion"):
                    df[output_col_name] = np.nan
                    st.sidebar.success("Prior analysis has been removed.")
                    df.to_parquet(selected_table, index=False)
        if num_to_be_analyzed > 0:
            if c1.button(
                "🌓 Run a sample analysis 🌓",
                help="This will run the LLM on a sample of 3 rows.  Use this to test the LLM.",
            ):
                if len(df) > 3:
                    sample = df.sample(3)
                else:
                    sample = df
                self.update_data_model(
                    file_name=selected_table,
                    column_name=output_col_name,
                    column_type='str',
                    column_info=col_info,
                )
                df[output_col_name] = np.nan
                with st.spinner("Analyzing sample data..."):
                    sample[output_col_name] = sample[selected_column].apply(lambda x: self.row_by_row_llm_res(x, system_instruction, word_limit=word_limit))
                    for row in sample[[selected_column, output_col_name]].values:
                        col1, col2 = st.columns(2)
                        col1.subheader("Input text")
                        col1.markdown(row[0], unsafe_allow_html=True)
                        col2.subheader("LLM output")
                        col2.markdown(row[1], unsafe_allow_html=True)
                        st.markdown("---")
        remaining_rows = len(df[df[output_col_name].isna()])
        if remaining_rows == 0:
            st.success("All rows have been analyzed.")
        else:
            st.warning(f"There are {remaining_rows} rows remaining to be analyzed.")
            if c2.button("💯 Analyze all the rows", help="This will run the LLM on rows where the output is empty."):
                tmp_dict = {}
                tmp_dict['research_name'] = self.research_name
                tmp_dict['project_name'] = self.project_folder
                tmp_dict['file_name'] = self.file_name
                tmp_dict['input_col'] = selected_column
                tmp_dict['output_col'] = output_col_name
                tmp_dict['word_limit'] = word_limit
                tmp_dict['row_by_row'] = consolidated
                tmp_dict['system_instruction'] = system_instruction
                res_projects = self.res_projects
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
                    (res_projects['research_name'] == self.research_name) &
                    (res_projects['project_name'] == (self.project_folder.strip())),
                    update_cols
                ] = update_values
                res_projects.to_parquet(self.research_projects_with_llm_path, index=False)
                self.update_data_model(
                    file_name=selected_table,
                    column_name=output_col_name,
                    column_type='str',
                    column_info=col_info,
                )
                with st.spinner("Analyzing the rest of the data..."):
                    if consolidated:
                        full_text = df[selected_column].str.cat(sep='\n\n')
                        res_text = self.row_by_row_llm_res(full_text, system_instruction, word_limit=word_limit)
                        df.iloc[0, df.columns.get_loc(output_col_name)] = res_text
                    else:
                        data = df.loc[df[output_col_name].isna(), selected_column].to_list()
                        output = []
                        for i, row in stqdm(enumerate(data)):
                            try:
                                res = self.row_by_row_llm_res(row, system_instruction, word_limit=word_limit)
                            except Exception as e:
                                res = np.nan
                            output.append(res)
                            df.loc[df[selected_column] == row, output_col_name] = res
                            if i % 3 == 0 and i > 0:
                                df.to_parquet(selected_table, index=False)
                                st.sidebar.info(f"Saved {i} rows.")
                df.to_parquet(selected_table, index=False)
                st.dataframe(df[[selected_column, output_col_name]])
        self.show_output(df, output_col_name)

    def create_llm_output(self, selected_res_project=None):
        selected_table = self.select_table(selected_res_project)
        df = pd.read_parquet(selected_table)
        selected_column, output_col_name = self.select_columns(df, selected_res_project)
        system_instruction, word_limit = self.get_system_instruction(df, selected_table, output_col_name)
        self.run_analysis(df, selected_table, selected_column, output_col_name, system_instruction, word_limit)

    def show_output(self, df, output_col_name):
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

        st.markdown(self.clean_markdown(buf))
        # Allow users to download markdown file
        if st.sidebar.download_button(
            label="Download markdown file",
            data=buf,
            file_name=f"{output_col_name}.md",
            mime="text/plain",
        ):
            st.success("Downloaded markdown file.")

    def update_data_model(self, file_name, column_name, column_type, column_info):
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
        data_model_file = os.path.join(self.project_folder, 'data_model.parquet')
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

    def clean_markdown(self, text):
        """
        Remove indents and escape special markdown characters.
        """
        import re
        # Remove indents at the beginning of each line
        # Escape special characters such as $
        # text = text.replace('$', '\$')
        return text

    def row_by_row_llm_res(self, text_or_list, system_instruction, sample=True, word_limit=1000, model='gpt-3.5-turbo'):

        if isinstance(text_or_list, str):
            text = text_or_list
        elif text_or_list is None:
            text = ''
        else:
            text = '\n\n'.join([str(i) for i in text_or_list])

        # Chunk the text by 8k characters for openai
        # and by 20k characters for claude
        st.session_state.last_sample = []
        if not text:
            return ""
        else:
            if 'claude' in model:
                max_chars = 50000
            else:
                max_chars = 8000

            chunks = self.chunk_text(text, max_chars=max_chars)
            output = []
            if sample:
                chunks = chunks[:2]

            for chunk in chunks:
                max_tokens = int(word_limit * 4/3)

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

    def chunk_text(self, text, max_chars=None, model_name='gpt-3.5-turbo'):
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

    def row_by_row(self):
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

        default_row_by_row_bool = self.default_row_by_row
        if default_row_by_row_bool:
            default_index = 1
        else:
            default_index = 0

        step = st.radio(
            "How would you like to analyze",
            ['Row by row', 'Consolidated'],
            index=default_index,
            horizontal=True,
            help=row_by_row_desc,
        )

        if step == 'Row by row':
            return False

        if step == 'Consolidated':
            return True