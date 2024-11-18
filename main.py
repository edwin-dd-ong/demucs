import os
import tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import demucs.separate

app = Flask(__name__)
CORS(app)

@app.route('/process', methods=['POST', 'GET'])
def process_twostem():
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
        # Invoke Demucs with `--two-stems` directly
        demucs.separate.main([
            "--mp3",                      # Save as MP3
            "--two-stems", "vocals",      # Extract only vocals and "no_vocals"
            "-n", "htdemucs",            # Use the "mdx_extra" model
            "-o", output_dir,             # Output directory
            input_file_path               # Input audio file
        ])
        print("Separation complete.")

        # Find the vocal file in the output directory
        vocal_file = None
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if "vocals" in file.lower() and not "no_vocals" in file.lower():
                    vocal_file = os.path.join(root, file)
                    break

        if not vocal_file:
            print("Vocal track not found")
            return jsonify({"error": "Vocal track not found"}), 500

        return send_file(vocal_file, as_attachment=True)

    except Exception as e:
        print(f"Error during separation: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080, debug=True)

