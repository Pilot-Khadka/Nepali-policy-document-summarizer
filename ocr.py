import sys
from pdf2image import convert_from_path
import pytesseract
import logging
from PIL import Image
import io
import matplotlib.pyplot as plt
from docx import Document
from tqdm import tqdm
import re

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


def save_text_to_file(text, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)

def load_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return text

def read_docx(doc_path):
    document = Document(doc_path)
    pages = []
    current_page = []

    for para in document.paragraphs:
        current_page.append(para.text)
        # if 'PAGE_BREAK' in para.text:
        pages.append('\n'.join(current_page))
        current_page = []

    if current_page:
        pages.append('\n'.join(current_page))

    return pages

def levenshtein_distance(s1, s2, max_words=1000):
    s1 = s1[:max_words]
    s2 = s2[:max_words]

    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1, max_words)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, word1 in enumerate(s1):
        current_row = [i + 1]
        for j, word2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (word1 != word2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def calculate_cer_wer(ground_truth, ocr_text):
    cer = levenshtein_distance(ground_truth, ocr_text) / len(ground_truth)
    ground_truth_words = re.findall(r'\b\w+\b', ground_truth.lower())
    ocr_text_words = re.findall(r'\b\w+\b', ocr_text.lower())
    wer = levenshtein_distance(ground_truth_words, ocr_text_words) / len(ground_truth_words)
    return cer, wer


def extract_and_save_texts(pdf_path, docx_path, save_pdf_text_path, save_docx_text_path):
    ground_truth_pages = read_docx(docx_path)
    images = convert_pdf_to_images(pdf_path)

    all_initial_texts = ""
    all_ground_truth_texts = ""

    for i, img in enumerate(tqdm(images, desc="Processing Pages")):
        initial_text = pytesseract.image_to_string(img, lang='eng+nep')
        all_initial_texts += initial_text + "\n"
        if i < len(ground_truth_pages):
            all_ground_truth_texts += ground_truth_pages[i] + "\n"

    save_text_to_file(all_initial_texts, save_pdf_text_path)
    save_text_to_file(all_ground_truth_texts, save_docx_text_path)

def evaluate_text_quality(pdf_path, docx_path, save_pdf_text_path, save_docx_text_pathh):
    try:
        pdf_text = load_text_from_file(save_pdf_text_path)
        docx_text = load_text_from_file(save_docx_text_path)
    except FileNotFoundError:
        extract_and_save_texts(pdf_path, docx_path, save_pdf_text_path, save_docx_text_path)
        pdf_text = load_text_from_file(save_pdf_text_path)
        docx_text = load_text_from_file(save_docx_text_path)

    cer_total, wer_total = calculate_cer_wer(docx_text, pdf_text)
    print(f'Total CER: {cer_total}, Total WER: {wer_total}')
    return cer_total, wer_total


if __name__ == "__main__":
    pdf_path = 'converted_pdf/Unbundling-Final-English(1).pdf'
    docx_path = 'Test documents/Unbundling-Final-English(1).docx'
    save_pdf_text_path = 'extracted_texts/pdf_extracted_text.txt'
    save_docx_text_path = 'extracted_texts/docx_extracted_text.txt'

    evaluate_text_quality(pdf_path, docx_path, save_pdf_text_path, save_docx_text_path)