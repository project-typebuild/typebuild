import requests
from datetime import datetime
import pandas as pd
import streamlit as st

positionstack_api_key = st.secrets.positionstack.key

def get_latitude_and_longitude_from_location_name(location_name):
    
    """
    Forward geocoding using positionstack API. Given a location name, returns 
    ['latitude', 'longitude', 'type', 'name', 'number', 'postal_code', 'street', 'confidence', 'region', 'region_code', 'county', 'locality', 'administrative_area', 'neighbourhood', 'country', 'country_code', 'continent', 'label']

    Args:
    - location_name (str): The location name to be geocoded.

    Returns:
    - location_df (dataframe): A dataframe with geocoded location information (possible matches, the first of them).
    
    """

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }

    response = requests.get(
        f'http://api.positionstack.com/v1/forward?access_key={positionstack_api_key}&query={location_name}',
        headers=headers,
        verify=False,
    )

    json_response = response.json()

    json_response = json_response['data']

    if len(json_response) > 0:
        json_response = json_response[0]
    else:
        json_response = None
    
    # convert it to a dataframe
    location_df = pd.DataFrame(json_response, index=[0])

    search_date = str(datetime.now().date())
    location_df['search_date'] = search_date
    location_df['search_term'] = location_name

    cleaned_search_term_for_filename = location_name.replace(' ', '_').replace(',', '_').replace('.', '_').replace(';', '_').replace(':', '_').replace('?', '_').replace('!', '_').replace('(', '_').replace(')', '_').replace('/', '_').replace('\\', '_').replace('\'', '_').replace('\"', '_').replace('=', '_').replace('+', '_').replace('-', '_').replace('*', '_').replace('&', '_').replace('%', '_').replace('$', '_').replace('#', '_').replace('@', '_')
    file_name = os.path.join(st.session_state.project_folder, 'data', f'location_api_{cleaned_search_term_for_filename}.parquet')
    location_df.to_parquet(file_name, index=False)

    col_names = ['latitude', 'longitude', 'type', 'name', 'number', 
                'postal_code', 'street', 'confidence', 'region', 'region_code', 'county', 
                'locality', 'administrative_area', 'neighbourhood', 'country', 'country_code', 
                'continent', 'label', 'search_date', 'search_term']

    col_types = ['float', 'float', 'object', 'object', 'object', 'object', 
                'object', 'int', 'object', 'object', 'object', 'object', 'object', 
                'object', 'object', 'object', 'object', 'object', 'datetime', 'object']

    col_infos = ['The latitude of the location.', 'The longitude of the location.', 
                'The type of the location.', 'The name of the location.', 
                'The number of the location.', 'The postal code of the location.', 
                'The street of the location.', 'The confidence of the location.', 
                'The region of the location.', 'The region code of the location.', 
                'The county of the location.', 'The locality of the location.', 
                'The administrative area of the location.', 
                'The neighbourhood of the location.', 'The country of the location.', 
                'The country code of the location.', 'The continent of the location.',
                 'The label of the location.', 'The date of the search. the format is YYYY-MM-DD', 
                 'The search term used to get the location.']

    new_data_model = pd.DataFrame({
        'column_name': col_names,
        'column_type': col_types,
        'column_info': col_infos
    })

    new_data_model['file_name'] = location_name

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

def reverse_geocoding(latitude, longitude):
        
        """
        Reverse geocoding using positionstack API. Given a latitude and longitude, gives the location name and other information such as 
        ['latitude', 'longitude', 'type', 'name', 'number', 'postal_code', 'street', 'confidence', 'region', 'region_code', 'county', 'locality', 'administrative_area', 'neighbourhood', 'country', 'country_code', 'continent', 'label']
    
        Args:
        - latitude (float): The latitude of the location to be geocoded.
        - longitude (float): The longitude of the location to be geocoded.
    
        Returns:
        - response (dict): A dictionary with the list of geocoded location information (possible matches).
        
        """
    
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        }

        response = requests.get(
            f'http://api.positionstack.com/v1/reverse?access_key={positionstack_api_key}&query={latitude},{longitude}',
            headers=headers,
            verify=False,
        )

        return response.json()

"""

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
"""