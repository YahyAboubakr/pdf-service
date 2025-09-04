from flask import Flask, request, render_template, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import tempfile
from datetime import datetime
import uuid

# Import des services PDF
from services.pdf_merger import PDFMerger
from services.pdf_compressor import PDFCompressor
from services.pdf_converter import PDFConverter
from services.pdf_splitter import PDFSplitter

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

# Route pour la compression PDF
@app.route('/compress', methods=['GET', 'POST'])
def compress():
    if request.method == 'GET':
        return render_template('compress.html')
    
    # Vérifier si un fichier a été uploadé
    if 'file' not in request.files:
        flash('Aucun fichier sélectionné')
        return redirect(request.url)
    
    file = request.files['file']
    quality = request.form.get('quality', 'medium')
    
    if file.filename == '':
        flash('Aucun fichier sélectionné')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        session_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        unique_filename = f"{session_id}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        try:
            # Sauvegarder le fichier uploadé
            file.save(filepath)
            
            # Compresser le PDF
            compressor = PDFCompressor()
            output_filename = f"compressed_{session_id}.pdf"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            
            compressor.compress_pdf(filepath, output_path, quality)
            
            # Nettoyer le fichier uploadé
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return send_file(output_path, as_attachment=True, 
                           download_name=f"compressed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        
        except Exception as e:
            # Nettoyer en cas d'erreur
            if os.path.exists(filepath):
                os.remove(filepath)
            flash(f'Erreur lors de la compression: {str(e)}')
            return redirect(request.url)
    
    flash('Fichier non valide. Seuls les fichiers PDF sont acceptés.')
    return redirect(request.url)

# Route pour la conversion PDF
@app.route('/convert', methods=['GET', 'POST'])
def convert():
    if request.method == 'GET':
        return render_template('convert.html')
    
    # Vérifier si un fichier a été uploadé
    if 'file' not in request.files:
        flash('Aucun fichier sélectionné')
        return redirect(request.url)
    
    file = request.files['file']
    conversion_type = request.form.get('conversion_type', 'images')
    format_type = request.form.get('format', 'PNG')
    
    if file.filename == '':
        flash('Aucun fichier sélectionné')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        session_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        unique_filename = f"{session_id}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        try:
            # Sauvegarder le fichier uploadé
            file.save(filepath)
            
            converter = PDFConverter()
            
            if conversion_type == 'images':
                # Convertir PDF en images
                output_dir = os.path.join(OUTPUT_FOLDER, f"images_{session_id}")
                image_paths = converter.pdf_to_images(filepath, output_dir, format_type)
                
                # Créer une archive ZIP des images
                import zipfile
                zip_filename = f"images_{session_id}.zip"
                zip_path = os.path.join(OUTPUT_FOLDER, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for image_path in image_paths:
                        zipf.write(image_path, os.path.basename(image_path))
                
                # Nettoyer les fichiers temporaires
                if os.path.exists(filepath):
                    os.remove(filepath)
                for image_path in image_paths:
                    if os.path.exists(image_path):
                        os.remove(image_path)
                if os.path.exists(output_dir):
                    os.rmdir(output_dir)
                
                return send_file(zip_path, as_attachment=True, 
                               download_name=f"images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
            
            elif conversion_type == 'word':
                # Convertir PDF en Word
                output_filename = f"converted_{session_id}.docx"
                output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                
                converter.pdf_to_word(filepath, output_path)
                
                # Nettoyer le fichier uploadé
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                return send_file(output_path, as_attachment=True, 
                               download_name=f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx")
            
            elif conversion_type == 'text':
                # Extraire le texte du PDF
                output_filename = f"extracted_text_{session_id}.txt"
                output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                
                converter.pdf_to_text(filepath, output_path)
                
                # Nettoyer le fichier uploadé
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                return send_file(output_path, as_attachment=True, 
                               download_name=f"extracted_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        except Exception as e:
            # Nettoyer en cas d'erreur
            if os.path.exists(filepath):
                os.remove(filepath)
            flash(f'Erreur lors de la conversion: {str(e)}')
            return redirect(request.url)
    
    flash('Fichier non valide. Seuls les fichiers PDF sont acceptés.')
    return redirect(request.url)

# Route pour obtenir des informations sur un PDF
@app.route('/info', methods=['GET', 'POST'])
def pdf_info():
    if request.method == 'GET':
        return render_template('info.html')
    
    if 'file' not in request.files:
        flash('Aucun fichier sélectionné')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('Aucun fichier sélectionné')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        session_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        unique_filename = f"{session_id}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        try:
            # Sauvegarder le fichier uploadé
            file.save(filepath)
            
            converter = PDFConverter()
            info = converter.get_pdf_info(filepath)
            
            # Nettoyer le fichier uploadé
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return render_template('info_result.html', info=info)
        
        except Exception as e:
            # Nettoyer en cas d'erreur
            if os.path.exists(filepath):
                os.remove(filepath)
            flash(f'Erreur lors de l\'analyse: {str(e)}')
            return redirect(request.url)
    
    flash('Fichier non valide. Seuls les fichiers PDF sont acceptés.')
    return redirect(request.url)

# Route pour la division PDF
@app.route('/split', methods=['GET', 'POST'])
def split_pdf():
    if request.method == 'GET':
        return render_template('split.html')
    
    # Vérifier si un fichier a été uploadé
    if 'file' not in request.files:
        flash('Aucun fichier sélectionné')
        return redirect(request.url)
    
    file = request.files['file']
    split_method = request.form.get('split_method', 'pages')
    
    if file.filename == '':
        flash('Aucun fichier sélectionné')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        session_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        unique_filename = f"{session_id}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        try:
            # Sauvegarder le fichier uploadé
            file.save(filepath)
            
            splitter = PDFSplitter()
            output_dir = os.path.join(OUTPUT_FOLDER, f"split_{session_id}")
            
            if split_method == 'pages':
                # Division par pages spécifiques
                pages_input = request.form.get('pages', '')
                if not pages_input:
                    raise ValueError("Veuillez spécifier les numéros de pages")
                
                # Parser les numéros de pages (ex: "1,3,5-8,10")
                page_numbers = parse_page_numbers(pages_input)
                output_files = splitter.split_by_pages(filepath, output_dir, page_numbers)
                
            elif split_method == 'range':
                # Division par plages
                ranges_input = request.form.get('ranges', '')
                if not ranges_input:
                    raise ValueError("Veuillez spécifier les plages de pages")
                
                ranges = parse_page_ranges(ranges_input)
                output_files = splitter.split_by_range(filepath, output_dir, ranges)
                
            elif split_method == 'every_n_pages':
                # Division par groupes de N pages
                n_pages = int(request.form.get('n_pages', 1))
                if n_pages < 1:
                    raise ValueError("Le nombre de pages doit être supérieur à 0")
                
                output_files = splitter.split_every_n_pages(filepath, output_dir, n_pages)
                
            elif split_method == 'bookmarks':
                # Division par signets
                output_files = splitter.split_by_bookmarks(filepath, output_dir)
            
            # Créer une archive ZIP des fichiers divisés
            import zipfile
            zip_filename = f"split_{session_id}.zip"
            zip_path = os.path.join(OUTPUT_FOLDER, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for output_file in output_files:
                    zipf.write(output_file, os.path.basename(output_file))
            
            # Nettoyer les fichiers temporaires
            if os.path.exists(filepath):
                os.remove(filepath)
            for output_file in output_files:
                if os.path.exists(output_file):
                    os.remove(output_file)
            if os.path.exists(output_dir):
                os.rmdir(output_dir)
            
            return send_file(zip_path, as_attachment=True, 
                           download_name=f"split_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
        
        except Exception as e:
            # Nettoyer en cas d'erreur
            if os.path.exists(filepath):
                os.remove(filepath)
            flash(f'Erreur lors de la division: {str(e)}')
            return redirect(request.url)
    
    flash('Fichier non valide. Seuls les fichiers PDF sont acceptés.')
    return redirect(request.url)

def parse_page_numbers(pages_input):
    """Parse les numéros de pages depuis une chaîne (ex: '1,3,5-8,10')"""
    page_numbers = []
    parts = pages_input.replace(' ', '').split(',')
    
    for part in parts:
        if '-' in part:
            # Plage de pages
            start, end = map(int, part.split('-'))
            page_numbers.extend(range(start, end + 1))
        else:
            # Page unique
            page_numbers.append(int(part))
    
    return sorted(list(set(page_numbers)))  # Supprimer les doublons et trier

def parse_page_ranges(ranges_input):
    """Parse les plages de pages depuis une chaîne (ex: '1-5,10-15')"""
    ranges = []
    parts = ranges_input.replace(' ', '').split(',')
    
    for part in parts:
        if '-' in part:
            start, end = map(int, part.split('-'))
            ranges.append((start, end))
        else:
            # Page unique = plage de 1 page
            page_num = int(part)
            ranges.append((page_num, page_num))
    
    return ranges

if __name__ == '__main__':
    cleanup_old_files()  # Nettoyer au démarrage
    app.run(debug=True)