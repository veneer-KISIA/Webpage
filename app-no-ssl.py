from flask import Flask, request, send_file, jsonify
import os

app = Flask(__name__)

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
        return jsonify(message='파일이 업로드되었습니다', fileName=file.filename), 200
    

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9999)
