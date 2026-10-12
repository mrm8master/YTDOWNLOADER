import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# Automatically write cookies from Render Environment Variable if it exists
cookies_env = os.environ.get("COOKIES_CONTENT")
COOKIE_FILE_PATH = "cookies.txt"

if cookies_env:
    with open(COOKIE_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(cookies_env)

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "YT-DLP Cloud API is running!"}), 200

@app.route('/get-link', methods=['POST'])
def get_download_link():
    data = request.json
    if not data or 'url' not in data:
        return jsonify({"status": "error", "message": "No URL provided"}), 400

    video_url = data.get('url')
    quality = data.get('quality', '720')

    ydl_opts = {
        'noplaylist': True,
    }

    # Use cookie file if it was successfully created from the environment variable
    if os.path.exists(COOKIE_FILE_PATH):
        ydl_opts['cookiefile'] = COOKIE_FILE_PATH

    if quality == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
    else:
        ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_url = info.get('url')
            if not direct_url and 'requested_formats' in info and len(info['requested_formats']) > 0:
                direct_url = info['requested_formats'][0].get('url')

            return jsonify({
                "status": "success",
                "title": info.get('title', 'video').replace('/', '_'),
                "download_url": direct_url
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
