"""
# TODO: Ranu, can you test if this works on jupyter notebook?
"""

import pandas as pd
import streamlit as st
# from test_llm import get_openai_output as get_llm_output
from plugins.llms import get_llm_output

def chunk_text(text, max_chars):
    """
    Chunk text into chunks of max_chars.
    It makes sure that sentences are not split across chunks.
    Also, adds the last sentence of the previous chunk to the next chunk.
    """

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
    return [c for c in chunks if c.strip()]

class LLMForTables:
    """
    Given system instruction, table name, input column and output column, 
    this runs the LLM through every row of the table and returns the output column.

    Parameters:
    - system_instruction (str): Detailed instruction on what the language model should do with the text of the input column.
    - file_name (str): file name.
    - input_column (str): The input column.
    - output_column (str): The output column.
    - max_tokens (int): Maximum number of tokens to generate.
    - row_by_row (bool): Whether to generate one row at a time or consolidate all rows into one output.
    """
    
    def __init__(self, system_instruction, file_name, input_column, output_column, max_tokens=750, row_by_row=True):
        self.system_instruction = system_instruction
        self.file_name = file_name
        self.input_column = input_column
        self.output_column = output_column
        self.max_tokens = max_tokens
        self.row_by_row = row_by_row
        self._load_data()
        self.check_restart()
        self.model = "gpt-3.5-turbo"

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
                self.restart_row = non_empty_rows.idxmax() + 1
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
            self.process_chunks()
        content = f"LLM run successfully on {self.file_name} and created the output column {self.output_column}."
        return {
            "content": content,
            "file_name": self.file_name,
            "output_column": self.output_column
        }

    def process_row_by_row(self):
        """
        Processes the data row by row.
        """
        for i, row in enumerate(self.data.itertuples(), start=1):
            if i < self.restart_row:
                continue
            input_text = getattr(row, self.input_column)
            # If input text is none or null, go to the next row
            if not input_text:
                continue
            # Set chunk size to be twice the max tokens.  
            # since chunks are inputs while max tokens is the output
            # Each token is approximately 3 characters long.
            chunks = chunk_text(
                input_text, 
                max_chars=self.max_tokens * 2 * 3
                )
            fin_output = ""
            for c in chunks:
                messages = [
                    {"role": "system", "content": self.system_instruction},
                    {"role": "user", "content": c},
                ]
                # output = get_llm_output(messages, self.max_tokens)
                output = get_llm_output(messages, self.max_tokens, model=self.model)
                fin_output += output + "\n"
            self.data.at[row.Index, self.output_column] = fin_output
            self._save_data(self.data)  # Save after each row
        return None
    
    def process_chunks(self):
        """
        Processes the data in chunks.
        """
        # Get the full input text
        full_text = "\n\n".join(self.data[self.input_column].tolist())
        
        # Chunk the text but skip the rows that have already been processed
        chunks = chunk_text(full_text, self.max_tokens * 2)[self.restart_row:]
        print(f"Number of chunks: {len(chunks)}")

        for i, chunk in enumerate(chunks, start=self.restart_row):
            messages = [
                {"role": "system", "content": self.system_instruction},
                {"role": "user", "content": chunk},
            ]
            output = get_llm_output(messages, self.max_tokens, model=self.model)
            # Add the output to the correct row
            self.data.at[i, self.output_column] = output
            self._save_data(self.data)
        return None

def tool_main(system_instruction, file_name, input_column, output_column, auto_rerun=False):
    """
    This tool will run the LLM on the given data and populate the output column.
    Uses GPT-3.5-turbo model.
    """
    
    llm_for_tables = LLMForTables(
        system_instruction=system_instruction,
        file_name=file_name,
        input_column='transcript',
        output_column=output_column,
        max_tokens=700,
    )
    res_dict = llm_for_tables.run()
    res_dict['ask_llm'] = False
    res_dict['task_finished'] = True

    return res_dict