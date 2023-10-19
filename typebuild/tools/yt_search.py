import requests
from bs4 import BeautifulSoup
import json
import re
import numpy as np
from youtube_transcript_api import YouTubeTranscriptApi
import time
from youtube_search import YoutubeSearch
import streamlit as st
from datetime import datetime
import pandas as pd
import os


def get_request_with_retry_timeout(url, headers=None, params=None,
                                  cookies=None, timeout=None, max_retry=5):
    response = request_with_retry_timeout(url, headers=headers,
                                          params=params, cookies=cookies,
                                          timeout=timeout, max_retry=max_retry, 
                                          method="get")
    return response

def request_with_retry_timeout(url, session=None, data=None, headers=None, params=None, cookies=None,
                 timeout = 300, max_retry=5, method="post"):
    """This is the wrapper function for request post method."""
    retry = 0
    res = None
    sleep_timeout = 2
    response = None
    while (retry < max_retry):
        try:
            if method == "post":
                if session:
                    response = session.post(url, data=data, timeout=timeout, params=params, cookies=cookies, headers=headers)
                else:
                    response = requests.post(url, data=data, timeout=timeout, params=params, cookies=cookies, headers=headers)
            else:
                response = requests.get(url, timeout=timeout, params=params, cookies=cookies, headers=headers)
            if response.status_code == 200:
                error = False
            else:
                error = True
        except requests.Timeout:
            # back off and retry
            print("request timeout error")
            error = True
        except requests.ConnectionError:
            print("request connection error")
            error = True
        if (error == True):
            retry = retry + 1
            time.sleep(sleep_timeout)
            sleep_timeout += 5
        else:
            retry = max_retry
    return response

def fetch_youtube_video_metadata(video_id):

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

    response = get_request_with_retry_timeout(f'https://www.youtube.com/watch?v={video_id}', headers=headers)
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


def search_youtube_and_save_results(search_term, num_videos=10):

    """
    Search YouTube and save the results to a parquet file.

    Args:
    - search_term (str): The search term.
    - num_videos (int): The number of videos to return. default 10.

    Returns:
    - None: Saves the results to a parquet file. The dataframe has the following columns:
        - video_url (str): The url of the youtube video.
        - title (str): The title of the youtube video.
        - view_count (str): The view count of the youtube video.
        - like_count (str): The like count of the youtube video.
        - full_description (str): The full description of the youtube video.
        - channel (str): The channel name of the youtube video.
        - channel_link (str): The channel link of the youtube video.
        - tags (list): A list of tags mentioned on the youtube video.
        - language (str): The language of the youtube video.
        - transcript (str): The text transcript of the youtube video.
        - thumbnail (str): The thumbnail url of the youtube video.
        - search_term (str): The search term used to get the youtube video.
        - search_date (datetime): The date of the search. the format is YYYY-MM-DD
    """


    with st.status("Downloading data...", expanded=True) as status:
        st.write("Searching in YouTube...")
        time.sleep(1)
        st.write("Getting video metadata...")
        time.sleep(1)
        results = get_yt_info(search_term, max_results=num_videos)
        st.write(f"Got {len(results)} videos!")
        st.session_state.yt_info = results
        time.sleep(2)
        st.write("Data downloaded!")
        time.sleep(1)
        st.write("Saving data...")
        time.sleep(1)
        cleaned_search_term_for_filename = search_term.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '').replace(':', '').replace('.', '').replace(',', '').replace('?', '').replace('!', '').replace("'", '').replace('"', '').replace('-', '').replace('&', '').replace(';', '').replace('=', '').replace('+', '').replace('*', '').replace('$', '').replace('#', '').replace('@', '')
        # Limit the length of the filename to 500 characters
        if len(cleaned_search_term_for_filename) > 500:
            cleaned_search_term_for_filename = cleaned_search_term_for_filename[:500]
        file_name = os.path.join(st.session_state.project_folder, 'data', f'youtube_{cleaned_search_term_for_filename}.parquet')
        save_youtube_data(file_name)
        st.write(f"Data saved to {file_name}")
        status.update(label=f"Download complete!", state="complete")

def get_yt_info(search_term, max_results=10):
    results = YoutubeSearch(search_term, max_results=max_results)
    videos = results.to_dict()
    st.warning(f"Search returned {len(videos)} videos!")
    video_details = []
    for i,v in enumerate(videos):
        print(f"Starting {i}")
        video_id = v['id']
        info = fetch_youtube_video_metadata(video_id)
        # info = {**info, **v}
        info['search_term'] = search_term
        video_details.append(info)    
    return video_details

def save_youtube_data(file_name):
    if 'yt_info' not in st.session_state:
        st.stop()
    # Save the data to a parquet file
    df = pd.DataFrame(st.session_state.yt_info)
    search_term = st.session_state.yt_info[0]['search_term']
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
    search_term = st.text_input("Search YouTube")
    num_videos = st.number_input("How many videos?", min_value=1, max_value=20, value=10, step=2)
    if st.button("Search"):
        search_youtube_and_save_results(search_term=search_term, num_videos=num_videos)
    return None
