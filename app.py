import os
import zipfile
import shutil
from flask import Flask, render_template, request, send_file, jsonify, after_this_request
from werkzeug.utils import secure_filename
from converters.router import ConverterRouter
import uuid
import threading
import time
from pathlib import Path

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
app.config['SECRET_KEY'] = os.urandom(24)

# Erstelle Ordner
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)

# Globale Session-Status-Speicher
sessions = {}

class ConversionSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        self.output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
        self.files = []
        self.converted_files = []
        self.status = 'processing'
        self.progress = 0
        self.total_files = 0
        self.processed_files = 0
        self.errors = []
        
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def add_file(self, filename, filepath):
        self.files.append({
            'name': filename,
            'path': filepath,
            'status': 'pending'
        })
        self.total_files += 1
    
    def update_progress(self):
        self.progress = int((self.processed_files / self.total_files) * 100) if self.total_files > 0 else 0
    
    def get_status(self):
        return {
            'status': self.status,
            'progress': self.progress,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'files': self.files,
            'converted_files': self.converted_files,
            'errors': self.errors
        }

def is_ignored(filename):
    """Überprüft ob eine Datei ignoriert werden soll"""
    ignored_patterns = [
        '.pyc', '.dll', '.exe', '.so',
        '__pycache__', '.git', '.venv', 'venv',
        '.DS_Store', 'Thumbs.db'
    ]
    
    for pattern in ignored_patterns:
        if pattern in filename:
            return True
    return False

def process_zip_file(zip_path, session):
    """Extrahiert eine ZIP-Datei und fügt die enthaltenen Dateien zur Session hinzu"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            extract_dir = os.path.join(session.upload_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            zip_ref.extractall(extract_dir)
            
            # Verarbeite alle extrahierten Dateien
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, extract_dir)
                    
                    if not is_ignored(rel_path):
                        # Kopiere Datei in den Upload-Ordner
                        dest_path = os.path.join(session.upload_dir, rel_path)
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        shutil.copy2(file_path, dest_path)
                        session.add_file(rel_path, dest_path)
            
            # Lösche temporären Extraktionsordner
            shutil.rmtree(extract_dir)
            
    except Exception as e:
        session.errors.append(f"Fehler beim Entpacken von {zip_path}: {str(e)}")

def process_session(session_id):
    """Verarbeitet alle Dateien in einer Session"""
    session = sessions.get(session_id)
    if not session:
        return
    
    router = ConverterRouter()
    
    try:
        # Verarbeite alle Dateien
        for file_info in session.files:
            try:
                file_path = file_info['path']
                file_name = file_info['name']
                
                # Prüfe ob Datei konvertiert werden kann
                if router.can_convert(file_name):
                    # Konvertiere Datei
                    output_path = os.path.join(session.output_dir, f"{os.path.splitext(file_name)[0]}.txt")
                    success = router.convert(file_path, output_path)
                    
                    if success and os.path.exists(output_path):
                        session.converted_files.append({
                            'original': file_name,
                            'converted': os.path.basename(output_path)
                        })
                        file_info['status'] = 'success'
                    else:
                        file_info['status'] = 'error'
                        session.errors.append(f"Fehler beim Konvertieren von {file_name}")
                else:
                    file_info['status'] = 'skipped'
                    
            except Exception as e:
                file_info['status'] = 'error'
                session.errors.append(f"Fehler bei {file_info['name']}: {str(e)}")
            
            session.processed_files += 1
            session.update_progress()
            
        session.status = 'completed'
        
    except Exception as e:
        session.status = 'error'
        session.errors.append(f"Allgemeiner Fehler: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Verarbeitet Datei-Uploads"""
    session_id = str(uuid.uuid4())
    session = ConversionSession(session_id)
    sessions[session_id] = session
    
    files = request.files.getlist('files')
    
    for file in files:
        if file.filename == '':
            continue
            
        filename = secure_filename(file.filename)
        
        # Prüfe ob Datei ignoriert werden soll
        if is_ignored(filename):
            continue
            
        file_path = os.path.join(session.upload_dir, filename)
        file.save(file_path)
        
        # Prüfe ob es eine ZIP-Datei ist
        if filename.lower().endswith('.zip'):
            process_zip_file(file_path, session)
        else:
            session.add_file(filename, file_path)
    
    # Starte Verarbeitung in Hintergrund-Thread
    thread = threading.Thread(target=process_session, args=(session_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'session_id': session_id})

@app.route('/status/<session_id>')
def get_status(session_id):
    """Gibt den aktuellen Verarbeitungsstatus zurück"""
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session nicht gefunden'}), 404
    
    return jsonify(session.get_status())

@app.route('/download/<session_id>')
def download_files(session_id):
    """Lädt alle konvertierten Dateien als ZIP herunter"""
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session nicht gefunden'}), 404
    
    if session.status != 'completed':
        return jsonify({'error': 'Konvertierung noch nicht abgeschlossen'}), 400
    
    # Erstelle ZIP-Datei
    zip_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}.zip")
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for converted_file in session.converted_files:
            file_path = os.path.join(session.output_dir, converted_file['converted'])
            if os.path.exists(file_path):
                zipf.write(file_path, converted_file['converted'])
    
    # Lösche Session nach Download
    @after_this_request
    def cleanup(response):
        try:
            # Lösche temporäre Dateien
            shutil.rmtree(session.upload_dir, ignore_errors=True)
            shutil.rmtree(session.output_dir, ignore_errors=True)
            os.remove(zip_path)
            del sessions[session_id]
        except:
            pass
        return response
    
    return send_file(zip_path, as_attachment=True, download_name=f"converted_files_{session_id}.zip")

@app.route('/download/<session_id>/<filename>')
def download_single_file(session_id, filename):
    """Lädt eine einzelne konvertierte Datei herunter"""
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session nicht gefunden'}), 404
    
    file_path = os.path.join(session.output_dir, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Datei nicht gefunden'}), 404
    
    return send_file(file_path, as_attachment=True)

@app.route('/preview/<session_id>/<filename>')
def preview_file(session_id, filename):
    """Zeigt eine Vorschau der konvertierten Datei"""
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session nicht gefunden'}), 404
    
    file_path = os.path.join(session.output_dir, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Datei nicht gefunden'}), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Begrenze Vorschau auf 1000 Zeichen
            if len(content) > 1000:
                content = content[:1000] + '...'
            return jsonify({'content': content})
    except:
        return jsonify({'error': 'Vorschau nicht verfügbar'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5001)