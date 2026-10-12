import os
import glob
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

COOKIE_FILE_PATH = "cookies.txt"

def setup_cookies():
    cookies_env = os.environ.get("COOKIES_CONTENT")
    if cookies_env:
        # Clean up any literal carriage returns if pasted weirdly
        cleaned_cookies = cookies_env.replace("\r\n", "\n")
        with open(COOKIE_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(cleaned_cookies)
        print("SUCCESS: cookies.txt written from environment variable.")
    else:
        print("WARNING: COOKIES_CONTENT environment variable is missing or empty!")

# Initialize cookies on startup
setup_cookies()

@app.route('/', methods=['GET'])
def health_check():
    cookie_exists = os.path.exists(COOKIE_FILE_PATH)
    return jsonify({
        "status": "online", 
        "message": "YT-DLP Cloud API is running!",
        "cookies_loaded": cookie_exists
    }), 200

@app.route('/download-media', methods=['POST'])
def download_media():
    data = request.json
    if not data or 'url' not in data:
        return jsonify({"status": "error", "message": "No URL provided"}), 400

    video_url = data.get('url')
    quality = data.get('quality', '720')

    # Clean up old files in container workspace
    for f in glob.glob("downloads/*"):
        try:
            os.remove(f)
        except:
            pass

    os.makedirs("downloads", exist_ok=True)

    if quality == 'audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,
        }
    else:
        ydl_opts = {
            'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'noplaylist': True,
        }

    # Bypass bot detection & reload prompts
    ydl_opts['extractor_args'] = {
        'youtube': {
            'player_client': ['web_safari', 'web']
        }
    }

    if os.path.exists(COOKIE_FILE_PATH):
        ydl_opts['cookiefile'] = COOKIES_FILE_PATH
        print("Using cookies.txt for yt-dlp request.")
    else:
        print("WARNING: cookies.txt not found during request!")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            
            if quality == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'
            elif not filename.endswith('.mp4'):
                filename = os.path.splitext(filename)[0] + '.mp4'

            if not os.path.exists(filename):
                files = glob.glob("downloads/*")
                if files:
                    filename = files[0]
                else:
                    return jsonify({"status": "error", "message": "File processing failed."}), 500

            title = info.get('title', 'media').replace('/', '_')
            return jsonify({
                "status": "success",
                "filename": os.path.basename(filename),
                "title": title
            })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get-file/<path:filename>', methods=['GET'])
def get_file(filename):
    safe_path = os.path.join("downloads", filename)
    if os.path.exists(safe_path):
        return send_file(safe_path, as_attachment=True)
    return "File not found or expired", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
