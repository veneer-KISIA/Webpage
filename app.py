import sys
import json
import stt
from flask import Flask, request, send_file, jsonify
import os
import log
from flask_sslify import SSLify  # SSL 적용을 위한 모듈

app = Flask(__name__)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        message='서버에서 받은 파일이 없습니다.'
        i(message)
        return jsonify(message=message), 400
    
    file = request.files['file']
    if file.filename == '':
        message='파일 이름이 공백입니다'
        i(message)
        return jsonify(message=message), 400
    
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
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
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(filepath, as_attachment=True)

def setup_ssl():
    ssl_home = '/etc/letsencrypt/live/veneer.r-e.kr/'
    global ssl_fullchain 
    ssl_fullchain = ssl_home + 'fullchain.pem'
    global ssl_privkey 
    ssl_privkey = ssl_home + 'privkey.pem'

    # SSL 적용
    return SSLify(app)

def configs():
    # uploads
    UPLOAD_FOLDER = 'uploads'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # stt
    STT_FOLDER = 'stt'
    app.config['STT_FOLDER'] = STT_FOLDER

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
