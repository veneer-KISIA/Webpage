import json
import os
import sys
from flask import Flask, request, send_file, jsonify
import pathlib

import modules.log as log
import modules.stt as stt
import modules.api as api
import modules.audio as audio


app = Flask(__name__)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/mask', methods=['POST'])
def mask_data():
    '''
    Runs STT on audio file and masks the text and audio
    Returns (stt), masked_stt and masked audio
    '''

    filename = json.loads(request.data).get('fileName', None)
    if filename is None:
        d(request.data)
        message = 'Empty fileName'
        d(f'{message}')
        return jsonify(message=message), 400
    filepath = pathlib.Path(app.config['AUDIO_FOLDER'])
    filepath = pathlib.Path.joinpath(filepath, filename)
    i(f'File: {filepath}')

    if (ext := filepath.suffix) not in app.config['AUDIO_EXTS']:
        message = f'Unsuppored file type'
        d(f'{message}: {ext}')
        return jsonify(message=message), 400
    
    if not filepath.exists():
        message = f'File does not exist'
        d(f'{message}: {filepath}')
        return jsonify(message=message), 400
    

    i(f'Opening file: {filepath}')
    text, word_list = stt.get_stt(filepath)

    masked_text = api.request_ner(text)
    if masked_text:
        masked_list = masked_text.split()
        i(f'Masked text: {masked_text}')

        mask_times = stt.get_mask_times(word_list, masked_list)
        if mask_times is None:
            message = 'test and masked text length did not match'
            i(message)
            d(f'Text: {text}, len = {len(word_list)}')
            d(f'Text: {masked_text}, len = {len(masked_list)}')
            return jsonify(message=message), 500
        
        masked_path = pathlib.Path(app.config['MASKED_AUDIO_FOLDER'])
        masked_path = pathlib.Path.joinpath(masked_path, filename)
        try:
            audio.overlay_mask_times(filepath, mask_times, save_path=masked_path)
            i(f'Masked audio file: {masked_path}')
        except Exception as e:
            d(e)
            return jsonify(message='Something went wrong'), 500
    else:
        masked_text = 'NER server error'
        return jsonify(message='Only STT done', fileName=None, stt_text=text, ner_text=masked_text), 200
    
    return jsonify(message='Audio Masking done', fileName=masked_path.name, stt_text=text, ner_text=masked_text), 200

@app.route('/upload', methods=['POST'])
def upload_stt():
    '''
    upload audio
    data here is personal data and should be encrypted in real use
    '''
    if 'audio' not in request.files:
        message='Server did not recieve audio file'
        i(message)
        return jsonify(message=message), 400
    
    file = request.files['audio']
    if file.filename == '':
        message='File name is blank'
        i(message)
        return jsonify(message=message), 400
    
    if file:
        # TODO add DBMS related code here
        filename = os.path.join(app.config['AUDIO_FOLDER'], file.filename)
        file.save(filename)
        i(f"File Uploaded: {filename}")
        
        return jsonify(message='File upload complete', fileName=file.filename), 200
    
    else:
        message='File does not exist'
        i(message)
        return jsonify(message=message), 400

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    filepath = os.path.join(app.config['AUDIO_FOLDER'], filename)
    return send_file(filepath, as_attachment=True)

@app.route('/download/masked', methods=['POST'])
def get_masked_audio():
    filename = json.loads(request.data).get('fileName', None)

    filepath = pathlib.Path.joinpath(app.config['MASKED_AUDIO_FOLDER'], filename)
    if (ext := filepath.suffix) not in app.config['AUDIO_EXTS']:
        message = f'Unsuppored file type'
        d(f'get_masked: {message}: {ext}')
        return jsonify(message=message), 400

    if not filepath.exists():
        message = f'File does not exist'
        d(f'get_masked: {message}: {filepath}')
        return jsonify(message=message), 400
    
    return send_file(filepath, as_attachment=False, download_name=f'masked-{filepath.stem}.mp3', mimetype='audio/*')

def setup_ssl():
    from flask_sslify import SSLify  # SSL 적용을 위한 모듈

    ssl_home = '/etc/letsencrypt/live/veneer-test.r-e.kr/'
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
    LOGS_FOLDER = 'logs'

    # supported audio file formats
    app.config['AUDIO_EXTS'] = ['.mp3']
    
    # 로컬 폴더 없으면 만들기
    folders = [LOGS_FOLDER]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # app 관련 config
    UPLOAD_FOLDER = 'uploads'
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    
    AUDIO_FOLDER = 'audio'  # upload/audio
    app.config['AUDIO_FOLDER'] = os.path.join(UPLOAD_FOLDER, AUDIO_FOLDER)

    MASKED_STT_FOLDER = 'masked-stt'  # upload/masked-stt
    app.config['MASKED_STT_FOLDER'] = os.path.join(UPLOAD_FOLDER, MASKED_STT_FOLDER)

    MASKED_AUDIO_FOLDER = 'masked-audio'  # upload/masked-audio
    app.config['MASKED_AUDIO_FOLDER'] = os.path.join(UPLOAD_FOLDER, MASKED_AUDIO_FOLDER)

    # app 관련 config의 모든 폴더 생성 및 설정
    folders = [AUDIO_FOLDER, MASKED_STT_FOLDER, MASKED_AUDIO_FOLDER]
    for folder in folders:
        folder_path = os.path.join(UPLOAD_FOLDER, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

def main():
    # app configs 설정
    configs()

    # 인자 가져와서 ssl 실행 유뮤 결정
    argv = sys.argv[1:]

    # python app.py --ssl
    app_kargs = {}
    if '--ssl' in argv:
        i("ssl 적용됨")
        setup_ssl()
        app_kargs['ssl_context'] = (ssl_fullchain, ssl_privkey)
    
    port = 9999
    app.run(debug=True, host='0.0.0.0', port=port, **app_kargs)
    i(f"서버가 {port}포트에서 시작되었습니다")

if __name__ == '__main__':    
    # 로거
    logger = log.get(__name__, 'logs/app.log')
    log.set_level(__name__, "d")
    i, d = logger.info, logger.debug

    main()

    
