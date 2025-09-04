# ================================
# services/pdf_converter.py - Service de conversion (structure pour future implémentation)
# ================================

class PDFConverter:
    """Service pour convertir des fichiers PDF"""
    
    def pdf_to_images(self, input_path, output_dir, format='PNG'):
        """Convertit un PDF en images"""
        # À implémenter avec pdf2image
        pass
    
    def images_to_pdf(self, image_paths, output_path):
        """Convertit des images en PDF"""
        # À implémenter avec PIL/Pillow
        pass
    
    def pdf_to_word(self, input_path, output_path):
        """Convertit un PDF en document Word"""
        # À implémenter avec pdf2docx
        pass