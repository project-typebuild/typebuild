"""
# TODO: Ranu, can you test if this works on jupyter notebook?
"""

import pandas as pd
from plugins.llm import get_llm_output

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
    return chunks

class LLMForTables:
    """
    Given system instruction, table name, input column and output column, 
    this runs the LLM through every row of the table and returns the output column.

    Parameters:
    - system_instruction (str): The system instruction.
    - file_name (str): file name.
    - input_column (str): The input column.
    - output_column (str): The output column.
    - max_tokens (int): Maximum number of tokens to generate.
    - row_by_row (bool): Whether to generate one row at a time or consolidate all rows into one output.
    - system_instruction (str): The system instruction.
    """
    
    def __init__(self, system_instruction, file_name, input_column, output_column, max_tokens=1000, row_by_row=True):
        self.system_instruction = system_instruction
        self.file_name = file_name
        self.input_column = input_column
        self.output_column = output_column
        self.max_tokens = max_tokens
        self.row_by_row = row_by_row
        self.data = pd.read_parquet(file_name)
        self.check_restart()

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
        return {
            "content": f"LLM run successfully on {self.file_name}.",
            "file_name": self.file_name,
            "output_column": self.output_column,
            "ask_llm": False,
            "task_finished": True,
            # Add a res dict on what to do next with the output

        }

    def process_row_by_row(self):
        """
        Processes the data row by row.
        """
        for i, row in enumerate(self.data.itertuples(), start=1):
            if i < self.restart_row:
                continue
            input_text = getattr(row, self.input_column)
            output = get_llm_output(self.system_instruction, input_text, self.max_tokens)
            self.data.at[row.Index, self.output_column] = output
            self.data.to_csv(self.file_name, index=False)  # Save after each row

    def process_chunks(self):
        """
        Processes the data in chunks.
        """
        all_input_text = self.data[self.input_column].tolist()[self.restart_row:]
        chunks = chunk_text(all_input_text, self.max_tokens)

        for i, chunk in enumerate(chunks, start=self.restart_row):
            output = get_llm_output(self.system_instruction, chunk, self.max_tokens)
            output_rows = output.split('\n')  # Assuming each line corresponds to a row
            for j, output_row in enumerate(output_rows):
                if i + j >= len(self.data):
                    break
                self.data.at[i + j, self.output_column] = output_row
            self.data.to_parquet(self.file_name, index=False)  # Save after each chunk

# Usage example
# llm_table = LLMForTables("Translate the following text to French:", "data.csv", "English_Text", "French_Text")
# llm_table.run()
