import requests, json
import modules.log as log

NER_DOMAIN = '34.64.229.136'
NER_URL = f'http://{NER_DOMAIN}:8000/ner'

logger = log.get(__name__)

def request_ner(text, url=NER_URL):
    # NER 모델 요청
    ner_data = json.dumps({'text': text})
    ner_headers = {'Content-Type': 'application/json; charset=utf-8'}

    try:
        ner_response = requests.post(url, data=ner_data, headers=ner_headers)        
        if ner_response.status_code == 200:
            ner_text = json.loads(ner_response.content.decode('unicode_escape'))['modified_text']
            logger.info('Response content:', ner_text)
        else:
            logger.info('Request failed with status code:', ner_response.status_code)
            logger.info('Response content:', ner_response.text)
            ner_text = None
            
    except requests.exceptions.ConnectTimeout as e:
        logger.debug(e)
        ner_text = None

    except requests.exceptions.ConnectionError as e:
        logger.debug(e)
        ner_text = None

    return ner_text