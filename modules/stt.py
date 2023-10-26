import whisper_timestamped as whisper
import re
import json

import modules.audio as audio
import modules.log as log

# 로거 설정
logger = log.get(__name__)
log.set_level(__name__, "i")
i, d = logger.info, logger.debug

def transcribe(file):
    """
    https://github.com/linto-ai/whisper-timestamped
    whisper_timestamped 이용해서 오디오 파일을 텍스트로 변환한다.

    :param file: 오디오 파일 경로
    """
    audio = whisper.load_audio(file)
    model = whisper.load_model("base", device="cpu")
    return whisper.transcribe(model, audio, language="ko")


def get_stt(filename):
    '''
    converts audio to stt and returns text and word list
    '''
    try:
        # STT 변환 실행
        result = transcribe(filename)
        i(f'Converted {filename} to text')

        # 'text' 부분만 추출하여 반환
        text = result.get('text', '')  # 'text' 키가 없을 경우 빈 문자열 반환

        segment_list = []  # for ner
        word_list = []  # for getting mask
        for segment in result.get('segments'):
            word_list.extend(segment['words'])
            segment_list.append(segment['text'])
    except Exception as e:
        d(e)

    return text, word_list, segment_list

def has_mask(word: str):
    """
    input a single str and tests if it is a masking token
    """
    pattern = r"^\[.*\]$"
    return bool(re.match(pattern, word))

def get_mask_times(word_list, masked_list):
    """
    get masked times from stt word list and ner masked text list

    return None if list elements have different lengths
    """
    if len(word_list) != len (masked_list):  # error handling done by caller
        return None
    
    mask_times = []
    previous_mask = False
    for word_data, word in zip(word_list, masked_list):
        if has_mask(word):  # is masked word
            if previous_mask:  # previous word was also a mask
                mask_times[-1][-1] = word_data['end']  # update end time of last timeframe
            else:
                mask_times.append([word_data['start'], word_data['end']])
            previous_mask = True

        else:
            previous_mask = False

    return mask_times    
    
def decode_text(txt):
    return bytes(txt, "utf-8").decode("unicode_escape")