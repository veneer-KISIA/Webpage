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

        word_list = []
        for segment in result.get('segments'):
            word_list.extend(segment['words'])
    except Exception as e:
        d(e)

    return text, word_list

def has_mask_old(text):
    """
    텍스트에 마스킹된 부분이 있는지 확인한다.
    :param text: 텍스트
    """
    pattern = r"\[.*\]"  # 정규 표현식 패턴: "["로 시작하고 "]"로 끝나는 문자열
    return re.search(pattern, text) is not None

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
    

def get_mask_times_old(file):
    """
    마스킹 된 단어들의 시간 구간 리스트를 가져온다.

    :param file: whisper-timestamped에서 추출된 json 파일
    :return: [[시작1, 종료1], [시작2, 종료2], ...]] 형태의 시간구간 리스트
    """
    with open(file, encoding="utf-8") as f:
        data = json.load(f)
    # d(json.dumps(data, indent='\t'))

    # 몇가지 단어가 테스트를 위해 [MASK] 처리된 문장
    # ner_text = " 안녕? 네 이름은 홍길 동이야 현재 대한민국 경기도에 살고 있어 너는 이름이 어떻게 돼? 괜찮으면 전화번호도 말려줘 잘가?"
    # ner_text = (
    #     " 안녕? 네 이름은 [NAME]이야 현재 [LOC_COUNTRY]에 살고 있어 너는 이름이 어떻게 돼? 괜찮으면 전화번호도 말려줘 잘가?"
    # )

    ner_text = data['text'] # mask 처리된 text
    i(f"ner_text: {ner_text}")
    ner_words = ner_text.strip().split(" ")
    d(f"ner_words {ner_words}")

    segments = data["segments"]
    raw_words = [word for segment in segments for word in segment["words"]] # mask 처리 안된 text
    i(f"raw_words: {raw_words}")

    # 덮어씌울 리스트 (구조: [[시작1, 종료1], [시작2, 종료2], ...]])
    mask_times = []

    # ner_words가 1개 이상일때 까지
    while len(ner_words):
        # 같은 word 진행하다가(pop() 사용), ner_words에서 mask를 만나면,
        # 시작시간을 저장하고 raw_words에서 mask의 다음 단어를 찾을때까지 pop()
        # 찾으면 종료시간을 저장
        raw_word_info = raw_words.pop(0)
        raw_word = raw_word_info["text"]
        ner_word = ner_words.pop(0)

        i(f"raw_word: {raw_word}, ner_word: {ner_word}")

        if ner_word == raw_word:
            continue

        # [MASK]가 포함된 단어를 찾으면
        if has_mask_old(ner_word):
            i("==================== 마스크 =======================")
            i(f"mask 시작 단어: {raw_word}")
            start_time = raw_word_info["start"]
            next_ner_word = ner_words[0] if len(ner_words) else "[]"
            prev_raw_word_info = raw_word_info
            if not has_mask_old(next_ner_word) and len(ner_words):
                ner_words.pop(0)
                while len(raw_words):
                    print("raw_word, next_ner_word", raw_word, next_ner_word)
                    if raw_word == next_ner_word:
                        raw_words.insert(0, raw_word_info)
                        ner_words.insert(0, next_ner_word)
                        break
                    prev_raw_word_info = raw_word_info
                    raw_word_info = raw_words.pop(0)
                    raw_word = raw_word_info["text"]

            # 끝까지 못찾으면 끝 단어까지 mask된것
            end_time = prev_raw_word_info["end"]
            mask_times.append([start_time, end_time])

            i(f"mask 종료 단어: {prev_raw_word_info['text']}")
            i(f"시작 시간: {start_time}, 종료 시간: {end_time}")
            i("==================================================")

    return mask_times


def decode_text(txt):
    return bytes(txt, "utf-8").decode("unicode_escape")