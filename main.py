import os
import tempfile
from flask import Flask, request, jsonify, send_file
from pydub import AudioSegment
from pydub.playback import play
import demucs.separate

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def process_audio():
    if request.method == 'GET':
        return "Hello, World!"

    print(f"Request headers: {request.headers}")
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    audio_file = request.files['file']
    if audio_file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Save uploaded file to a temporary location
    temp_dir = tempfile.TemporaryDirectory()
    input_file_path = os.path.join(temp_dir.name, audio_file.filename)
    audio_file.save(input_file_path)
    print(f"File saved at: {input_file_path}")

    output_dir = os.path.join(temp_dir.name, "demucs_output")
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Load the MP3 file
        audio = AudioSegment.from_file(input_file_path)

        # Create output directory for Demucs
        output_dir = os.path.join(temp_dir.name, "demucs_output")
        os.makedirs(output_dir, exist_ok=True)

        # Process the entire audio file with Demucs
        demucs.separate.main([
        "--mp3",
        "--two-stems", "vocals",
        "-n", "htdemucs",
        "-o", output_dir,
        input_file_path
        ])
        print(f"Processed audio file: {input_file_path}")

        # Find the vocal track in the output directory
        vocal_file = None
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if "vocals" in file.lower() and not "no_vocals" in file.lower():
                    vocal_file = os.path.join(root, file)
                    break

        if not vocal_file:
            print(f"Vocal track not found for file: {input_file_path}")
            return jsonify({"error": "Vocal track not found"}), 500

        # Return the processed audio file
        return send_file(vocal_file, as_attachment=True)

    except Exception as e:
        print(f"Error during processing: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080, debug=True)

