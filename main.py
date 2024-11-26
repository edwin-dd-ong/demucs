import os
import tempfile
from flask import Flask, request, jsonify, send_file, Response
from pydub import AudioSegment
from pydub.playback import play
from demucs import separate
from flask_cors import CORS
import shutil
import sys


app = Flask(__name__)
CORS(app)

@app.route('/list-working-dir', methods=['GET'])
def list_working_dir():
    import os
    # Get the current working directory
    cwd = os.getcwd()
    # List all files and directories in the working directory
    files = os.listdir(cwd)
    return f"Current working directory: {cwd}<br>Contents:<br>{'<br>'.join(files)}"


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
    temp_dir = tempfile.mkdtemp()  
    input_file_path = os.path.join(temp_dir, audio_file.filename)
    audio_file.save(input_file_path)
    print(f"File saved at: {input_file_path}")

    output_dir = os.path.join(temp_dir, "demucs_output")
    os.makedirs(output_dir, exist_ok=True)

    try:

        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the absolute path to the release_models directory
        release_models_path = os.path.join(current_dir, 'release_models')

        sys.stderr.write(f"Using release models path: {release_models_path}")

        # Process the entire audio file with Demucs
        separate.main([
        "--two-stems", "vocals",
        "-n", "d6b2e963",
        "-o", output_dir,
        "--repo", release_models_path,
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

        def stream_file(file_path, chunk_size=8192):
            """Stream a file in chunks."""
            htdemucs_dir = os.path.join(output_dir)
            print(f"Contents of {htdemucs_dir}: {os.listdir(htdemucs_dir)}")
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    yield chunk

        # Return the processed audio file
        response = Response(stream_file(vocal_file), content_type='audio/wav')
        # Delay cleanup after the response
        response.call_on_close(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        return response


    except Exception as e:
        print(f"Error during processing: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080, debug=True)

