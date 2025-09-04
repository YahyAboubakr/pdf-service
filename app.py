# app.py - Application Flask principale
from flask import Flask, request, render_template, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import tempfile
from datetime import datetime
import uuid

# Import des services PDF
from services.pdf_merger import PDFMerger
from services.pdf_compressor import PDFCompressor  # À implémenter
from services.pdf_converter import PDFConverter    # À implémenter

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Configuration des dossiers
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'pdf'}

# Créer les dossiers s'ils n'existent pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_old_files():
    """Nettoie les fichiers temporaires plus anciens que 1 heure"""
    import time
    current_time = time.time()
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath):
                if current_time - os.path.getmtime(filepath) > 3600:  # 1 heure
                    os.remove(filepath)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge', methods=['GET', 'POST'])
def merge_pdfs():
    if request.method == 'GET':
        return render_template('merge.html')
    
    # Vérifier si des fichiers ont été uploadés
    if 'files[]' not in request.files:
        flash('Aucun fichier sélectionné')
        return redirect(request.url)
    
    files = request.files.getlist('files[]')
    
    if len(files) < 2:
        flash('Au moins 2 fichiers PDF sont requis pour la fusion')
        return redirect(request.url)
    
    # Sauvegarder les fichiers uploadés
    uploaded_files = []
    session_id = str(uuid.uuid4())
    
    try:
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Ajouter timestamp pour éviter les conflits
                unique_filename = f"{session_id}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(filepath)
                uploaded_files.append(filepath)
        
        if len(uploaded_files) < 2:
            flash('Au moins 2 fichiers PDF valides sont requis')
            return redirect(request.url)
        
        # Fusionner les PDF
        merger = PDFMerger()
        output_filename = f"merged_{session_id}.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        merger.merge_pdfs(uploaded_files, output_path)
        
        # Nettoyer les fichiers uploadés
        for filepath in uploaded_files:
            if os.path.exists(filepath):
                os.remove(filepath)
        
        return send_file(output_path, as_attachment=True, download_name=f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    
    except Exception as e:
        # Nettoyer en cas d'erreur
        for filepath in uploaded_files:
            if os.path.exists(filepath):
                os.remove(filepath)
        flash(f'Erreur lors de la fusion: {str(e)}')
        return redirect(request.url)

# Route pour futures fonctionnalités
@app.route('/compress')
def compress():
    return render_template('compress.html')

@app.route('/convert')
def convert():
    return render_template('convert.html')

if __name__ == '__main__':
    cleanup_old_files()  # Nettoyer au démarrage
    app.run(debug=True)