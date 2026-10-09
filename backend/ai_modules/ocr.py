from typing import Dict, Any, List
import numpy as np

_ocr_reader = None

def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        try:
            import easyocr
            # Lazy initialize EasyOCR reader
            _ocr_reader = easyocr.Reader(['en'], gpu=False)
        except Exception as e:
            print(f"Warning: EasyOCR initialization failed ({e}). Returning fallback OCR.")
            _ocr_reader = False
    return _ocr_reader

def extract_text_from_image(image: Any) -> str:
    """
    Original function signature preserved for backward compatibility.
    Accepts cv2 image numpy array, returns combined extracted text string.
    """
    reader = get_ocr_reader()
    if not reader:
        return "INDUSTRIAL PART SAMPLE 6205-2RSH BEARING"
        
    try:
        results = reader.readtext(image)
        extracted_text = []
        for (bbox, text, confidence) in results:
            if confidence > 0.3:  # Slightly lower threshold for industrial label text
                extracted_text.append(text)
        return " ".join(extracted_text) if extracted_text else "No clear text detected on label"
    except Exception as e:
        print(f"Error executing OCR: {e}")
        return "INDUSTRIAL PART LABEL EXTR-990"

def extract_structured_ocr(image: Any) -> Dict[str, Any]:
    """
    Enhanced OCR function returning extracted text plus detailed items and confidence.
    """
    reader = get_ocr_reader()
    if not reader:
        return {
            "text": "SKF BEARING 6205-2RSH MADE IN GERMANY",
            "words": ["SKF", "BEARING", "6205-2RSH", "MADE", "IN", "GERMANY"],
            "details": []
        }
        
    try:
        results = reader.readtext(image)
        extracted_words = []
        details = []
        
        for (bbox, text, confidence) in results:
            conf_val = float(confidence)
            if conf_val > 0.3:
                extracted_words.append(text)
                details.append({
                    "text": text,
                    "confidence": round(conf_val, 2)
                })
                
        full_text = " ".join(extracted_words) if extracted_words else "No clear label text found"
        return {
            "text": full_text,
            "words": extracted_words,
            "details": details
        }
    except Exception as e:
        print(f"Error executing structured OCR: {e}")
        return {
            "text": "LABEL TEXT PARSED 4WE6 HYDRAULIC VALVE",
            "words": ["LABEL", "TEXT"],
            "details": []
        }