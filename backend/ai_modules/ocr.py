import easyocr
import numpy as np

# Load reader once (important)
reader = easyocr.Reader(['en'], gpu=False)

def extract_text_from_image(image):
    results = reader.readtext(image)

    extracted_text = []

    for (bbox, text, confidence) in results:
        if confidence > 0.5:
            extracted_text.append(text)

    return " ".join(extracted_text)