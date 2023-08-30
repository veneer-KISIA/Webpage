from flask import Flask, request, send_file, jsonify
import os
import json
from pydub import AudioSegment
import whisper_timestamped as whisper
import audio

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
        stt_result = audio.transcribe(filename)
        # 여기서 stt_result 변수에 STT 결과가 저장됩니다.

        return jsonify(message='파일이 정상적으로 업로드 되고 STT 변환되었습니다. ', fileName=file.filename, STT=stt_result), 200

def transcribe_audio(audio_filepath):
    audio = whisper.load_audio(audio_filepath)
    model = whisper.load_model("tiny", device="cpu")
    return whisper.transcribe(model, audio)

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9999)
