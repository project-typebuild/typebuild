import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import streamlit as st
from PyPDF2 import PdfReader
from glob import glob
from datetime import datetime


class ArxivSearch:

    def __init__(self):
        pass

    def _download_article_pdf(self, url):
        """
        Get the full text of the paper from the Arxiv URL
        """
        pdf_url = self._convert_url_to_pdf_url(url)
        response = requests.get(pdf_url)
        tmp_folder = os.path.join(st.session_state.project_folder, 'documents','arxiv')
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)
        file_name = os.path.join(tmp_folder, pdf_url.split('/')[-1])
        with open(file_name, 'wb') as f:
            f.write(response.content)

        return file_name

    def _get_full_text_of_paper(self, url):
        """
        Get the full text of the paper from the Arxiv URL, the arxiv url will be converted to the pdf url and the pdf will be downloaded

        Parameters:

            url (str): The Arxiv URL of the paper

        Returns:

            str: The full text of the paper

        """

        # read the pdf and get the text
        file_name = self._download_article_pdf(url)
        reader = PdfReader(file_name, 'rb')

        number_of_pages = len(reader.pages)

        full_text = ''
        for page in reader.pages:
            full_text +=  page.extract_text()

        # remove the file
        os.remove(file_name)
        return full_text

    def _convert_url_to_pdf_url(self, url):
        """
        Convert the Arxiv URL to the PDF URL
        """
        pdf_url = url.replace('abs', 'pdf')
        pdf_url += '.pdf'
        return pdf_url

    def get_results(self, search_term, max_results=10, start=0, sort_by='relevance', sort_order='descending'):
        """
        Get the results from the Arxiv search

        Parameters:
            search_term (str): The search query.
            max_results (int): Maximum number of results to return. Default is 10.
            start (int): The index of the first result to return. Default is 0.
            sort_by (str): The field to sort by. Default is 'relevance'. Options are 'relevance', 'lastUpdatedDate', 'submittedDate'.
            sort_order (str): The sort order. Default is 'descending'. Options are 'descending', 'ascending'.

        Returns:
            pandas.DataFrame: A DataFrame containing the search results.
        """
        # API endpoint
        api_url = f"http://export.arxiv.org/api/query?search_query={search_term}&start=0&max_results={max_results}&sortBy={sort_by}&sortOrder={sort_order}"
        # Get the response
        response = requests.get(api_url)
        # Get the content
        content = response.content
        # Parse the content
        soup = BeautifulSoup(content, 'xml')

        # Get the entries
        entries = soup.find_all('entry')
        # Get the results
        results = []
        for entry in entries:
            title = entry.title.text
            authors = [author.find('name').text for author in entry.find_all('author')]
            summary = entry.summary.text
            link = entry.link['href']
            full_text = self._get_full_text_of_paper(link)
            date_of_publication = entry.published.text
            result = {
                'title': title,
                'author': authors,
                'summary': summary,
                'link': link,
                'date_of_publication': date_of_publication,
                'full_text': full_text
            }
            results.append(result)

        df = pd.DataFrame(results)
        # Get the results and add the search term and date
        df['search_term'] = search_term
        df['search_date'] = pd.to_datetime(datetime.now())


        return df

    def _get_results_as_string(self, search_term, max_results=10):

        """
        Get the results from the Arxiv search as a string
        """
        df = self.get_results(search_term, max_results=max_results)
        
        result_text = ""
        for i, row in df.iterrows():
            result_text += f"[{row['title']}]({row['link']})\n\n{row['summary']}\n\n"

        return result_text

    def display_results(self, df):

        # In markdown formatm, with title, link and summary
        # Add a checkbox to download the full text of the papers
        for i, row in df.iterrows():
            st.markdown(f"[{row['title']}]({row['link']})")
            st.write(row['summary'])
            # display the pdf url
            pdf_url = self._convert_url_to_pdf_url(row['link'])
            st.write(f"[Click here to read full paper]({pdf_url})")

            st.write('---')
        return None

    def _clean_search_term_for_filename(self, search_term):
        """
        Clean the search term for use in a file name
        """
        return search_term.replace(' ', '_').replace('/', '_'). \
            replace('\\', '_').replace(':', '_').replace('*', '_'). \
            replace('?', '_').replace('"', '_').replace('<', '_'). \
            replace('>', '_').replace('|', '_')

    def store_to_db(self, df, search_term):
        """
        Save the results to a Parquet file
        """
        project_folder = st.session_state.project_folder

        cleaned_search_term_for_filename = self._clean_search_term_for_filename(search_term)
        file_name = os.path.join(project_folder, 'data', f'arxiv_{cleaned_search_term_for_filename}.parquet')
        df.to_parquet(file_name, index=False)

        return file_name

    
    def _get_file_name(self):
        """
        Get the name of the saved Parquet file
        """
        return self.file_name

    def arxiv_interface(self):

        # Check what field the user wants to search in arxiv. Default is all fields. List out the options according to the arxiv API

        # Create a mapping between the arxiv API fields and the user friendly fields

        arxiv_fields = {
            'All fields': 'all',
            'Title': 'ti',
            'Author': 'au',
            'Abstract': 'abs',
            'Comment': 'co',
            'Journal reference': 'jr',
            'Subject category': 'cat',
            'Report number': 'rn',
            'Identifier': 'id',
        }

        # Get all arxiv parquet files in the data folder
        project_folder = st.session_state.project_folder
        data_folder = os.path.join(project_folder, 'data')
        
        arxiv_files = glob(os.path.join(data_folder, 'arxiv_*.parquet'))

        if 'arxiv_search_results' not in st.session_state:
            # Read the files and get the search terms
            search_terms = []
            for file in arxiv_files:
                df = pd.read_parquet(file)
                search_terms.extend(df['search_term'].unique().tolist())

            search_terms.insert(0, 'New search term')
            st.session_state.arxiv_search_results = search_terms

        search_terms = st.session_state.arxiv_search_results
        if 'arxiv_results' not in st.session_state:
            st.write('No results to display')
        with st.expander('Search Arxiv', expanded=True):
            c1, c2 = st.columns(2)

            # Let the user choose the search term
            search_term = c1.selectbox('Select search term', search_terms)

            if search_term == 'New search term':
                search_term = c1.text_input('Enter search term')
                if not search_term:
                    st.warning('Please enter a search term and click enter')
                    st.stop()
                # replace spaces with +
                search_term = search_term.replace(' ', '+')

            # Let the user choose the field to search in
            search_field = c2.selectbox('Select field to search in', list(arxiv_fields.keys()))

            # Get the number of results to return
            max_results = c1.number_input('Select number of results to return', min_value=1, max_value=100, value=10)

            arxiv_query = f"{arxiv_fields[search_field]}:{search_term}"

            sort_by = c2.selectbox('Sort by', ['relevance', 'lastUpdatedDate', 'submittedDate'])

            sort_order = c2.selectbox('Sort order', ['descending', 'ascending'])

            st.session_state.arxiv_results = None
            if st.button('Get results'):
                with st.spinner('Getting results...'):
                    # Perform the Arxiv search
                    df_results = self.get_results(arxiv_query, max_results=max_results, sort_by=sort_by, sort_order=sort_order)
                    st.dataframe(df_results)
                    st.session_state.arxiv_results = df_results


        if st.session_state.arxiv_results is not None:
            # Display the results
            self.display_results(st.session_state.arxiv_results)
            if st.button('Save results'):
                with st.spinner('Saving results...'):
                    file_name = self._clean_search_term_for_filename(search_term)
                    # Save results to a Parquet file
                    self.store_to_db(df_results, project_folder=st.session_state.project_folder, file_name=file_name)


def tool_main(search_term, num_results=5, auto_rerun=False):
    """
    Given the search term, this function will search and fetch results from Arxiv. 
    the results will be saved to disk as a parquet file with the following columns:
    title, author, summary, link, date_of_publication, full_text, search_term, search_date
    
    Parameters:
        search_term (str): The search query.
        num_results (int): Maximum number of results to return. Default is 5.

    Returns:
        res_dict (dict): A dictionary containing the following keys:
            content (str): A message to display to the user.
            file_name (str): The name of the file where the results are saved.
            ask_llm (bool): Whether to ask the user to use the LLM model.
            task_finished (bool): Whether the task is finished.
    """
    arxiv_search = ArxivSearch()
    df = arxiv_search.get_results(search_term, max_results=num_results)
    arxiv_search.display_results(df)
    file_name = arxiv_search.store_to_db(df, search_term= search_term)

    res_dict = {
        'content': f"The arxiv search results can be found in {file_name} file.  It includes title, summary, author, and full_text columns.",
        'file_name': file_name,
        'ask_llm': True,
        'task_finished': True,
    }
    st.success(f"Data saved to {file_name}")

    return res_dict