import requests
from bs4 import BeautifulSoup
import pandas as pd

class ArxivSearch:

    def __init__(self):
        pass

    def get_results(self, query, max_results=10):
        """
        Get the results from the Arxiv search
        """
        # API endpoint
        api_url = f"http://export.arxiv.org/api/query?search_query={query}&start=0&max_results={max_results}"
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
            date_of_publication = entry.published.text

            result = {
                'title': title,
                'author': authors,
                'summary': summary,
                'link': link,
                'date_of_publication': date_of_publication
            }
            results.append(result)

        df = pd.DataFrame(results)


        return df


if __name__ == "__main__":
    query = "quantum computing"
    arxiv_search = ArxivSearch(query=query)
    df = arxiv_search.get_results()
    print(df.head())