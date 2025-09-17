#!/usr/bin/env python3
"""
Swedish Residence Permit OCR and Translation Script

This script extracts text from residence permit documents using Tesseract OCR
and translates Swedish text to English using the transformers library.

Requirements:
- pytesseract
- Pillow (PIL)
- transformers
- torch
- opencv-python (optional, for image preprocessing)

Installation:
pip install pytesseract Pillow transformers torch opencv-python

You also need to install Tesseract OCR:
- Ubuntu/Debian: sudo apt install tesseract-ocr tesseract-ocr-swe
- macOS: brew install tesseract tesseract-lang
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
"""

import os
import sys
import re
import tempfile
import math
from typing import Optional, Union

try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    from transformers import pipeline, MarianMTModel, MarianTokenizer
    from deskew import determine_skew
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Please install required packages:")
    print("pip install pytesseract Pillow transformers torch opencv-python")
    sys.exit(1)
    

def deskew_image(image: np.ndarray) -> np.ndarray:
    angle = determine_skew(image)
    old_width, old_height = image.shape[:2]
    angle_radian = math.radians(angle)
    width = abs(np.sin(angle_radian) * old_height) + abs(np.cos(angle_radian) * old_width)
    height = abs(np.sin(angle_radian) * old_width) + abs(np.cos(angle_radian) * old_height)

    image_center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    rot_mat[1, 2] += (width - old_width) / 2
    rot_mat[0, 2] += (height - old_height) / 2
    return cv2.warpAffine(image, rot_mat, (int(round(height)), int(round(width))), borderValue=(0, 0, 0))


