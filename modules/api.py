import requests, json
import modules.log as log
try:
    from google.cloud import language
    noapi = False
except ModuleNotFoundError:  # when running from local test enviroment
    noapi = True

NER_DOMAIN = '34.64.229.136'
NER_URL = f'http://{NER_DOMAIN}:8000/ner'

logger = log.get(__name__)

def request_ner(segment_list, url=NER_URL):
    # NER 모델 요청
    ner_headers = {'Content-Type': 'application/json; charset=utf-8'}
    ner_text = ''
    try:
        for segment in segment_list:
            ner_data = json.dumps({'text': segment})
            ner_response = requests.post(url, data=ner_data, headers=ner_headers)        
            if ner_response.status_code == 200:
                ner_text += json.loads(ner_response.content.decode('unicode_escape'))['modified_text']
            else:
                logger.info('Request failed with status code:', ner_response.status_code)
                logger.info('Response content:', ner_response.text)
                ner_text = None
                break
            
    except requests.exceptions.ConnectTimeout as e:
        logger.debug(e)
        ner_text = None

    except requests.exceptions.ConnectionError as e:
        logger.debug(e)
        ner_text = None

    logger.info('Response content:', ner_text)

    # convert PS_PET to PS_NAME (별명도 이름이랑 동일한 것으로 간주)
    ner_text = ner_text.replace('[PS_PET]', '[PS_NAME]')

    return ner_text

def moderate_text(text: str):
    '''
    returns List[{'name': str, 'confidence': float}]
    '''
    if not noapi:
        client = language.LanguageServiceClient()
        document = language.Document(
            content=text,
            type_=language.Document.Type.PLAIN_TEXT,
        )
        def confidence(category: language.ClassificationCategory) -> float:
            return category.confidence
        response = client.moderate_text(document=document)
        categories = sorted(response.moderation_categories, key=confidence, reverse=True)
        return [{'name': category.name, 'confidence': category.confidence} for category in categories]
    else: 
        return None
        # test data
        # return [{'name': 'Religion & Belief', 'confidence': 0.9814285635948181}, {'name': 'Finance', 'confidence': 0.1769547313451767}, {'name': 'Legal', 'confidence': 0.17687074840068817}, {'name': 'War & Conflict', 'confidence': 0.12195122241973877}, {'name': 'Health', 'confidence': 0.1031307578086853}, {'name': 'Toxic', 'confidence': 0.10083770751953125}, {'name': 'Death, Harm & Tragedy', 'confidence': 0.08539944887161255}, {'name': 'Illicit Drugs', 'confidence': 0.05737704783678055}, {'name': 'Violent', 'confidence': 0.05284553021192551}, {'name': 'Derogatory', 'confidence': 0.05208257585763931}, {'name': 'Public Safety', 'confidence': 0.05181347206234932}, {'name': 'Insult', 'confidence': 0.04048556089401245}, {'name': 'Politics', 'confidence': 0.0346083790063858}, {'name': 'Firearms & Weapons', 'confidence': 0.0181818176060915}, {'name': 'Profanity', 'confidence': 0.01593935862183571}, {'name': 'Sexual', 'confidence': 0.00903258752077818}]
