import sys
import json
import stt
from flask import Flask, request, send_file, jsonify
import os
import log

app = Flask(__name__)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/upload/time-list', methods=['POST'])
def upload_time_list():
    """
    whisper_timestamped의 json결과를 받아서 text의 masking된 부분의 time-list를 반환
    (mask-audio에게 전달할때 시간 리스트만 전달해서 오디오 마스킹 해주도록 편하게 만들기 위함)
    """
    # 요청에서 whisper_timestamped의 json결과 가져오기
    json_data = json.loads(request.form['data'])

    # whisper_timestamped의 json에서 마스킹 된 부분들의
    # time-list를 추출해서 반환
    mask_times = stt.get_mask_times(json_data)
    return jsonify(mask_times=mask_times)
    

@app.route('/upload/mask-audio', methods=['POST'])
def upload_mask_audio():
    """
    audio파일과 whisper_timestamped의 json결과 또는 시간 리스트를 받아서 마스킹된 오디오를 반환

    json일때와 시간 리스트를 구분하는 방법: json객체 안에 'type'키로 구분합니다. 
    'type'키의 값이 'json'이면 json객체로 인식하고, 'time-list'이면 시간 리스트로 인식합니다.
    데이터는 'data'키에 들어있어야 합니다.
    """
    # 요청에서 오디오 파일과 JSON 데이터 가져오기
    audio_file = request.files['audio']
    json_data = json.loads(request.form['data'])

    # audio_file을 upload/audio폴더에 저장
    audio_filename = os.path.join(app.config['AUDIO_FOLDER'], audio_file.filename)
    audio_file.save(audio_filename)

    # 데이터가 JSON 객체인지 시간 리스트인지 확인하기
    if json_data['type'] == 'json':
        # 데이터를 masked_stt폴더에 파일로 저장
        masked_stt = json_data['data']
        masked_stt_filename = os.path.splitext(audio_file.filename)[0] + '.json'
        masked_stt_filepath = os.path.join(app.config['MASKED_STT_FOLDER'], masked_stt_filename)
        with open(masked_stt_filepath, 'w', encoding='utf-8') as masked_stt_file:
            json.dump(masked_stt, masked_stt_file, ensure_ascii=False, indent='\t')

        # whisper_timestamped의 json에서 마스킹 된 부분들의
        # time-list를 추출해서 마스킹된 오디오를 반환
        mask_times = stt.get_mask_times(masked_stt_filepath)
        overlay_path = os.path.join(audio_file.filename, app.config['MASKED_AUDIO_FOLDER'])
        stt.overlay_mask_times(audio_filename, mask_times, save_path=overlay_path)

    elif json_data['type'] == 'time-list':
        # 주어진 time-list를 이용해서 마스킹된 오디오를 반환
        pass # 만들어야 함

    # 마스킹된 오디오를 반환
    return send_file(overlay_path, as_attachment=True)



@app.route('/upload/stt', methods=['POST'])
def upload_stt():
    if 'audio' not in request.files:
        message='서버에서 받은 파일이 없습니다.'
        i(message)
        return jsonify(message=message), 400
    
    file = request.files['audio']
    if file.filename == '':
        message='파일 이름이 공백입니다'
        i(message)
        return jsonify(message=message), 400
    
    if file:
        filename = os.path.join(app.config['AUDIO_FOLDER'], file.filename)
        file.save(filename)
        i(f"파일이 업로드되었습니다: {filename}")

        # STT 변환 실행
        # 여기서 stt_result 변수에 STT 결과가 저장됩니다.
        stt_result = stt.transcribe(filename)
        print("STT 결과:", stt_result)
        #print(stt_result)
        # 'text' 부분만 추출하여 반환
        stt_text = stt_result.get('text', '')  # 'text' 키가 없을 경우 빈 문자열 반환
        print("추출된 텍스트:", stt_text)
        
        # STT 결과를 JSON 파일로 저장 (STT 폴더에 저장됩니다)
        stt_filename = os.path.splitext(file.filename)[0] + '.json'
        stt_filepath = os.path.join(app.config['STT_FOLDER'], stt_filename)

        with open(stt_filepath, 'w', encoding='utf-8') as stt_file:
            json.dump(stt_result, stt_file, ensure_ascii=False, indent='\t')
        
        return jsonify(message='파일 업로드 및 STT 변환 완료', fileName=file.filename, STT=stt_text), 200

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    filepath = os.path.join(app.config['AUDIO_FOLDER'], filename)
    return send_file(filepath, as_attachment=True)

def setup_ssl():
    from flask_sslify import SSLify  # SSL 적용을 위한 모듈

    ssl_home = '/etc/letsencrypt/live/veneer.r-e.kr/'
    global ssl_fullchain 
    ssl_fullchain = ssl_home + 'fullchain.pem'
    global ssl_privkey 
    ssl_privkey = ssl_home + 'privkey.pem'

    # SSL 적용
    return SSLify(app)

def configs():
    """
    설정 관련
    """
    # 로컬 폴더
    AUDIO_FOLDER = 'audio'
    LOGS_FOLDER = 'logs'
    
    # 로컬 폴더 없으면 만들기
    folders = [AUDIO_FOLDER, LOGS_FOLDER]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # app 관련 config
    UPLOAD_FOLDER = 'uploads'
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # upload/audio
    AUDIO_FOLDER = 'uploads'
    app.config['AUDIO_FOLDER'] = os.path.join(UPLOAD_FOLDER, AUDIO_FOLDER)

    # upload/stt
    STT_FOLDER = 'stt'
    app.config['STT_FOLDER'] = os.path.join(UPLOAD_FOLDER, STT_FOLDER)

    # upload/time-list
    TIME_LIST_FOLDER = 'time-list'
    app.config['TIME_LIST_FOLDER'] = os.path.join(UPLOAD_FOLDER, TIME_LIST_FOLDER)

    # upload/masked-stt
    MASKED_STT_FOLDER = 'masked-stt'
    app.config['MASKED_STT_FOLDER'] = os.path.join(UPLOAD_FOLDER, MASKED_STT_FOLDER)

    # upload/masked-audio
    MASKED_AUDIO_FOLDER = 'masked-audio'
    app.config['MASKED_AUDIO_FOLDER'] = os.path.join(UPLOAD_FOLDER, MASKED_AUDIO_FOLDER)

    # app 관련 config의 모든 폴더 없으면 만들기
    folders = [AUDIO_FOLDER, STT_FOLDER, TIME_LIST_FOLDER, MASKED_STT_FOLDER, MASKED_AUDIO_FOLDER]
    for folder in folders:
        folder_path = os.path.join(UPLOAD_FOLDER, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
    


if __name__ == '__main__':
    # app configs 설정
    configs()

    # 로거
    logger = log.get(__name__, "./logs/app.log")
    log.set_level(__name__, "i")
    i, d = logger.info, logger.debug

    # 인자 가져와서 ssl 실행 유뮤 결정
    argv = sys.argv[1:]
    # python app.py --ssl
    app_kargs = {}
    if '--ssl' in argv:
        i("ssl 적용됨")
        setup_ssl()
        app_kargs['ssl_context'] = (ssl_fullchain, ssl_privkey)
    
    app.run(debug=True, host='0.0.0.0', port=9999, **app_kargs)
    i("서버가 9999포트에서 시작되었습니다")