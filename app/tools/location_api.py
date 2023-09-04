import requests

positionstack_api_key = 'f4a785fcc7ec185c12f652c4c7ef0dbb'

def forward_geocoding(location_name):
    
    """
    Forward geocoding using positionstack API. Given a location name, returns 
    ['latitude', 'longitude', 'type', 'name', 'number', 'postal_code', 'street', 'confidence', 'region', 'region_code', 'county', 'locality', 'administrative_area', 'neighbourhood', 'country', 'country_code', 'continent', 'label']

    Args:
    - location_name (str): The location name to be geocoded.

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
        f'http://api.positionstack.com/v1/forward?access_key={positionstack_api_key}&query={location_name}',
        headers=headers,
        verify=False,
    )

    return response.json()

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