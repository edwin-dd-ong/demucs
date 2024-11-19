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
        duration = len(audio)  # Duration in milliseconds
        segment_length = 10 * 1000  # 10 seconds in milliseconds

        # Split the audio into 10-second segments
        segments = []
        for start in range(0, duration, segment_length):
            segment = audio[start:start + segment_length]
            segment_path = os.path.join(temp_dir.name, f"segment_{start}.mp3")
            segment.export(segment_path, format="mp3")
            segments.append(segment_path)

        # Process each segment with Demucs
        processed_segments = []
        for segment_path in segments:
            segment_output_dir = os.path.join(temp_dir.name, f"output_{os.path.basename(segment_path)}")
            os.makedirs(segment_output_dir, exist_ok=True)

            demucs.separate.main([
                "--mp3",
                "--two-stems", "vocals",
                "-n", "htdemucs",
                "-o", segment_output_dir,
                segment_path
            ])
            print(f"Processed segment: {segment_path}")

            # Find the vocal track in the output directory
            vocal_file = None
            for root, dirs, files in os.walk(segment_output_dir):
                for file in files:
                    if "vocals" in file.lower() and not "no_vocals" in file.lower():
                        vocal_file = os.path.join(root, file)
                        break

            if not vocal_file:
                print(f"Vocal track not found for segment: {segment_path}")
                return jsonify({"error": f"Vocal track not found for segment: {segment_path}"}), 500

            processed_segments.append(AudioSegment.from_file(vocal_file))

        # Stitch the processed segments back together
        final_audio = sum(processed_segments)
        final_output_path = os.path.join(output_dir, "final_output.mp3")
        final_audio.export(final_output_path, format="mp3")
        print(f"Final audio saved at: {final_output_path}")

        return send_file(final_output_path, as_attachment=True)

    except Exception as e:
        print(f"Error during processing: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080, debug=True)

