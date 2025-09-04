# ================================
# services/pdf_converter.py - Service de conversion PDF
# ================================

import os
import tempfile
import io
from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF
from pdf2docx import Converter
import subprocess

class PDFConverter:
    """Service pour convertir des fichiers PDF"""
    
    def __init__(self):
        self.supported_image_formats = ['PNG', 'JPEG', 'JPG', 'TIFF', 'BMP']
        self.supported_doc_formats = ['DOCX', 'DOC']
    
    def pdf_to_images(self, input_path, output_dir, format='PNG', dpi=150):
        """
        Convertit un PDF en images
        
        Args:
            input_path: Chemin du fichier PDF source
            output_dir: Dossier de sortie pour les images
            format: Format des images ('PNG', 'JPEG', 'TIFF', 'BMP')
            dpi: Résolution des images (150 par défaut)
        
        Returns:
            list: Liste des chemins des images générées
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Le fichier {input_path} n'existe pas")
            
            if format.upper() not in self.supported_image_formats:
                raise ValueError(f"Format non supporté: {format}. Utilisez: {self.supported_image_formats}")
            
            # Créer le dossier de sortie s'il n'existe pas
            os.makedirs(output_dir, exist_ok=True)
            
            # Ouvrir le PDF avec PyMuPDF
            pdf_document = fitz.open(input_path)
            image_paths = []
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                
                # Convertir la page en image
                mat = fitz.Matrix(dpi/72, dpi/72)  # Matrice de transformation pour le DPI
                pix = page.get_pixmap(matrix=mat)
                
                # Générer le nom du fichier
                image_filename = f"page_{page_num + 1:03d}.{format.lower()}"
                image_path = os.path.join(output_dir, image_filename)
                
                # Sauvegarder l'image
                if format.upper() == 'PNG':
                    pix.save(image_path)
                else:
                    # Convertir en PIL Image pour les autres formats
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    img.save(image_path, format=format.upper())
                
                image_paths.append(image_path)
            
            pdf_document.close()
            return image_paths
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la conversion PDF vers images: {str(e)}")
    
    def images_to_pdf(self, image_paths, output_path, quality=95):
        """
        Convertit des images en PDF
        
        Args:
            image_paths: Liste des chemins des images
            output_path: Chemin du fichier PDF de sortie
            quality: Qualité de compression (1-100)
        
        Returns:
            bool: True si la conversion a réussi
        """
        try:
            if not image_paths:
                raise ValueError("Aucune image fournie")
            
            # Vérifier que toutes les images existent
            for image_path in image_paths:
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"L'image {image_path} n'existe pas")
            
            # Créer un nouveau PDF
            pdf_document = fitz.open()
            
            for image_path in image_paths:
                # Ouvrir l'image avec PIL
                img = Image.open(image_path)
                
                # Convertir en RGB si nécessaire
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Créer une nouvelle page dans le PDF
                page = pdf_document.new_page(width=img.width, height=img.height)
                
                # Insérer l'image dans la page
                page.insert_image(fitz.Rect(0, 0, img.width, img.height), filename=image_path)
            
            # Sauvegarder le PDF
            pdf_document.save(output_path)
            pdf_document.close()
            
            return True
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la conversion images vers PDF: {str(e)}")
    
    def pdf_to_word(self, input_path, output_path):
        """
        Convertit un PDF en document Word
        
        Args:
            input_path: Chemin du fichier PDF source
            output_path: Chemin du fichier Word de sortie
        
        Returns:
            bool: True si la conversion a réussi
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Le fichier {input_path} n'existe pas")
            
            # Utiliser pdf2docx pour la conversion
            cv = Converter(input_path)
            cv.convert(output_path, start=0, end=None)
            cv.close()
            
            return True
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la conversion PDF vers Word: {str(e)}")
    
    def pdf_to_text(self, input_path, output_path=None):
        """
        Extrait le texte d'un PDF
        
        Args:
            input_path: Chemin du fichier PDF source
            output_path: Chemin du fichier texte de sortie (optionnel)
        
        Returns:
            str ou bool: Texte extrait ou True si sauvegardé dans un fichier
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Le fichier {input_path} n'existe pas")
            
            # Ouvrir le PDF avec PyMuPDF
            pdf_document = fitz.open(input_path)
            text_content = ""
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                text_content += page.get_text()
                text_content += "\n\n"  # Séparateur entre les pages
            
            pdf_document.close()
            
            if output_path:
                # Sauvegarder dans un fichier
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                return True
            else:
                # Retourner le texte
                return text_content
                
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'extraction de texte: {str(e)}")
    
    def get_pdf_info(self, input_path):
        """
        Obtient des informations sur un fichier PDF
        
        Args:
            input_path: Chemin du fichier PDF
        
        Returns:
            dict: Informations sur le PDF
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Le fichier {input_path} n'existe pas")
            
            pdf_document = fitz.open(input_path)
            
            info = {
                'page_count': pdf_document.page_count,
                'file_size_mb': round(os.path.getsize(input_path) / (1024 * 1024), 2),
                'metadata': pdf_document.metadata,
                'is_encrypted': pdf_document.is_encrypted,
                'is_pdf': pdf_document.is_pdf
            }
            
            pdf_document.close()
            return info
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'analyse du PDF: {str(e)}")