import os
from pydub import AudioSegment
from pydub.generators import Sine

def load(file):
    """
    오디오 파일을 불러온다
    
    :param file: 불러올 오디오 파일 경로
    :return: 불러온 오디오 객체
    """

    # audio 객체라면 바로 리턴
    if not isinstance(file, str):
        return file
    
    # 아니라면 파일 로드
    _, format = name_format(file)
    return AudioSegment.from_file(file, format=format)


def save(audio, path, new_format=None):
    """
    pydub 오디오 파일을 저장한다. (확장자가 없으면 .mp3 확장자를 붙여준다.)

    :param audio: 저장할 오디오 파일 객체
    :param path: 저장할 경로
    """
    _, extension = name_format(path)
    if new_format:
        extension = new_format
    audio.export(path, format=extension)


def name_format(file):
    """
    파일 이름과 확장자를 분리해서 리턴한다.

    :param file: 파일 경로
    :return: 파일 이름, 확장자
    """
    file_name, format = os.path.splitext(file)
    format = format[1:]
    return file_name, format


def convert_format(file, dst_format):
    """
    오디오 파일의 포맷을 변환해서 같은 이름으로 저장한다.

    :param file: 변환할 오디오 파일 경로
    :param dst_format: 변환할 포맷
    """
    audio = load(file)
    name, _ = name_format(file)
    save(audio, f"{name}.{dst_format}", dst_format)


def crop_audio(src, start, end, dst=None):
    """
    오디오 파일을 자른다.

    :param src: 원본 오디오 파일 경로
    :param start: 자를 시작 시간
    :param end: 자를 종료 시간
    :param dst: 저장할 경로

    :return: 자른 오디오 파일 객체
    """
    audio = load(src)
    audio = audio[start:end]
    if dst:
        save(audio, dst)
    return audio


def repeat_audio(src, repeat_count, dst=None):
    """
    오디오 파일을 반복한다.

    :param src: 원본 오디오 파일 경로
    :param repeat_count: 반복 횟수
    :param dst: 저장할 경로

    :return: 반복된 오디오 파일 객체
    """
    repeat_count = int(repeat_count)
    audio = load(src)
    repeated_audio = audio * repeat_count
    if dst:
        save(repeated_audio, dst)
    return repeated_audio


def overlay_audio(original_file, start, end, overlay_file=None, output_file=None, mix=False):
    """
    오디오 파일의 특정 구간을 다른 오디오 파일로 덮어씌운다.

    :param original_file: 원본 오디오 파일 경로 (또는 pydub 음성 객체)
    :param overlay_file: 덮어씌울 오디오 파일 경로 (또는 pydub 음성 객체) (없으면 사인파)
    :param start: 덮어씌울 구간의 시작 시간
    :param end: 덮어씌울 구간의 종료 시간
    :param output_file: 저장할 경로

    :return: 특정 구간 덮어씌워진 오디오 파일 객체    
    """
    
    original_audio = load(original_file)
    overlay_audio = load(overlay_file) if overlay_file else sine_wave()

    # 덮어씌울 구간의 길이
    duration = end - start

    # 덮어씌울 구간의 길이가 덮어씌울 오디오 길이보다 길면 repeat_audio() 함수를 사용하여 덮어씌울 구간의 길이를 덮어씌울 오디오 길이에 맞춘다.
    if duration > len(overlay_audio):
        overlay_audio = repeat_audio(overlay_audio, duration // len(overlay_audio) + 1)

    # 만약 end가 오디오 길이보다 길면 오디오 길이에 맞춘다.
    if end > len(original_audio):
        end = len(original_audio)

    overlay_segment = overlay_audio[:duration] # 덮어씌울 오디오 길이 자르기

    if mix:
        output_audio = original_audio.overlay(overlay_segment, position=start)  # 두 가지 소리 동시에 들림
    else:
        # output_audio = original_audio.overlay_in_place(overlay_segment, position=start_time)  # overlay_audio가 덮어씌우기인데 함수 존재 에러
        original_audio_s2m = original_audio[:start]  # start to mid
        original_audio_m2e = original_audio[end:]  # mid to end
        output_audio = original_audio_s2m + overlay_segment + original_audio_m2e

    # 만약 output_file이 있으면 저장
    if output_file:
        save(output_audio, output_file)

    # overylay된 audio 객체 리턴
    return output_audio


def sine_wave(duration=1000, freq=440):
    """
    사인파 생성
    """
    duration = duration # ms
    frequency = freq # Hz
    return Sine(frequency).to_audio_segment(duration=duration)


# 메인
if __name__ == "__main__":
    pass