# ================================
# services/pdf_splitter.py - Service de division PDF
# ================================

import os
import fitz  # PyMuPDF
from pathlib import Path

class PDFSplitter:
    """Service pour diviser des fichiers PDF"""
    
    def __init__(self):
        self.supported_split_methods = ['pages', 'range', 'every_n_pages']
    
    def split_by_pages(self, input_path, output_dir, page_numbers):
        """
        Divise un PDF en pages individuelles
        
        Args:
            input_path: Chemin du fichier PDF source
            output_dir: Dossier de sortie pour les pages
            page_numbers: Liste des numéros de pages à extraire (1-indexé)
        
        Returns:
            list: Liste des chemins des fichiers générés
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Le fichier {input_path} n'existe pas")
            
            # Créer le dossier de sortie s'il n'existe pas
            os.makedirs(output_dir, exist_ok=True)
            
            # Ouvrir le PDF source
            pdf_document = fitz.open(input_path)
            output_files = []
            
            # Vérifier que tous les numéros de pages sont valides
            max_pages = pdf_document.page_count
            for page_num in page_numbers:
                if page_num < 1 or page_num > max_pages:
                    raise ValueError(f"Numéro de page invalide: {page_num}. Le PDF contient {max_pages} pages.")
            
            # Extraire chaque page
            for page_num in page_numbers:
                # Créer un nouveau PDF avec une seule page
                new_pdf = fitz.open()
                new_pdf.insert_pdf(pdf_document, from_page=page_num-1, to_page=page_num-1)
                
                # Nom du fichier de sortie
                output_filename = f"page_{page_num:03d}.pdf"
                output_path = os.path.join(output_dir, output_filename)
                
                # Sauvegarder le PDF
                new_pdf.save(output_path)
                new_pdf.close()
                
                output_files.append(output_path)
            
            pdf_document.close()
            return output_files
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la division par pages: {str(e)}")
    
    def split_by_range(self, input_path, output_dir, ranges):
        """
        Divise un PDF en plages de pages
        
        Args:
            input_path: Chemin du fichier PDF source
            output_dir: Dossier de sortie pour les plages
            ranges: Liste de tuples (start, end) pour les plages (1-indexé)
        
        Returns:
            list: Liste des chemins des fichiers générés
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Le fichier {input_path} n'existe pas")
            
            # Créer le dossier de sortie s'il n'existe pas
            os.makedirs(output_dir, exist_ok=True)
            
            # Ouvrir le PDF source
            pdf_document = fitz.open(input_path)
            output_files = []
            max_pages = pdf_document.page_count
            
            # Vérifier et traiter chaque plage
            for i, (start, end) in enumerate(ranges):
                if start < 1 or end > max_pages or start > end:
                    raise ValueError(f"Plage invalide: {start}-{end}. Le PDF contient {max_pages} pages.")
                
                # Créer un nouveau PDF avec la plage de pages
                new_pdf = fitz.open()
                new_pdf.insert_pdf(pdf_document, from_page=start-1, to_page=end-1)
                
                # Nom du fichier de sortie
                output_filename = f"pages_{start:03d}-{end:03d}.pdf"
                output_path = os.path.join(output_dir, output_filename)
                
                # Sauvegarder le PDF
                new_pdf.save(output_path)
                new_pdf.close()
                
                output_files.append(output_path)
            
            pdf_document.close()
            return output_files
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la division par plages: {str(e)}")
    
    def split_every_n_pages(self, input_path, output_dir, n_pages):
        """
        Divise un PDF en fichiers de N pages chacun
        
        Args:
            input_path: Chemin du fichier PDF source
            output_dir: Dossier de sortie pour les fichiers
            n_pages: Nombre de pages par fichier
        
        Returns:
            list: Liste des chemins des fichiers générés
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Le fichier {input_path} n'existe pas")
            
            if n_pages < 1:
                raise ValueError("Le nombre de pages par fichier doit être supérieur à 0")
            
            # Créer le dossier de sortie s'il n'existe pas
            os.makedirs(output_dir, exist_ok=True)
            
            # Ouvrir le PDF source
            pdf_document = fitz.open(input_path)
            output_files = []
            total_pages = pdf_document.page_count
            
            # Calculer le nombre de fichiers nécessaires
            num_files = (total_pages + n_pages - 1) // n_pages  # Arrondi vers le haut
            
            for i in range(num_files):
                start_page = i * n_pages
                end_page = min((i + 1) * n_pages - 1, total_pages - 1)
                
                # Créer un nouveau PDF avec les pages de cette plage
                new_pdf = fitz.open()
                new_pdf.insert_pdf(pdf_document, from_page=start_page, to_page=end_page)
                
                # Nom du fichier de sortie
                output_filename = f"part_{i+1:03d}_pages_{start_page+1:03d}-{end_page+1:03d}.pdf"
                output_path = os.path.join(output_dir, output_filename)
                
                # Sauvegarder le PDF
                new_pdf.save(output_path)
                new_pdf.close()
                
                output_files.append(output_path)
            
            pdf_document.close()
            return output_files
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la division par groupes: {str(e)}")
    
    def split_by_bookmarks(self, input_path, output_dir):
        """
        Divise un PDF selon les signets (bookmarks)
        
        Args:
            input_path: Chemin du fichier PDF source
            output_dir: Dossier de sortie pour les fichiers
        
        Returns:
            list: Liste des chemins des fichiers générés
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Le fichier {input_path} n'existe pas")
            
            # Créer le dossier de sortie s'il n'existe pas
            os.makedirs(output_dir, exist_ok=True)
            
            # Ouvrir le PDF source
            pdf_document = fitz.open(input_path)
            output_files = []
            
            # Obtenir la table des matières
            toc = pdf_document.get_toc()
            
            if not toc:
                raise ValueError("Ce PDF ne contient pas de signets (table des matières)")
            
            # Traiter chaque signet
            for i, (level, title, page_num) in enumerate(toc):
                # Nettoyer le titre pour le nom de fichier
                clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                clean_title = clean_title.replace(' ', '_')[:50]  # Limiter la longueur
                
                # Déterminer la page de fin
                if i + 1 < len(toc):
                    end_page = toc[i + 1][2] - 1
                else:
                    end_page = pdf_document.page_count - 1
                
                # Créer un nouveau PDF avec les pages de cette section
                new_pdf = fitz.open()
                new_pdf.insert_pdf(pdf_document, from_page=page_num-1, to_page=end_page)
                
                # Nom du fichier de sortie
                output_filename = f"section_{i+1:03d}_{clean_title}.pdf"
                output_path = os.path.join(output_dir, output_filename)
                
                # Sauvegarder le PDF
                new_pdf.save(output_path)
                new_pdf.close()
                
                output_files.append(output_path)
            
            pdf_document.close()
            return output_files
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la division par signets: {str(e)}")
    
    def get_pdf_info(self, input_path):
        """
        Obtient des informations sur un fichier PDF pour la division
        
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
                'has_bookmarks': len(pdf_document.get_toc()) > 0,
                'bookmarks': pdf_document.get_toc(),
                'is_encrypted': pdf_document.is_encrypted,
                'is_pdf': pdf_document.is_pdf
            }
            
            pdf_document.close()
            return info
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'analyse du PDF: {str(e)}")
