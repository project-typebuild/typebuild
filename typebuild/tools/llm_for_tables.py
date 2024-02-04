"""
# TODO: Ranu, can you test if this works on jupyter notebook?
"""

import pandas as pd
import streamlit as st
# from test_llm import get_openai_output as get_llm_output
from plugins.llms import get_llm_output
import os

def chunk_text_by_words(text, max_words):
    """
    Chunk text into chunks of max_words.
    It makes sure that sentences are not split across chunks.
    Also, adds the last sentence of the previous chunk to the next chunk.
    """

    chunks = []
    chunk = ''
    # Split the text into sentences
    sentences = text.split('.')
    # Remove empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    # Chunk the sentences
    for s in sentences:
        words_in_chunk = len(chunk.split())
        words_in_sentence = len(s.split())

        if words_in_chunk + words_in_sentence <= max_words:
            chunk += f"{s}. " if s else ""
        else:
            chunks.append(chunk)
            chunk = f"{s}. " if s else ""

    if chunk:
        chunks.append(chunk)
    
    return [c.strip() for c in chunks if c.strip()]

class LLMForTables:
    """
    Given system instruction, table name, input column and output column, 
    this runs the LLM through every row of the table and returns the output column.

    Parameters:
    - system_instruction (str): Detailed instruction on what the language model should do with the text of the input column.
    - file_name (str): file name.
    - input_column (str): The input column.
    - output_column (str): The output column.
    - max_words (int): Maximum number of words in the input.
    - input_format (str): 'row_by_row' generates one row at a time or 'consolidated' all rows into one input.
    """
    
    def __init__(self, system_instruction, file_name, input_column, output_column, max_words=10000, input_format="row_by_row"):
        self.system_instruction = system_instruction
        self.file_name = file_name
        self.input_column = input_column
        self.output_column = output_column
        self.max_words = max_words
        if input_format == "row_by_row":
            self.row_by_row = True
        else:
            self.row_by_row = False
        self._load_data()
        self.check_restart()
        self.model = "gpt-3.5-turbo-1106"

    def _save_data(self, data):
        """
        Save the data to the file.
        """
        self.data.to_parquet(self.file_name, index=False)

    def _load_data(self):
        """
        Load the data from the file.
        """
        self.data = pd.read_parquet(self.file_name)

    def check_restart(self):
        """
        Check if there is a need to restart from a specific row or chunk.
        """
        if self.output_column in self.data.columns:
            # Find the last non-empty row in the output column
            non_empty_rows = self.data[self.output_column].notnull()
            
            if non_empty_rows.any():
                self.restart_row = len(non_empty_rows)
            else:
                self.restart_row = 0
        else:
            self.data[self.output_column] = None
            self.restart_row = 0

    def run(self):
        """
        Runs the LLM on the input data and populates the output column.
        When done, saves the data to the file and returns a success message.
        """
        if self.row_by_row:
            self.process_row_by_row()
        else:
            if st.session_state.developer_options:
                st.warning("Processing chunks")
            self.process_chunks()
        content = f"LLM run successfully on {self.file_name} and created the output column {self.output_column}."
        st.success(content)
        return {
            "content": content,
            "file_name": self.file_name,
            "output_column": self.output_column
        }

    def process_row_by_row(self):
        """
        Processes the data row by row.
        """
        st.warning("Processing row by row")
        
        for i, row in enumerate(self.data.itertuples(), start=0):
            st.progress(i / len(self.data), f"Processing row {i+1} of {len(self.data)}")
            if i < self.restart_row:
                continue
            input_text = getattr(row, self.input_column)
            # If input text is none or null, go to the next row
            if not input_text:
                continue
            
            chunks = chunk_text_by_words(
                input_text, 
                max_words=self.max_words
                )
            fin_output = ""
            for c in chunks:
                messages = [
                    {"role": "system", "content": self.system_instruction},
                    {"role": "user", "content": c},
                ]
                output = get_llm_output(messages, model=self.model)
                fin_output += output + "\n"
            self.data.at[row.Index, self.output_column] = fin_output
            self._save_data(self.data)  # Save after each row
        return None
    
    def process_chunks(self):
        """
        Processes the data in chunks.
        """
        # Get the full input text
        full_text = "\n\n".join(self.data[self.input_column].dropna().tolist())
        
        # Chunk the text but skip the rows that have already been processed
        chunks = chunk_text_by_words(full_text, self.max_words)[self.restart_row:]
        # Show what has been completed so far

        for i, chunk in enumerate(chunks, start=0):
            if i < self.restart_row:
                continue
            # Create progress bar
            messages = [
                {"role": "system", "content": self.system_instruction},
                {"role": "user", "content": chunk},
            ]
            output = get_llm_output(messages, model=self.model)
            # Add the output to the correct row
            self.data.at[i, self.output_column] = output
            self._save_data(self.data)
        return None

def tool_main(system_instruction, file_name, input_column, output_column, input_format='row_by_row', auto_rerun=True):
    """
    This tool will run the LLM on the given data and populate the output column using GPT-3.5-turbo model.

    parameters:
    ----------
    system_instruction: str
        The system instruction for the LLM.
    file_name: str
        The name of the file to process.
    input_column: str
        The name of the input column.
    output_column: str
        The name of the output column.
    input_format: str
        The format of the input.  It can be row_by_row or consolidated.
    
    returns:    
    --------
    res_dict: dict
        A dictionary containing the results of the tool.    
    """

    # Each word is approximately 1.3 tokens
    # The input context for 3.5-1106 model 16,385 tokens
    # Let's make sure that the input is less than 15,000 tokens by all means
    max_words = int(15000/1.5)
    # If the data path is not there in the file, add it
    if '/data/' not in file_name:
        file_name = os.path.join(st.session_state.data_folder, file_name)
        st.success(f"File modified to: {file_name}")

    llm_for_tables = LLMForTables(
        system_instruction=system_instruction,
        file_name=file_name,
        input_column=input_column,
        output_column=output_column,
        max_words=max_words,
        input_format=input_format
    )
    res_dict = llm_for_tables.run()
    res_dict['ask_llm'] = False
    res_dict['task_finished'] = True

    return res_dict