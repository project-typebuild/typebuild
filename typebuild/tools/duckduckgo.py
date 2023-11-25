from duckduckgo_search import DDGS
import streamlit as st
from datetime import datetime
import requests
import tldextract
from bs4 import BeautifulSoup
import pandas as pd
import os
import time


class DuckDuckGo:

    def __init__(self):
        self.results = []
        self.file_name = None
    
    def get_ddg_search_results(self, search_term, num_results=1, full_text=False):
        """
        Perform a DuckDuckGo search and store the results.

        Args:
        - search_term (str): The search term.
        - num_results (int): Maximum number of results to return. Default is 1.
        - full_text (bool): Whether to retrieve the full text of the page. Default is False.

        Returns:
        - List of dictionaries containing search results.
        """
        with DDGS() as ddgs:
            time.sleep(2)
            results = [r for r in ddgs.text(search_term, max_results=num_results)]
        result_text = ""
        for result in results:
            result_text += f"[{result['title']}]({result['href']})\n\n{result['body']}\n\n"
            if full_text:
                try:
                    content = requests.get(result['href'], timeout=timeout).content
                    page_content = BeautifulSoup(content).get_text()
                    self.results.append({
                        'url': result['href'],
                        'title': result['title'],
                        'description': result['body'],
                        'text_content': page_content,
                        'domain': tldextract.extract(result['href']).domain
                    })
                except requests.exceptions.Timeout:
                    st.write(f"Request to {result['href']} timed out.")
            # Add result text to instance var
        self.result_text = result_text
        # return results


    def get_results_as_list(self):
        """
        Retrieve the stored search results as a list.

        Returns:
        - List of dictionaries containing search results.
        """
        return self.results

    def get_results_as_string(self):
        """
        Retrieve the stored search results as a string.

        Returns:
        - String representation of search results.
        """
        return "\n".join([str(result) for result in self.results])


    def store_to_db(self, search_term, project_folder):
        """
        Save the stored results to a Parquet file.

        Args:
        - search_term (str): The search term used.
        - project_folder (str): The project folder to save the file in.
        """
        df_results = pd.DataFrame(self.results)
        df_results['search_term'] = search_term
        df_results['search_date'] = pd.to_datetime(datetime.now())

        cleaned_search_term_for_filename = self._clean_search_term_for_filename(search_term)
        self.file_name = os.path.join(project_folder, 'data', f'ddg_{cleaned_search_term_for_filename}.parquet')
        df_results.to_parquet(self.file_name, index=False)

    def get_file_name(self):
        """
        Retrieve the name of the saved Parquet file.

        Returns:
        - String: Name of the saved Parquet file.
        """
        return self.file_name

    @staticmethod
    def _clean_search_term_for_filename(search_term):
        """
        Clean the search term to be used in a file name.

        Args:
        - search_term (str): The search term.

        Returns:
        - String: Cleaned search term suitable for use in a file name.
        """
        cleaned = ''.join(e for e in search_term if e.isalnum() or e in ['_'])
        return cleaned[:500]  # Limit the length to 500 characters



    def ddg_search_interface(self):

        search_term = st.text_input('Enter search term')
        num_results = st.number_input('Enter number of results', min_value=1, max_value=50, value=10)

        if st.button('Get results'):
            with st.spinner('Getting results...'):
                # Perform the Google search
                self.get_ddg_search_results(search_term, num_results=num_results)
                # Save results to a Parquet file
                st.session_state.project_folder = 'tmp'
                self.store_to_db(search_term, project_folder=st.session_state.project_folder)

                # Retrieve and display the file name where results are saved
                file_name = self.get_file_name()
                st.success('Done.')
                st.write('Results saved to parquet file.')
                st.write(f"Data saved to {file_name}")
        return None


def tool_main(search_term, num_results=1, full_text=False):
    """
    This tool performs a DuckDukGo search and returns the
    content of the results.  All results are concatenated and returned as one string.

    Parameters:
    - search_term (str): The search term or search_term to search with.
    - num_results (int): The number of results to return.  Default is 1.
    
    Returns (str):
    - The content of the results as one string.
    """
    with st.spinner(f"Searching for {search_term}..."):
        ddg_searcher = DuckDuckGo()
        ddg_searcher.get_ddg_search_results(search_term, num_results=num_results, full_text=full_text)
        output = f"HERE ARE THE SEARCH RESULTS.  USE THIS TO ANSWER THE QUESTION:\n\n{ddg_searcher.result_text}"
        res = {
            'content': output,
            'ask_llm': True,
            'task_finished': False,
        }
        return res

