import os
import tempfile
import subprocess
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/process', methods=['POST'])
def process_twostem():
    print(f"Request headers: {request.headers}")
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    audio_file = request.files['file']
    if audio_file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    temp_dir = tempfile.TemporaryDirectory()
    input_file_path = os.path.join(temp_dir.name, audio_file.filename)
    audio_file.save(input_file_path)
    print(f"File saved at: {input_file_path}")

    output_dir = os.path.join(temp_dir.name, "demucs_output")
    os.makedirs(output_dir, exist_ok=True)

    demucs_command = [
        "demucs", "--two-stems=vocals", "-o", output_dir, input_file_path
    ]
    try:
        result = subprocess.run(demucs_command, check=True, capture_output=True, text=True)
        print(f"Demucs stdout: {result.stdout}")
        print(f"Demucs stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Demucs command failed: {e.stderr}")
        return jsonify({"error": "Demucs processing failed"}), 500

    print(f"Files in output directory: {os.listdir(output_dir)}")

    vocal_file = None
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if "vocals" in file.lower():
                vocal_file = os.path.join(root, file)
                break

    if not vocal_file:
        print("Vocal track not found")
        return jsonify({"error": "Vocal track not found"}), 500

    print(f"Returning file: {vocal_file}")
    return send_file(vocal_file, as_attachment=True, download_name="vocal.mp3")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

