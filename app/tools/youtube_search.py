import requests

from bs4 import BeautifulSoup

import json

import re

import numpy as np

from youtube_transcript_api import YouTubeTranscriptApi

import time


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
    
    
    ## Title and view count
    try:
        try:
            video_details['title'] = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][0]['videoPrimaryInfoRenderer']['title']['runs'][0]['text']
        except:
            video_details['title'] = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][1]['videoPrimaryInfoRenderer']['title']['runs'][0]['text']
        video_details['view_count'] = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][1]['videoPrimaryInfoRenderer']['viewCount']['videoViewCountRenderer']['viewCount']['simpleText']
        video_details['takedown'] = False
    except:
        video_details['takedown'] = True
    
    ## Like count
    try:
        try:
            video_details['like_count'] = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][0]['videoPrimaryInfoRenderer']['videoActions']['menuRenderer']['topLevelButtons'][0]['toggleButtonRenderer']['defaultText']['accessibility']['accessibilityData']['label']
        except:
            video_details['like_count'] = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][1]['videoPrimaryInfoRenderer']\
['videoActions']['menuRenderer']['topLevelButtons'][0]['segmentedLikeDislikeButtonRenderer']['likeButton']['toggleButtonRenderer']\
['defaultText']['accessibility']['accessibilityData']['label'].replace(' likes','')
    except:
        video_details['like_count'] = np.nan
    
    
    ## Description
    try:
        try:
            description = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][1]['videoSecondaryInfoRenderer']\
    ['attributedDescription']['content']
        except:
            description = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][2]['videoSecondaryInfoRenderer']\
    ['attributedDescription']['content']
        video_details['full_description'] = description
    except:
        video_details['full_description'] = ''
    
    ## Channel name and link
    try:
        try:
            video_details['channel'] = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][1]['videoSecondaryInfoRenderer']['owner']['videoOwnerRenderer']['title']['runs'][0]['text']
            video_details['channel_link'] = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][1]['videoSecondaryInfoRenderer']['owner']['videoOwnerRenderer']['title']['runs'][0]['navigationEndpoint']['browseEndpoint']['canonicalBaseUrl']
        except:
            video_details['channel'] = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][2]['videoSecondaryInfoRenderer']['owner']['videoOwnerRenderer']['title']['runs'][0]['text']
            video_details['channel_link'] = json_response['contents']['twoColumnWatchNextResults']['results']['results']['contents'][2]['videoSecondaryInfoRenderer']['owner']['videoOwnerRenderer']['title']['runs'][0]['navigationEndpoint']['browseEndpoint']['canonicalBaseUrl']
    except:
        video_details['channel'] = np.nan
        video_details['channel_link'] = np.nan
    
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