class ResidencePermitProcessor:
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize the processor with optional Tesseract path.

        Args:
            tesseract_path: Path to tesseract executable (if not in PATH)
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        # Initialize translation model (Swedish to English)
        self.translator = None
        self._load_translator()

    def _load_translator(self):
        """Load the translation model."""
        try:
            print("Loading Swedish to English translation model...")
            model_name = "Helsinki-NLP/opus-mt-sv-en"
            self.translator = pipeline(
                "translation",
                model=model_name,
                tokenizer=model_name,
                device=-1  # Use CPU (-1) or 0 for GPU
            )
            print("Translation model loaded successfully!")
        except Exception as e:
            print(f"Error loading translation model: {e}")
            print("Falling back to basic word replacement...")
            self.translator = None

    def preprocess_image(self, image_path: Union[str , bytes]) -> np.ndarray:
        """
        Preprocess image to improve OCR accuracy.

        Args:
            image_path: Path to the image file

        Returns:
            Preprocessed image as numpy array
        """
        # Read image
        
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image from {image_path}")

        img_orig=np.array(img)
        img_orig=cv2.cvtColor(img_orig, cv2.COLOR_RGB2BGR)

    # normalize
        img = cv2.normalize(img_orig, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

        # Convert to grayscale

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)

        deskewd = deskew_image(denoised)

        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        heights = [cv2.boundingRect(c)[3] for c in contours if cv2.boundingRect(c)[3] > 5]

        avg_height = np.mean(heights) if heights else 0
        print(f"Average character height: {avg_height:.1f}px")

        # 5. If characters too small, upscale
        if avg_height < 20:
            scale = 2 if avg_height > 10 else 3
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            print(f"Image upscaled {scale}x")
            #show(thresh, "Upscaled & Thresholded")
        else:
        # Apply threshold to get binary image
            pass


        # Morphological operations to clean up the image
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        return cleaned

    def extract_text_from_image(self, image_path: str, preprocess: bool = True) -> str:
        """
        Extract text from image using Tesseract OCR.

        Args:
            image_path: Path to the image file
            preprocess: Whether to preprocess the image

        Returns:
            Extracted text
        """
        try:
            if preprocess:


                if isinstance(image_path, bytes):
                    # Convert bytes to a temporary file

                  with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    temp_file.write(image_path)
                    temp_file_path = temp_file.name
                    image_path = temp_file_path
                
            
            # Load image from file (more reliable than from bytes)

                # Use preprocessed image
                processed_img = self.preprocess_image(image_path)
                pil_img = Image.fromarray(processed_img)
            else:
                # Use original image
                pil_img = Image.open(image_path)

            # Configure Tesseract for Swedish and English
            custom_config = r'--oem 3 --psm 6 -l swe+eng'

            # Extract text
            text = pytesseract.image_to_string(pil_img, config=custom_config)

            try:
                os.unlink(temp_file_path)
            except:
                pass

            return text.strip()

        except Exception as e:
            print(f"Error during OCR: {e}")
            return ""

    def clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing extra whitespace and fixing common OCR errors.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', text)

        # Fix common OCR errors for Swedish characters
        replacements = {
            'â': 'å',
            'ä': 'ä',
            'ö': 'ö',
            'Â': 'Å',
            'Ä': 'Ä',
            'Ö': 'Ö'
        }

        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)

        return cleaned.strip()

    def translate_text(self, text: str) -> str:
        """
        Translate Swedish text to English.

        Args:
            text: Swedish text to translate

        Returns:
            English translation
        """
        if not text:
            return ""

        if self.translator:
            try:
                # Split text into chunks (transformers have token limits)
                max_length = 512
                chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]

                translated_chunks = []
                for chunk in chunks:
                    if chunk.strip():
                        result = self.translator(chunk, max_length=512)
                        translated_chunks.append(result[0]['translation_text'])

                return ' '.join(translated_chunks)

            except Exception as e:
                print(f"Translation error: {e}")                                 
                return self._basic_translate(text)
        else:
            return self._basic_translate(text)

    def _basic_translate(self, text: str) -> str:
        """
        Basic word-level translation for common Swedish words.
        This is a fallback when the translation model fails.
        """
        basic_translations = {
            'uppehållstillstånd': 'residence permit',
            'migrationsverket': 'Swedish Migration Agency',
            'namn': 'name',
            'personnummer': 'personal number',
            'medborgarskap': 'citizenship',
            'giltigt': 'valid',
            'till': 'until',
            'från': 'from',
            'adress': 'address',
            'telefon': 'telephone',
            'datum': 'date',
            'beslut': 'decision',
            'ansökan': 'application',
            'beviljas': 'granted',
            'tillfälligt': 'temporary',
            'permanent': 'permanent'
        }

        translated = text
        for swedish, english in basic_translations.items():
            translated = re.sub(rf'\b{swedish}\b', english, translated, flags=re.IGNORECASE)

        return translated

    def extract_key_information(self, text: str) -> dict:
        """
        Extract key information from the residence permit text.

        Args:
            text: Extracted text from the document

        Returns:
            Dictionary with extracted information
        """
        info = {}

        # Personal number pattern (Swedish personnummer)
        personnummer_pattern = r'\b\d{6}[-\s]?\d{4}\b'
        personnummer_match = re.search(personnummer_pattern, text)
        if personnummer_match:
            info['personal_number'] = personnummer_match.group()

        # Date patterns
        date_pattern = r'\b\d{4}[-/]\d{2}[-/]\d{2}\b'
        dates = re.findall(date_pattern, text)
        if dates:
            info['dates'] = dates

        # Look for validity period
        validity_pattern = r'giltigt.*?till.*?(\d{4}[-/]\d{2}[-/]\d{2})'
        validity_match = re.search(validity_pattern, text, re.IGNORECASE)
        if validity_match:
            info['valid_until'] = validity_match.group(1)

        return info

    def process_document(self, image_path: str, output_file: Optional[str] = None) -> dict:
        """
        Complete processing pipeline for a residence permit document.

        Args:
            image_path: Path to the image file
            output_file: Optional path to save results

        Returns:
            Dictionary with processing results
        """
        print(f"Processing document: {image_path}")

        # Extract text
        print("Extracting text with OCR...")
        raw_text = self.extract_text_from_image(image_path)

        print(f"Extracted text: {raw_text}")

        if not raw_text:
            return {"error": "No text extracted from image"}

        # Clean text
        cleaned_text = self.clean_text(raw_text)

        print(f"Cleaned text: {cleaned_text}")

        # Translate text
        print("Translating text...")
        translated_text = self.translate_text(cleaned_text)

        # Extract key information
        key_info = self.extract_key_information(cleaned_text)

        results = {
            "original_text": cleaned_text,
            "translated_text": translated_text,
            "key_information": key_info,
            "processing_successful": True
        }

        # Save results if output file specified
        if output_file:
            self.save_results(results, output_file)

        return results

    def save_results(self, results: dict, output_file: str):
        """Save processing results to a file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== RESIDENCE PERMIT PROCESSING RESULTS ===\n\n")
                f.write("ORIGINAL SWEDISH TEXT:\n")
                f.write("-" * 50 + "\n")
                f.write(results["original_text"])
                f.write("\n\n")

                f.write("ENGLISH TRANSLATION:\n")
                f.write("-" * 50 + "\n")
                f.write(results["translated_text"])
                f.write("\n\n")

                f.write("KEY INFORMATION EXTRACTED:\n")
                f.write("-" * 50 + "\n")
                for key, value in results["key_information"].items():
                    f.write(f"{key}: {value}\n")

            print(f"Results saved to: {output_file}")

        except Exception as e:
            print(f"Error saving results: {e}")


def main():
    """
    parser = argparse.ArgumentParser(
        description="Extract and translate text from Swedish residence permit documents"
    )
    parser.add_argument("image_path", help="Path to the residence permit image")
    parser.add_argument("-o", "--output", help="Output file for results")
    parser.add_argument("--tesseract-path", help="Path to tesseract executable")
    parser.add_argument("--no-preprocess", action="store_true",
                       help="Skip image preprocessing")

    args = parser.parse_args()

    """

    image_path = 'hemkop_picture.jpeg'

    # Check if image file exists
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found")
        sys.exit(1)

    # Initialize processor
    try:
        processor = ResidencePermitProcessor(tesseract_path=None)
    except Exception as e:
        print(f"Error initializing processor: {e}")
        sys.exit(1)

    """
    # Process document
    results = processor.process_document(image_path, "output.txt")

    if "error" in results:
        print(f"Processing failed: {results['error']}")
        sys.exit(1)

    # Display results
    print("\n" + "="*60)
    print("PROCESSING COMPLETED SUCCESSFULLY")
    print("="*60)

    print(f"\nORIGINAL SWEDISH TEXT:")
    print("-" * 40)
    print(results["original_text"][:500] + "..." if len(results["original_text"]) > 500 else results["original_text"])

    print(f"\nENGLISH TRANSLATION:")
    print("-" * 40)
    print(results["translated_text"][:500] + "..." if len(results["translated_text"]) > 500 else results["translated_text"])

    if results["key_information"]:
        print(f"\nKEY INFORMATION:")
        print("-" * 40)
        for key, value in results["key_information"].items():
            print(f"{key}: {value}")
    """

if __name__ == "__main__":
    main()