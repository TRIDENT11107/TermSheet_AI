"""
PDF processing utilities for TermSheet AI
"""
import logging
import io

logger = logging.getLogger(__name__)

try:
    import PyPDF2
    PDF_SUPPORT_AVAILABLE = True
    logger.info("PyPDF2 is available for PDF processing")
except ImportError:
    PDF_SUPPORT_AVAILABLE = False
    logger.warning("PyPDF2 not available. PDF processing will be limited.")

def extract_text_from_pdf(file_stream):
    """
    Extract text from a PDF file using PyPDF2
    
    Args:
        file_stream: A file-like object containing the PDF
        
    Returns:
        str: Extracted text from the PDF
    """
    if not PDF_SUPPORT_AVAILABLE:
        logger.error("PDF processing not available - PyPDF2 not installed")
        return "PDF processing not available. Please install PyPDF2."
    
    try:
        # Save the current position of the file stream
        current_position = file_stream.tell()
        
        # Read the first few bytes to check if it's a PDF
        header = file_stream.read(5)
        file_stream.seek(current_position)  # Reset to the original position
        
        if header != b'%PDF-':
            logger.error(f"File does not appear to be a valid PDF. Header: {header}")
            return "The file does not appear to be a valid PDF document."
        
        # Create a copy of the stream to avoid issues with PyPDF2
        stream_copy = io.BytesIO(file_stream.read())
        file_stream.seek(current_position)  # Reset the original stream
        
        # Create a PDF reader object
        logger.debug("Creating PDF reader object")
        pdf_reader = PyPDF2.PdfReader(stream_copy)
        
        # Extract text from all pages
        logger.debug(f"Extracting text from PDF with {len(pdf_reader.pages)} pages")
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            logger.debug(f"Processing page {page_num+1}")
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            text += page_text + "\n\n"
        
        if not text.strip():
            logger.warning("No text could be extracted from the PDF")
            return "No text could be extracted from the PDF. It may be scanned or contain only images."
            
        logger.debug(f"Successfully extracted {len(text)} characters from PDF")
        return text
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        return f"Error processing PDF: {str(e)}"
