from flask import Flask, request, send_file, jsonify
import os
from flask_sslify import SSLify  # SSL 적용을 위한 모듈

app = Flask(__name__)
ssl_home = '/etc/letsencrypt/live/veneer.r-e.kr/'
ssl_fullchain = ssl_home + 'fullchain.pem'
ssl_privkey = ssl_home + 'privkey.pem'

# SSL 적용
sslify = SSLify(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
        return jsonify(message='File uploaded successfully', fileName=file.filename), 200

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9999, ssl_context=(ssl_fullchain, ssl_privkey))
