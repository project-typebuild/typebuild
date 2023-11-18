import time
import requests
from bs4 import BeautifulSoup
import json
import re
import numpy as np
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_search import YoutubeSearch
import pandas as pd
import os
from datetime import datetime
import streamlit as st


class YouTubeDataFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.yt_info = []

    def get_request_with_retry_timeout(url, headers=None, params=None,
                                    cookies=None, timeout=None, max_retry=5):
        response = request_with_retry_timeout(url, headers=headers,
                                            params=params, cookies=cookies,
                                            timeout=timeout, max_retry=max_retry, 
                                            method="get")
        return response

    def request_with_retry_timeout(self, url, data=None, headers=None, params=None, cookies=None,
                                   timeout=300, max_retry=5, method="post"):
        """Makes a request with retry and timeout logic."""
        retry = 0
        sleep_timeout = 2
        while retry < max_retry:
            try:
                response = self.session.request(method, url, data=data, timeout=timeout, 
                                                params=params, cookies=cookies, headers=headers)
                if response.status_code == 200:
                    return response
            except (requests.Timeout, requests.ConnectionError) as e:
                print(f"Request error: {e}")
                retry += 1
                time.sleep(sleep_timeout)
                sleep_timeout += 5

    def fetch_youtube_video_metadata(self, video_id):
        """
        Fetches the metadata of a youtube video. 

        Args:
        - video_id (str): The youtube video id.

        Returns:
        - video_details (dict): A dictionary with the video metadata.
            The keys are:
            - title (str): The title of the video.
            - view_count (str): The view count of the video.
            - like_count (str): The like count of the video.
            - full_description (str): The full description of the video.
            - channel (str): The channel name of the video.
            - channel_link (str): The channel link of the video.
            - tags (list): A list of tags for the video.
            - language (str): The language of the video.
            - transcript (str): The transcript of the video.
            - thumbnail (str): The thumbnail of the video.
        """
        # This list will be passed to the transcripts function to avoid transcript not found error
        languages_list = ['af','sq','am','ar','hy','az','bn','eu','be','bs','bg','my','ca','co','hr','cs','da','nl','en','eo','et','fil','fi','fr','gl','ka','de','el','gu','ht','ha','haw','iw','hi','hmn','hu','is','ig','id','ga','it','ja','jv','kn','kk','km','rw','ko','ku','ky','lo','la','lv','lt','lb','mk','mg','ms','ml','mt','mi','mr','mn','ne','no','ny','or','ps','fa','pl','pt','pa','ro','ru','sm','gd','sr','sn','sd','si','sk','sl','so','st','es','su','sw','sv','tg','ta','tt','te','th','tr','tk','uk','ur','ug','uz','vi','cy','fy','xh','yi','yo','zu','zh-Hans','zh-Hant'] 

        headers= {
                    "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                    "Accept-Language": 'en'
                }

        if video_id.startswith('http'):
            # Using regex to extract the video id from the url
            video_id = re.findall(r'v=([^&]+)', video_id)[0]

        response = requests.get(f'https://www.youtube.com/watch?v={video_id}', headers=headers)
        soup = BeautifulSoup(response.content,'lxml')
        json_response = json.loads(response.text.split('ytInitialData =')[1].split(';</script><script nonce=')[0])
        
        video_details = {}
        video_details['video_url'] = f'https://www.youtube.com/watch?v={video_id}'
        
        ## Title and view count
        try:
            video_details['title'] = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][0]['videoPrimaryInfoRenderer']['title']['runs'][0]['text']
            video_details['view_count'] = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][0]['videoPrimaryInfoRenderer']['viewCount']['videoViewCountRenderer']['viewCount']['simpleText']
            video_details['takendown'] = False
            video_details['main_reason'] = np.nan
            video_details['subreason'] = np.nan
        except:
            video_details['takendown'] = True
            video_details['title'] = np.nan
            video_details['view_count'] = np.nan
            initital_json_response = json.loads(response.text.split('ytInitialPlayerResponse =')[1].split(';</script>')[0].strip())
            video_details['main_reason'] = initital_json_response.get('playabilityStatus', {}).get('errorScreen', {}).get('playerErrorMessageRenderer', {}).get('reason', {}).get('simpleText')
            video_details['subreason'] = initital_json_response.get('playabilityStatus', {}).get('errorScreen', {}).get('playerErrorMessageRenderer', {}).get('subreason', {}).get('simpleText')

        ## Like count
        try:
            video_details['like_count'] = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][0]['videoPrimaryInfoRenderer']['videoActions']['menuRenderer']['topLevelButtons'][0]['toggleButtonRenderer']['defaultText']['accessibility']['accessibilityData']['label']
        except:
            video_details['like_count'] = np.nan
        
        ## Description
        try:
            description = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][1]['videoSecondaryInfoRenderer']\
        ['attributedDescription']['content']
        except:
            description = json_response.get('contents', {}).get('twoColumnWatchNextResults', {}).get('results', {}).get('results', {}).get('contents', [])[2].get('videoSecondaryInfoRenderer', {}).get('attributedDescription', {}).get('content', '')
        video_details['full_description'] = ''
        
        ## Channel name and link
        try:
            video_details['channel'] = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][1]['videoSecondaryInfoRenderer']['owner']['videoOwnerRenderer']['title']['runs'][0]['text']
            video_details['channel_link'] = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][1]['videoSecondaryInfoRenderer']['owner']['videoOwnerRenderer']['title']['runs'][0]['navigationEndpoint']['browseEndpoint']['canonicalBaseUrl']
        except:
            video_details['channel'] = json_response.get('contents', {}).get('twoColumnWatchNextResults', {}).get('results', {}).get('results', {}).get('contents', [{}])[2].get('videoSecondaryInfoRenderer', {}).get('owner', {}).get('videoOwnerRenderer', {}).get('title', {}).get('runs', [{}])[0].get('text')
            video_details['channel_link'] = json_response.get('contents', {}).get('twoColumnWatchNextResults', {}).get('results', {}).get('results', {}).get('contents', [{}])[2].get('videoSecondaryInfoRenderer', {}).get('owner', {}).get('videoOwnerRenderer', {}).get('title', {}).get('runs', [{}])[0].get('navigationEndpoint', {}).get('browseEndpoint', {}).get('canonicalBaseUrl')
        
        ## Tags
        try:
            tags_dict = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][0]['videoPrimaryInfoRenderer']['superTitleLink']['runs']
            tags = []
            for item in tags_dict:
                tag= item['text']
                if tag != ' ':
                    tags.append(tag)
            video_details['tags'] = tags
        except:
            video_details['tags'] = []
        
        # Language
        try:
            video_details['language'] = json_response['topbar']['desktopTopbarRenderer']['searchbox']['fusionSearchboxRenderer']['config']['webSearchboxConfig']['requestLanguage']
        except:
            video_details['language'] = np.nan
        
        ## Transcripts
        try:
            transcripts_list = YouTubeTranscriptApi.get_transcript(video_id,languages=languages_list)

            transcript = ''

            for l in transcripts_list:
                transcript += (f" {l['text']}")
            
            video_details['transcript'] = transcript
        except Exception as e:
            video_details['transcript'] = np.nan
        
        
        ## Thumbnail
        try:
            video_details['thumbnail'] = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
        except:
            video_details['thumbnail'] = np.nan

        return video_details


    def search_youtube(self, search_term, num_videos=10, output_folder="data"):
        """Searches YouTube and stores the results in the session state.

        Args:
        - search_term (str): The search term.
        - num_videos (int): The number of videos to return. Default is 10.

        Returns:
        - None: Stores the search results in the session state.
        """
        with st.spinner("Searching YouTube..."):
            # Assuming get_yt_info is a method that fetches YouTube data
            results = self.get_yt_info(search_term, max_results=num_videos)
            self.yt_info = results

    def save_search_results(self):
        """
        Saves the YouTube search results to a parquet file.

        Args:
        - search_term (str): The search term used for filename generation.

        Returns:
        - None: Saves the data to a parquet file.
        """
        with st.spinner("Saving data..."):
            cleaned_search_term = self._clean_filename(self.search_term)
            file_name = os.path.join(st.session_state.project_folder, 'data', f'youtube_{cleaned_search_term}.parquet')
            # if the folder doesn't exist, create it
            if not os.path.exists(os.path.dirname(file_name)):
                os.makedirs(os.path.dirname(file_name))
            self.file_name = file_name
            # Assuming save_youtube_data is a method that saves data to a file
            self.save_youtube_data(file_name)
            st.success(f"Data saved to {file_name}")

    @staticmethod
    def _clean_filename(search_term):
        """
        Cleans the search term to be used as a filename.

        Args:
        - search_term (str): The search term.

        Returns:
        - str: A cleaned string suitable for a filename.
        """
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '', search_term)
        return cleaned[:500]  # Limit the length of the filename to 500 characters

    def get_yt_info(self, search_term, max_results=10):
        """Gets detailed information for a list of YouTube videos."""
        self.search_term = search_term
        results = YoutubeSearch(search_term, max_results=max_results)
        videos = results.to_dict()
        st.warning(f"Search returned {len(videos)} videos!")
        video_details = []
        for i,v in enumerate(videos):
            print(f"Starting {i}")
            video_id = v['id']
            info = self.fetch_youtube_video_metadata(video_id)
            # info = {**info, **v}
            info['search_term'] = search_term
            video_details.append(info)    
        return video_details

    def save_youtube_data(self, file_name):
        # Method implementation...
        if not self.yt_info:
            st.stop()
        # Save the data to a parquet file
        df = pd.DataFrame(self.yt_info)

        # Add the search data to the data model
        search_date = str(datetime.now().date())
        df['search_date'] = search_date

        df.to_parquet(file_name, index=False)

        col_names = ['video_url', 'title', 'view_count', 'like_count', 'full_description',
            'channel', 'channel_link', 'tags', 'language', 'transcript',
            'thumbnail', 'search_term', 'search_date']

        col_types = ['object', 'object', 'object', 'object', 'object', 'object', 'object', 'object', 'object', 'object', 'object', 'object', 'datetime']

        col_infos = ['The url of the youtube video.', 'The title of the youtube video.',
                    'The view count of the youtube video.', 'The like count of the youtube video.', 
                    'The full description of the youtube video.', 'The channel name of the youtube video.',
                    'The channel link of the youtube video.', 'A list of tags mentioned on the youtube video.',
                    'The language of the youtube video.', 'The text transcript of the youtube video.', 
                    'The thumbnail url of the youtube video.', 'The search term used to get the youtube video.',
                        'The date of the search. the format is YYYY-MM-DD']

        new_data_model = pd.DataFrame({
            'column_name': col_names, 
            'column_type': col_types, 
            'column_info': col_infos
            })
        new_data_model['file_name'] = file_name
        # Save the data model to the project folder, append to the existing data model
        data_model_file = os.path.join(st.session_state.project_folder, 'data_model.parquet')
        all_dfs = []
        if os.path.exists(data_model_file):
            current_model = pd.read_parquet(data_model_file)
            all_dfs.append(current_model)
            all_dfs.append(new_data_model)
            df_all_col_infos = pd.concat(all_dfs)
            df_all_col_infos.to_parquet(data_model_file, index=False)
        else:
            new_data_model.to_parquet(data_model_file, index=False)
        return None



def main():
    fetcher = YouTubeDataFetcher()  # Create an instance of the YouTubeDataFetcher class

    search_term = st.text_input("Search YouTube")
    num_videos = st.number_input("How many videos?", min_value=1, max_value=20, value=10, step=2)

    if st.button("Search"):
        # Use the class method to perform the search and save results
        fetcher.search_youtube(search_term=search_term, num_videos=num_videos)
        # Save the results to a parquet file
        fetcher.save_search_results()
    return None

def tool_main(search_term, num_results=10):
    """
    Given a search term, this fetches the youtube transcripts.
    The transcripts are saved to a parquet file and the file path is returned.
    
    Parameters:
    - search_term (str): The search term.
    - num_results (int): The number of results to return. Default is 10.

    Returns (str):
    - Path to the parquet file where the results are saved.
    """

    fetcher = YouTubeDataFetcher()  # Create an instance of the YouTubeDataFetcher class

    # Use the class method to perform the search and save results
    fetcher.search_youtube(search_term=search_term, num_videos=num_results)
    # Save the results to a parquet file
    fetcher.save_search_results()
    return fetcher.file_name
