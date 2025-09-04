# ================================
# services/pdf_merger.py - Service de fusion PDF
# ================================

import PyPDF2
from PyPDF2 import PdfWriter, PdfReader
import os

class PDFMerger:
    """Service pour fusionner des fichiers PDF"""
    
    def merge_pdfs(self, input_files, output_path):
        """
        Fusionne plusieurs fichiers PDF en un seul
        
        Args:
            input_files: Liste des chemins des fichiers PDF à fusionner
            output_path: Chemin du fichier de sortie
        """
        try:
            merger = PdfWriter()
            
            for pdf_file in input_files:
                if not os.path.exists(pdf_file):
                    raise FileNotFoundError(f"Fichier non trouvé: {pdf_file}")
                
                with open(pdf_file, 'rb') as file:
                    reader = PdfReader(file)
                    
                    # Vérifier que le PDF n'est pas corrompu
                    if reader.is_encrypted:
                        raise ValueError(f"PDF crypté non supporté: {pdf_file}")
                    
                    # Ajouter toutes les pages
                    for page in reader.pages:
                        merger.add_page(page)
            
            # Écrire le fichier fusionné
            with open(output_path, 'wb') as output_file:
                merger.write(output_file)
            
            merger.close()
            return True
            
        except Exception as e:
            raise Exception(f"Erreur lors de la fusion PDF: {str(e)}")
