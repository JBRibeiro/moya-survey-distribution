import requests
from requests.exceptions import HTTPError
import uuid
import time
import pprint
import logging
import traceback
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import hashlib 
import datetime
import pprint
from message import send_message

retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

# API Token of the client
API_USER_TOKEN = 'SHOOyR25g56isgbY-gemdu5imniIg1iUloyn3gaIxdCE_f932AtuACUHAUxwd4Hr'
VOXCO_TOKEN = 'EsE5Gr9AwTBXFeibgFiswbfBwhPDx64jfFv6ZxUCH/LPdlX5FiSAT9LVRgzKBuKZsGiF9okR7TOqeirf7ET2TBJ50Q26R6JNiSlyUX/ZK3oBcIE12RbeEg=='
BASE_URL = 'https://survey.moyaresearch.co/api/'
MOYA_PANEL_TOKEN = 'U6rATbtgolwPOeHX7L23iRxj36JxVXWCKK73Ccq9AZwoRr_SsMhlXJcBfqC3X1rz'

headers = {
    'Authorization': 'Client %s' % VOXCO_TOKEN,
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

log = []
total_contacts = 0

def get_respondents(survey_id, page):
    try:
        # time.sleep(60)       
        resp = http.get(
            url = BASE_URL + 'respondents/%s/Get?pageStart=%s' % (survey_id, page), 
            headers=headers
        )
        resp.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')  # Python 3.6
    except Exception as err:
        print(f'Other error occurred: {err}')  # Python 3.6
    else:
        print('Success!')
        return(resp.json())


def get_respondent_name(panelist_id, survey_id):
    try:
        name = None
        # time.sleep(60)
        resp = http.get(
            url = BASE_URL + 'respondent/answer/%s?respondentId=%s' % (survey_id, panelist_id),
            headers=headers
        )
        # If the response was successful, no Exception will be raised
        resp.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')  # Python 3.6
    except Exception as err:
        print(f'Other error occurred: {err}')  # Python 3.6
    else:
        print('Success!')
        try:
            for var in resp.json():
                if var.get('VariableName') == 'FIRSTNAME':
                    matrices = var.get('Matrices')
                    # print(matrices)
                    # print(matrices[0])
                    # print(matrices[0].get('Mentions'))
                    name = var.get('Matrices')[0].get('Mentions')[0].get('Value')
                    if name:
                        name = name.lower().capitalize()
        except:
            name = 'Dear'
    return name


def append_rows_to_export(output_file_name, rows):
    # Open file in append mode
    with open('files/'+output_file_name, 'a+', newline='') as write_obj:    
        for row in rows:
            print(row, file=write_obj)


def message_all_respondents(
    greeting, message, mode,
    survey_id, survey_link_public, 
    output_file_name, simulate=False):
    '''
    Iterate over pages of respondents.
    Per page, send a message to each unique respondent individually, with a unique survey link.
    '''
    total_count = 0
    respondents_batch = []
    finished_respondents = False
    page = 0
    logs = []
    respondent_number = 0
    MOYA_PANEL_NUMBER = '27837962219'

    while not finished_respondents:
        print('Getting respondents batch #%s' % str(int(page / 100 + 1)))
        respondents_batch = get_respondents(survey_id=survey_id, page=page)
        
        if respondents_batch is not None:
            print('Fetched another %s respondents' % len(respondents_batch))
            pprint.pprint(respondents_batch)
            
            for respondent in respondents_batch:
                # Send message to each user including link
                name = get_respondent_name(
                    respondent.get('Id'), survey_id=survey_id
                )
                if name:
                    name = name.lower().capitalize()
                else:
                    name = 'Dear Moya User'
                    
                if not simulate:
                    if not respondent.get('Phone'):
                        print("No phone num, skipping")
                        continue # nothing to do without a phone no
                    if respondent.get('Phone'):
                        respondent_number = respondent.get('Phone')
                    
                    if mode == 1:
                        id_parameter = str(respondent.get('Pin'))
                    elif mode == 2:
                        id_parameter = str(hash(respondent.get('Phone')))
                    else:
                        raise ValueError(f'Unsupported choice for mode: {mode}. Please re-run, selecting a valid mode option (1 0r 2).')
                        
                    formatted_message =greeting + ' ' + name + '! ' + message + ' \n%s' % survey_link_public + '&p=' + id_parameter
                    
                    log = send_message(
                        to_number=respondent_number, 
                        message=formatted_message, 
                        from_number=MOYA_PANEL_NUMBER,
                        api_key=MOYA_PANEL_TOKEN
                    )

                    now_str = datetime.datetime.now().strftime('%d%b%Y%H%M') 
                    append_rows_to_export(output_file_name=output_file_name,rows=[f'{respondent_number},{message},{now_str}'])
                    print(log)
                    # print(respondent_number)
                    print(now_str)
                    print(formatted_message)
                    
                    name = None
                    formatted_message = None
                    id_parameter = None
                else:
                    pin = respondent.get('Pin') if respondent.get('Pin') else str(0)
                    print('Simulating message send to %s: %s' % (
                            respondent.get('Phone'), 
                            greeting + ' ' + name + '! ' + message + ' \n%s' % survey_link_public + '&p=' + pin
                        )
                    )
            total_count += len(respondents_batch)
            finished_respondents = len(respondents_batch) == 0
            page += 100
    return logs if not simulate else ['test run']


def run():
    """
    Pseudocode:
    - get survey number and message from user
    - get batch of 100 respondents (confirm max page size using insomnia)
    - for each respondent, create a survey link using forumula {{general link}} + &p= + {{Pin}}
    """
    results = None
    try:
        print('NB: Please ensure that the API_USER_TOKEN is set correctly.') # TODO: replace this with a check against the support service.
        print('Are we running a VoxCo survey or a 3rd party one? ')
        mode = int(input('Please enter 1 for VoxCo or 2 for third party > '))
        survey_id = input('Please enter the survey ID > ')
        survey_link_public = input('Please enter the survey link > ')
        greeting = input('Please enter the greeting that you would like to use. E.g. Hello > ')
        message = input('Please enter the message that needs to be sent to the panelists > ')
        simulate = False
        
        # Name output file meaningfully.
        now_str = datetime.datetime.now().strftime('%d%b%Y%H%M')
        output_file_name = f'Moya_Survey_Distribution_Log_Survey_{survey_id}_{now_str}.csv'

        results = message_all_respondents(
            output_file_name=output_file_name,
            mode=mode,
            greeting=greeting.lower().capitalize(),
            message=message, 
            survey_id=survey_id, 
            survey_link_public=survey_link_public,
            simulate=simulate
        )

        return results
    except Exception as e:
        logging.error(str(e))
        traceback.print_exc()
        return results

run()
