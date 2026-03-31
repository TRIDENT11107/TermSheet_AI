try:
    import pytesseract
    from PIL import Image
    import numpy as np
    import cv2
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("Warning: OCR dependencies not available. OCR functionality will be limited.")

def extract_text_from_image(file_stream):
    """Extract text from image using Tesseract OCR"""
    if not DEPENDENCIES_AVAILABLE:
        return "OCR processing not available. Please install pytesseract, PIL, numpy, and opencv-python."
    
    try:
        img = Image.open(file_stream).convert('RGB')
        img_np = np.array(img)
        
        # Preprocess image for better OCR
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Extract text
        text = pytesseract.image_to_string(thresh)
        return text
    except Exception as e:
        return f"Error processing image: {str(e)}"
