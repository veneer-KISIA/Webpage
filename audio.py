import os 
import re
import log
import json
from pydub import AudioSegment
from pydub.generators import Sine


def save_audio(audio_file, path):
    """
    pydub 오디오 파일을 저장한다. (확장자가 없으면 .mp3 확장자를 붙여준다.)

    :param audio_file: 저장할 오디오 파일 객체
    :param path: 저장할 경로
    """
    _, extension = os.path.splitext(path)
    has_extension = bool(extension)
    if not has_extension:
        path += ".mp3"
    audio_file.export(path)


# 참고: https://stackoverflow.com/questions/7629873/how-do-i-mix-audio-files-using-python
# 라이브러리가 작동 안해서 테스트 더 필요
def overlay_sound(origin, start_ms, end_ms, overlay=None, save_path=None):
    """
    오디오 파일의 특정 구간에 소리를 덮어씌운다.

    :param origin: 원본 오디오 파일
    :param start_ms: 덮어씌울 시작 시간(ms)
    :param end_ms: 덮어씌울 종료 시간(ms)
    :param overlay: 덮어씌울 오디오 파일
    :param save_path: 저장할 경로

    :return: 덮어씌워진 오디오 파일 객체
    """

    # 오디오 파일 불러오기
    audio = AudioSegment.from_file(origin)

    # 덮어씌울 소리가 없으면 1000Hz 사인파를 만든다.
    if not overlay:
        overlay = Sine(1000)

    # 특정 부분에 소리 덮어씌우기
    start_frame = int(start_ms * audio.frame_rate / 1000)
    end_frame = int(end_ms * audio.frame_rate / 1000)

    # overlay 길이 설정
    frame_length = int(overlay.duration_seconds * overlay.frame_rate)

    # 특정 부분의 데이터 가져오기
    start_sample = start_frame * audio.frame_width
    end_sample = (end_frame + frame_length) * audio.frame_width
    replace_audio = audio.raw_data[start_sample:end_sample]

    # 새로운 오디오 생성하여 소리 덮어씌우기
    modified_audio = AudioSegment(
        data=audio.raw_data[:start_sample]
        + overlay.raw_data
        + audio.raw_data[end_sample:],
        frame_rate=audio.frame_rate,
        sample_width=audio.sample_width,
        channels=audio.channels,
    )

    # 저장하기
    save_audio(modified_audio, save_path)
    return modified_audio


def overlay_mask_times(origin, mask_times, overlay=None, save_path=None):
    """
    마스킹 된 단어들의 시간 리스트를 오디오 파일에 덮어씌운다.

    :param origin: 원본 오디오 파일
    :param mask_times: 마스킹 된 단어들의 시간 구간 리스트
    :param overlay: 덮어씌울 오디오 파일
    :param save_path: 저장할 경로

    :return: 덮어씌워진 오디오 파일 객체
    """
    for start, end in mask_times:
        masked_audio = overlay_sound(origin, start, end, overlay)
        origin = masked_audio  # 연속적으로 계속 덮어씌우기

    # 저장하기
    if save_path:
        save_audio(origin, save_path)
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
    with open(file) as f:
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

        d(f"raw_word: {raw_word}, ner_word: {ner_word}")

        if ner_word == raw_word:
            continue

        # [MASK]가 포함된 단어를 찾으면
        if has_mask(ner_word):
            d("===============================================")
            d(f"mask 시작 단어: {raw_word}")
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

            d(f"mask 종료 단어: {prev_raw_word_info['text']}")
            d(f"시작 시간: {start_time}, 종료 시간: {end_time}")
            d("===============================================")

    return mask_times


def decode_text(txt):
    return bytes(txt, "utf-8").decode("unicode_escape")


# 메인
if __name__ == "__main__":
    # 로거
    logger = log.get(__name__)
    log.set_level(__name__, "d")
    d = logger.debug

    audio_file = "korean3.mp3"
    timestamped_file = "korean3-2.json"
    # 마스킹 된 단어들의 시간 구간 리스트 구하기
    mask_times = get_mask_times(timestamped_file)
    d(f"마스킹 시간구간: {mask_times}")

    # 마스킹 된 단어들의 시간 구간 리스트를 오디오 파일에 덮어씌우기
    # overlay_mask_times(audio_file, mask_times, save_path="korean3-masked.mp3")
