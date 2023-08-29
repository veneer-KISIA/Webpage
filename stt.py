import whisper_timestamped as whisper
import audio
import re
import log
import json

def transcribe(file):
    """
    https://github.com/linto-ai/whisper-timestamped
    whisper_timestamped 이용해서 오디오 파일을 텍스트로 변환한다.

    :param file: 오디오 파일 경로
    """
    audio = whisper.load_audio(file)
    model = whisper.load_model("tiny", device="cpu")
    return whisper.transcribe(model, audio)


def overlay_mask_times(origin, mask_times, overlay=None, save_path=None, mix=False):
    """
    마스킹 된 단어들의 시간 리스트를 오디오 파일에 덮어씌운다.

    :param origin: 원본 오디오 파일
    :param mask_times: 마스킹 된 단어들의 시간 구간 리스트
    :param overlay: 덮어씌울 오디오 파일
    :param save_path: 저장할 경로

    :return: 덮어씌워진 오디오 파일 객체
    """
    for start, end in mask_times:
        start *= 1000
        end *= 1000
        overlayed_audio = audio.overlay_audio(origin, start, end, overlay, mix=mix)
        origin = overlayed_audio  # 연속적으로 계속 덮어씌우기

    # 저장하기
    if save_path:
        audio.save(origin, save_path)
    return origin


def has_mask(text):
    """
    텍스트에 마스킹된 부분이 있는지 확인한다.
    :param text: 텍스트
    """
    pattern = r"\[.*\]"  # 정규 표현식 패턴: "["로 시작하고 "]"로 끝나는 문자열
    return re.search(pattern, text) is not None


def get_mask_times(file):
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
    ner_text = (
        " 안녕? 네 이름은 [NAME]이야 현재 [LOC_COUNTRY]에 살고 있어 너는 이름이 어떻게 돼? 괜찮으면 전화번호도 말려줘 잘가?"
    )
    ner_words = ner_text.strip().split(" ")
    d(f"ner_words {ner_words}")
    segments = data["segments"]

    # 덮어씌울 리스트 (구조: [[시작1, 종료1], [시작2, 종료2], ...]])
    mask_times = []
    raw_words = [word for segment in segments for word in segment["words"]]

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
        if has_mask(ner_word):
            i("==================== 마스크 =======================")
            i(f"mask 시작 단어: {raw_word}")
            start_time = raw_word_info["start"]
            next_ner_word = ner_words.pop(0)
            prev_raw_word_info = raw_word_info
            while len(raw_words):
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


# 메인
if __name__ == "__main__":
    # 로거
    logger = log.get(__name__)
    log.set_level(__name__, "i")
    i, d = logger.info, logger.debug

    # 파일 경로
    audio_file = "audio/korean.mp3"
    stt_file = "stt/korean.json"
    
    # # STT 후, 파일 저장
    stt = transcribe(audio_file)
    with open(stt_file, "w", encoding='utf-8') as f:
        json.dump(stt, f, indent='\t', ensure_ascii=False)
    # 출력해보기
    stt = json.dumps(stt, indent='\t', ensure_ascii=False)
    d(f"STT: {stt}")
    
    # 마스킹 된 단어들의 시간 구간 리스트 구하기
    mask_times = get_mask_times(stt_file)
    i(f"마스킹 시간구간: {mask_times}")

    # 마스킹 된 단어들의 시간 구간 리스트를 오디오 파일에 덮어씌우기
    # overlay_mask_times(audio_file, mask_times, overlay="audio/beep.mp3", save_path="audio/overlayed-korean.mp3")
    overlay_path = "audio/overlayed-korean.mp3"
    overlay_mask_times(audio_file, mask_times, save_path=overlay_path)
    i(f"{overlay_path} 파일 저장됨")

    # 마스킹 된 단어들의 시간 구간 리스트를 오디오 파일에 믹스하기 (동시에 들림)
    mix_path = "audio/mixed-korean.mp3"
    overlay_mask_times(audio_file, mask_times, save_path=mix_path, mix=True)
    i(f"{mix_path} 파일 저장됨")
