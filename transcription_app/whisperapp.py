# whisperapp.py
from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
import uuid

# -------------------------
# REAL Faster Whisper usage
# -------------------------
from faster_whisper import WhisperModel

# If you only have a CPU, leave device="cpu". 
# If you have a GPU with proper NVIDIA drivers, use device="cuda".
# You can also pick a different model like "tiny", "base", "small", "medium", "large-v2".
model = WhisperModel("base", device="cpu", compute_type="int8")

app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = '/tmp'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac'}

def allowed_file(filename):
    """Ensure the file extension is one of the allowed audio types."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_secure_filename():
    """Generate a secure unique filename."""
    return str(uuid.uuid4())

def transcribe_audio(file_path):
    """
    Run the Faster Whisper model on the given audio file and return the transcription.
    """
    # segments is a generator of recognized segments
    segments, info = model.transcribe(file_path)
    # Combine all segment texts into one string
    text = " ".join([segment.text for segment in segments])
    return text

def handle_transcription_request():
    """Handle the transcription request for both the web form and the API routes."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    try:
        # Generate a secure filename while preserving extension
        original_extension = os.path.splitext(file.filename)[1]
        secure_name = f"{get_secure_filename()}{original_extension}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_name)
        
        # Save the uploaded file
        file.save(file_path)
        
        # Transcribe the audio file
        transcription = transcribe_audio(file_path)

        # Remove the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Return the transcription in JSON
        return jsonify({'transcription': transcription})
        
    except Exception as e:
        # Ensure cleanup on error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    """Renders the simple HTML file upload form."""
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """Handles form submissions from the web UI."""
    return handle_transcription_request()

@app.route('/api/transcribe', methods=['POST'])
def api_transcribe():
    """API endpoint for programmatic access."""
    return handle_transcription_request()

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handles the case where the file is larger than MAX_CONTENT_LENGTH."""
    return jsonify({'error': 'File too large'}), 413

if __name__ == '__main__':
    # For a simple deployment, this is fine. 
    # In true production, you'd typically use Gunicorn or another WSGI server.
    app.run(host='0.0.0.0', port=5000, debug=True)
