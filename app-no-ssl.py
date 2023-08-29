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
        return jsonify(message='서버가 파일을 받았습니다', fileName=file.filename), 200

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

if __name__ == '__main__':
    UPLOAD_FOLDER = 'uploads'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # SSL 적용
    # setup_ssl()

    # 로거
    logger = log.get(__name__, "./logs/app.log")
    log.set_level(__name__, "i")
    i, d = logger.info, logger.debug

    app.run(debug=True, host='0.0.0.0', port=9999)
    i("서버가 9999포트에서 시작되었습니다")
