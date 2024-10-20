import os
import requests
import subprocess
from flask import Flask, send_from_directory, request, jsonify

app = Flask(__name__)

UPLOAD_DIR = 'uploads'
HLS_DIR = 'hls'

# Create directories for uploads and HLS if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(HLS_DIR, exist_ok=True)

def download_video(video_url, file_name):
    """Download the video from the provided URL."""
    video_path = os.path.join(UPLOAD_DIR, file_name)
    response = requests.get(video_url, stream=True)
    with open(video_path, 'wb') as video_file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                video_file.write(chunk)
    return video_path

def convert_to_hls(input_video, output_dir, stream_name):
    """Convert the downloaded video to HLS format (.m3u8)."""
    hls_output = os.path.join(output_dir, stream_name + '.m3u8')
    command = [
        'ffmpeg', '-i', input_video, '-codec: copy',
        '-start_number', '0', '-hls_time', '10',
        '-hls_list_size', '0', '-f', 'hls', hls_output
    ]
    subprocess.run(command)
    return hls_output

@app.route('/upload', methods=['POST'])
def upload_video():
    """Endpoint to download video from a URL and convert it to HLS."""
    video_url = request.args.get('url')  # Get the URL from the request
    if not video_url:
        return jsonify({'error': 'Please provide a video URL.'}), 400

    file_name = video_url.split('/')[-1]  # Use the file name from URL
    video_path = download_video(video_url, file_name)

    # Convert video to HLS
    stream_name = file_name.split('.')[0]
    hls_output = convert_to_hls(video_path, HLS_DIR, stream_name)

    # Generate the streaming link (HLS .m3u8 link)
    stream_link = f"http://{request.host}/hls/{stream_name}.m3u8"
    return jsonify({'m3u8_link': stream_link})

@app.route('/hls/<path:filename>')
def serve_hls(filename):
    """Serve the HLS (.m3u8 and .ts) files."""
    return send_from_directory(HLS_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
