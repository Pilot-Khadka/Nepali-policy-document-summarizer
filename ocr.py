import sys
from pdf2image import convert_from_path
import pytesseract
import logging
from PIL import Image
import io
import matplotlib.pyplot as plt
import unittest


def convert_pdf_to_images(pdf_path: str):
    logging.info('Parsing document from PDF to images')
    try:
        images = convert_from_path(pdf_path)
    except Exception as exception:
        logging.error(f"Failed to convert PDF to images: {exception}")
        images = []
    return images


def display_images(images):
    for i, img in enumerate(images):
        plt.figure(figsize=(10, 10))
        plt.imshow(img)
        plt.title(f'Page {i + 1}')
        plt.axis('off')
    plt.show()



if __name__ == "__main__":
    pdf_path = 'policy_document.pdf'
    images = convert_pdf_to_images(pdf_path)

    if images:
        display_images(images)
    else:
        print("No images to display.")