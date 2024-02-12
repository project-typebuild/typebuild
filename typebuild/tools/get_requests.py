import requests
import time
import streamlit as st

class Requests:
    """
    A class that handles HTTP GET requests with retry and timeout functionality.
    """

    def __init__(self):
        pass

    def get_request_with_retry_timeout(self, url, headers=None, params=None,
                                       cookies=None, timeout=None, max_retry=5):
        """
        Sends an HTTP GET request with retry and timeout functionality.

        Parameters:
            url (str): The URL to send the GET request to.
            headers (dict, optional): The headers to include in the request. Defaults to None.
            params (dict, optional): The query parameters to include in the request. Defaults to None.
            cookies (dict, optional): The cookies to include in the request. Defaults to None.
            timeout (float, optional): The timeout value for the request in seconds. Defaults to None.
            max_retry (int, optional): The maximum number of retries for the request. Defaults to 5.

        Returns:
            requests.Response: The response object of the GET request.
        """
        response = self.request_with_retry_timeout(url, headers=headers,
                                                   params=params, cookies=cookies,
                                                   timeout=timeout, max_retry=max_retry,
                                                   method="get")
        return response

    def post_request_with_retry_timeout(self, url, data=None, headers=None, params=None,
                                        cookies=None, timeout=None, max_retry=5):
        """
        Sends an HTTP POST request with retry and timeout functionality.

        Parameters:
            url (str): The URL to send the POST request to.
            data (dict, optional): The data to include in the request body. Defaults to None.
            headers (dict, optional): The headers to include in the request. Defaults to None.
            params (dict, optional): The query parameters to include in the request. Defaults to None.
            cookies (dict, optional): The cookies to include in the request. Defaults to None.
            timeout (float, optional): The timeout value for the request in seconds. Defaults to None.
            max_retry (int, optional): The maximum number of retries for the request. Defaults to 5.

        Returns:
            requests.Response: The response object of the POST request.
        """

        response = self.request_with_retry_timeout(url, data=data, headers=headers,
                                                   params=params, cookies=cookies,
                                                   timeout=timeout, max_retry=max_retry,
                                                   method="post")

        return response

    def request_with_retry_timeout(self, url, session=None, data=None, headers=None, params=None, cookies=None,
                                   timeout=300, max_retry=5, method="post"):
        """
        Sends an HTTP request with retry and timeout functionality.

        Parameters:
            url (str): The URL to send the request to.
            session (requests.Session, optional): The session object to use for the request. Defaults to None.
            data (dict, optional): The data to include in the request body. Defaults to None.
            headers (dict, optional): The headers to include in the request. Defaults to None.
            params (dict, optional): The query parameters to include in the request. Defaults to None.
            cookies (dict, optional): The cookies to include in the request. Defaults to None.
            timeout (float, optional): The timeout value for the request in seconds. Defaults to 300.
            max_retry (int, optional): The maximum number of retries for the request. Defaults to 5.
            method (str, optional): The HTTP method to use for the request. Defaults to "post".

        Returns:
            requests.Response: The response object of the request.
        """
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
                error = True
            except requests.ConnectionError:
                error = True
            if (error == True):
                retry = retry + 1
                time.sleep(sleep_timeout)
                sleep_timeout += 5
            else:
                retry = max_retry
        return response


def tool_main(key, url):
    """
    Given the url, this function sends an HTTP GET request to the url and returns the response content.

    Parameters:
        url (str): The URL to send the GET request to.
        key (str): A unique key that can be used to update the task, if needed.
    """
    
    # Initialize the class
    get_requests = Requests()

    response = get_requests.get_request_with_retry_timeout(url)

    res_dict = {
        'content': response.content,
        'task_finished': True,
        'ask_llm': False,
        'ask_human': False,
        'key': key,
        'task_name': st.session_state.current_task
        
    }

    return res_dict
