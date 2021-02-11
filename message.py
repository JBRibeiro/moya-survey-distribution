from requests.exceptions import HTTPError
from werkzeug.exceptions import BadRequest, InternalServerError
from requests.adapters import HTTPAdapter
import requests
from requests.packages.urllib3.util.retry import Retry
import logging

retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)


def send_message(from_number, to_number, message, api_key=None):
    try:
        headers = {
            'Authorization': 'Bearer %s' % api_key,
            'Content-Type': 'application/json'
        }
        resp = http.post(url='https://api.moya.app/v1/message', json={
            "to":"%s" % to_number,
            "recipient_type":"individual",
            "type":"text",
            "text":
                {
                    "body":"%s" % message
                }
        }, headers=headers)     
        
        _raise_response_error(resp)
        
        append_rows_to_export(output_file_name=log_filename, rows=[f'{recipient},{message},{now_str}'])
        result = {'number': to_number, 'status': resp.ok, 'message': message, 'id': resp.json().get('id')}  
        
        return result
    
    except Exception as e:
        print('Error: ' +  str(e))
    return False


def _raise_response_error(response):
    """
    Raise appropriate Werkzeug Exception if the response
    from the VoxCo API can be qualified.

    :param response: a requests.Response object.
    """

    try:
        response.raise_for_status()
    except HTTPError as e:
        if 400 <= response.status_code < 500:
            raise BadRequest(response.json()['Message'], response)
        elif 500 <= response.status_code < 600:
            raise InternalServerError(response.json()['Message'], response)
