# ================================
# services/pdf_compressor.py - Service de compression PDF
# ================================

import os
import subprocess
import tempfile
from pathlib import Path

class PDFCompressor:
    """Service pour compresser des fichiers PDF"""
    
    def __init__(self):
        self.quality_settings = {
            'low': {
                'dpi': 72,
                'gs_options': ['-dPDFSETTINGS=/screen', '-dCompatibilityLevel=1.4']
            },
            'medium': {
                'dpi': 150,
                'gs_options': ['-dPDFSETTINGS=/ebook', '-dCompatibilityLevel=1.4']
            },
            'high': {
                'dpi': 300,
                'gs_options': ['-dPDFSETTINGS=/printer', '-dCompatibilityLevel=1.4']
            }
        }
    
    def compress_pdf(self, input_path, output_path, quality='medium'):
        """
        Compresse un fichier PDF en utilisant Ghostscript
        
        Args:
            input_path: Chemin du fichier PDF source
            output_path: Chemin du fichier compressé
            quality: Niveau de qualité ('low', 'medium', 'high')
        
        Returns:
            bool: True si la compression a réussi, False sinon
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Le fichier {input_path} n'existe pas")
            
            if quality not in self.quality_settings:
                raise ValueError(f"Qualité non supportée: {quality}. Utilisez: {list(self.quality_settings.keys())}")
            
            # Vérifier si Ghostscript est installé
            if not self._check_ghostscript():
                raise RuntimeError("Ghostscript n'est pas installé sur le système")
            
            settings = self.quality_settings[quality]
            
            # Commande Ghostscript pour la compression
            cmd = [
                'gs',
                '-sDEVICE=pdfwrite',
                '-dCompatibilityLevel=1.4',
                '-dPDFSETTINGS=/ebook' if quality == 'medium' else f'-dPDFSETTINGS=/{quality}',
                '-dNOPAUSE',
                '-dQUIET',
                '-dBATCH',
                '-dColorImageDownsampleType=/Bicubic',
                '-dColorImageResolution=150',
                '-dGrayImageDownsampleType=/Bicubic',
                '-dGrayImageResolution=150',
                '-dMonoImageDownsampleType=/Bicubic',
                '-dMonoImageResolution=150',
                f'-sOutputFile={output_path}',
                input_path
            ]
            
            # Exécuter la commande
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise RuntimeError(f"Erreur Ghostscript: {result.stderr}")
            
            if not os.path.exists(output_path):
                raise RuntimeError("Le fichier compressé n'a pas été créé")
            
            return True
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("La compression a pris trop de temps")
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la compression: {str(e)}")
    
    def _check_ghostscript(self):
        """Vérifie si Ghostscript est installé"""
        try:
            subprocess.run(['gs', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_compression_info(self, input_path):
        """
        Obtient des informations sur le fichier PDF pour estimer la compression
        
        Args:
            input_path: Chemin du fichier PDF
            
        Returns:
            dict: Informations sur le fichier
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Le fichier {input_path} n'existe pas")
            
            file_size = os.path.getsize(input_path)
            
            return {
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'file_size_bytes': file_size,
                'estimated_compression': {
                    'low': f"{round(file_size * 0.3 / (1024 * 1024), 2)} MB",
                    'medium': f"{round(file_size * 0.5 / (1024 * 1024), 2)} MB",
                    'high': f"{round(file_size * 0.8 / (1024 * 1024), 2)} MB"
                }
            }
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'analyse du fichier: {str(e)}")
