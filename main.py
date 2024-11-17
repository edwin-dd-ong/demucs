import os
import tempfile
import subprocess
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_twostem():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    audio_file = request.files['file']
    if audio_file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Save the uploaded file temporarily
    temp_dir = tempfile.TemporaryDirectory()
    input_file_path = os.path.join(temp_dir.name, audio_file.filename)
    audio_file.save(input_file_path)

    # Create an output directory for Demucs
    output_dir = os.path.join(temp_dir.name, "demucs_output")
    os.makedirs(output_dir, exist_ok=True)

    # Run Demucs in twostem mode to separate vocals and instruments
    try:
        demucs_command = [
            "demucs", "--two-stems=vocals", "-o", output_dir, input_file_path
        ]
        subprocess.run(demucs_command, check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Demucs processing failed: {str(e)}"}), 500

    # Locate the vocal  track
    vocal_file = None
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if "vocals" in file:  # Demucs typically labels non-vocal files as "no_vocals"
                vocal_file = os.path.join(root, file)
                break

    if not vocal_file:
        return jsonify({"error": "Vocal track not found"}), 500

    # Return the instrumental track
    return send_file(vocal_file, as_attachment=True, download_name="vocal.mp3")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

