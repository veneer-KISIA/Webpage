from pydub import AudioSegment
from pydub.generators import Sine
from pydub.utils import ms2frame, frame2ms

def overlay_sound(origin, start_ms, end_ms, overlay=None, save_path=None):
    """
    origin: 원본 오디오 파일
    overlay: 덮어씌울 오디오 파일
    start_ms: 덮어씌울 시작 시간(ms)
    end_ms: 덮어씌울 종료 시간(ms)
    """

    # 오디오 파일 불러오기
    audio = AudioSegment.from_file(origin)

    # 덮어씌울 소리가 없으면 1000Hz 사인파를 만든다.
    if not overlay:
        overlay = Sine(1000)

    # 특정 부분에 소리 덮어씌우기
    start_frame = ms2frame(start_ms, audio.frame_rate)
    end_frame = ms2frame(end_ms, audio.frame_rate)
    frame_length = len(overlay)

    # 특정 부분의 데이터 가져오기
    start_sample = start_frame * audio.frame_width
    end_sample = (end_frame + frame_length) * audio.frame_width
    replace_audio = audio.raw_data[start_sample:end_sample]

    # 새로운 오디오 생성하여 소리 덮어씌우기
    modified_audio = AudioSegment(
        data=audio.raw_data[:start_sample] + overlay.raw_data + audio.raw_data[end_sample:],
        frame_rate=audio.frame_rate,
        sample_width=audio.sample_width,
        channels=audio.channels
    )

    # 저장하기
    if save_path:
        # 만약 save_path가 확장자가 없으면 .mp3 확장자를 붙여준다.
        if not save_path.endswith('.mp3'):
            save_path += '.mp3'
        modified_audio.export(save_path)

    return modified_audio

overlay_sound('a1.mp3', 1000, 2000, None, 'modified-a1.mp3')

