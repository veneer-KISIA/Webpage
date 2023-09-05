from flask import Flask, request, send_file, jsonify
import os
import log

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
            json.dump(stt_result, stt_file, ensure_ascii=False, indent=4)
        
        return jsonify(message='파일 업로드 및 STT 변환 완료', fileName=file.filename, STT=stt_text), 200

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    UPLOAD_FOLDER = 'uploads'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # 로거
    logger = log.get(__name__, "./logs/app.log")
    log.set_level(__name__, "i")
    i, d = logger.info, logger.debug

    app.run(debug=True, host='0.0.0.0', port=9999)
    i("서버가 9999포트에서 시작되었습니다")















from flask import Flask, request, send_file, jsonify
import os
import json
from pydub import AudioSegment
import whisper_timestamped as whisper
import stt

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
STT_FOLDER = 'stt'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STT_FOLDER'] = STT_FOLDER

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify(message='No file part'), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify(message='No selected file'), 400

    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

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
            json.dump(stt_result, stt_file, ensure_ascii=False, indent=4)
        

        return jsonify(message='파일 업로드 및 STT 변환 완료', fileName=file.filename, STT=stt_text), 200

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(filepath, as_attachment=True)

@app.route('/get_stt_result', methods=['GET'])
def get_stt_result():
    stt_result = stt.transcribe("audio/korean.mp3")  # 적절한 파일 경로로 변경

    # 'text' 부분만 추출하여 반환
    stt_text = stt_result.get('text', '')

    return jsonify(STT=stt_text)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9999)
    # stt_result = stt.transcribe("audio/korean.mp3")
    # print(stt_result)
    # print(type(stt_result))


# 할 것
# - 로그 사용해서 디버깅하기
