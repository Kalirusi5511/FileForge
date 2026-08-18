"""
AI File Platform
=================
Flask-Webanwendung, die (fast) jedes Dateiformat automatisch in Text
umwandelt: PDF, Bilder (OCR), Audio (Whisper), Video (Whisper),
DOCX, XLSX, ZIP-Archive (rekursiv entpacken & verarbeiten).

Start lokal:
    pip install -r requirements.txt
    python app.py

Deployment auf Render:
    siehe README.md
"""

import os
import uuid
import shutil
import zipfile
from pathlib import Path

from flask import (
    Flask, request, render_template, send_from_directory,
    redirect, url_for, flash, jsonify
)
from werkzeug.utils import secure_filename

from converters import pdf as pdf_conv
from converters import image as image_conv
from converters import audio as audio_conv
from converters import video as video_conv
from converters import office as office_conv
from converters import archive as archive_conv
from duplicate_finder.finder import find_duplicates
from feedback import feedback_bp
from feedback import init_mail

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB Upload-Limit

app = Flask(__name__)

init_mail(app)

app.register_blueprint(feedback_bp)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "dev-secret-change-me"
)

app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# Dateiendung -> Konverter-Funktion (jede Funktion nimmt einen Pfad
# und gibt extrahierten Text als String zurück)
CONVERTERS = {
    ".pdf": pdf_conv.pdf_to_text,
    ".png": image_conv.image_to_text,
    ".jpg": image_conv.image_to_text,
    ".jpeg": image_conv.image_to_text,
    ".bmp": image_conv.image_to_text,
    ".tiff": image_conv.image_to_text,
    ".gif": image_conv.image_to_text,
    ".mp3": audio_conv.audio_to_text,
    ".wav": audio_conv.audio_to_text,
    ".m4a": audio_conv.audio_to_text,
    ".flac": audio_conv.audio_to_text,
    ".ogg": audio_conv.audio_to_text,
    ".mp4": video_conv.video_to_text,
    ".mov": video_conv.video_to_text,
    ".avi": video_conv.video_to_text,
    ".mkv": video_conv.video_to_text,
    ".webm": video_conv.video_to_text,
    ".docx": office_conv.docx_to_text,
    ".xlsx": office_conv.xlsx_to_text,
    ".csv": office_conv.csv_to_text,
    ".odt": office_conv.odt_to_text,
}

ARCHIVE_EXTENSIONS = {".zip"}


def get_converter(filepath: Path):
    return CONVERTERS.get(filepath.suffix.lower())


def process_single_file(filepath: Path, results: list, errors: list):
    """Verarbeitet eine einzelne Datei und hängt das Ergebnis an results an."""
    converter = get_converter(filepath)
    if converter is None:
        errors.append(f"{filepath.name}: Kein Konverter für dieses Format gefunden.")
        return
    try:
        text = converter(str(filepath))
        results.append({"filename": filepath.name, "text": text})
    except Exception as exc:  # bewusst breit, damit ein Fehler nicht den ganzen Batch stoppt
        errors.append(f"{filepath.name}: {exc}")


def process_path(filepath: Path, results: list, errors: list):
    """Verarbeitet eine Datei ODER, falls es ein Archiv ist, entpackt es rekursiv."""
    if filepath.suffix.lower() in ARCHIVE_EXTENSIONS:
        extract_dir = filepath.parent / (filepath.stem + "_extracted")
        try:
            archive_conv.extract_zip(str(filepath), str(extract_dir))
        except Exception as exc:
            errors.append(f"{filepath.name}: Entpacken fehlgeschlagen ({exc})")
            return
        for root, _, files in os.walk(extract_dir):
            for fname in files:
                process_path(Path(root) / fname, results, errors)
    else:
        process_single_file(filepath, results, errors)


@app.route("/feedback-page")
def feedback_page():

    return render_template(
        "feedback.html"
    )

@app.route("/upload", methods=["POST"])
def upload():
    if "files" not in request.files:
        flash("Keine Dateien ausgewählt.")
        return redirect(url_for("index"))

    files = request.files.getlist("files")
    if not files or files[0].filename == "":
        flash("Keine Dateien ausgewählt.")
        return redirect(url_for("index"))

    session_id = uuid.uuid4().hex[:12]
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    for f in files:
        filename = secure_filename(f.filename)
        if not filename:
            continue
        dest = session_dir / filename
        f.save(dest)
        saved_paths.append(dest)

    results, errors = [], []
    for p in saved_paths:
        process_path(p, results, errors)

    # Kombinierten Text als .txt-Datei zum Download bereitstellen
    combined_txt_path = OUTPUT_DIR / f"{session_id}.txt"
    with open(combined_txt_path, "w", encoding="utf-8") as out:
        for r in results:
            out.write(f"\n{'=' * 60}\nDATEI: {r['filename']}\n{'=' * 60}\n\n")
            out.write(r["text"])
            out.write("\n")

    # Aufräumen der Upload-Session (Originaldateien werden nicht mehr gebraucht)
    shutil.rmtree(session_dir, ignore_errors=True)

    return render_template(
        "results.html",
        results=results,
        errors=errors,
        download_name=f"{session_id}.txt",
    )


@app.route("/download/<name>")
def download(name):
    safe_name = secure_filename(name)
    return send_from_directory(OUTPUT_DIR, safe_name, as_attachment=True)


@app.route("/duplicates", methods=["GET", "POST"])
def duplicates():
    if request.method == "GET":
        return render_template("duplicates.html", groups=None)

    files = request.files.getlist("files")
    if not files or files[0].filename == "":
        flash("Keine Dateien ausgewählt.")
        return redirect(url_for("duplicates"))

    session_id = uuid.uuid4().hex[:12]
    session_dir = UPLOAD_DIR / ("dup_" + session_id)
    session_dir.mkdir(parents=True, exist_ok=True)

    for f in files:
        filename = secure_filename(f.filename)
        if filename:
            f.save(session_dir / filename)

    groups = find_duplicates(str(session_dir))
    shutil.rmtree(session_dir, ignore_errors=True)

    return render_template("duplicates.html", groups=groups)


@app.route("/api/convert", methods=["POST"])
def api_convert():
    """JSON-API: einzelne Datei hochladen, extrahierten Text als JSON zurückbekommen."""
    if "file" not in request.files:
        return jsonify({"error": "Kein Feld 'file' im Request gefunden."}), 400

    f = request.files["file"]
    filename = secure_filename(f.filename)
    if not filename:
        return jsonify({"error": "Ungültiger Dateiname."}), 400

    session_id = uuid.uuid4().hex[:12]
    session_dir = UPLOAD_DIR / ("api_" + session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    dest = session_dir / filename
    f.save(dest)

    results, errors = [], []
    process_path(dest, results, errors)
    shutil.rmtree(session_dir, ignore_errors=True)

    if errors and not results:
        return jsonify({"error": errors[0]}), 422

    return jsonify({"results": results, "errors": errors})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
