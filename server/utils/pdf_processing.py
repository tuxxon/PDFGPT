import fitz
import logging

logger = logging.getLogger(__name__)

def pdf_to_text(path, start_page=1, end_page=None):
    logger.info(f"Converting PDF to text: {path}")
    doc = fitz.open(path)
    total_pages = doc.page_count

    if end_page is None:
        end_page = total_pages

    text_list = []

    for i in range(start_page - 1, end_page):
        text = doc.load_page(i).get_text("text")
        text_list.append(text.strip())

    doc.close()
    logger.info(f"PDF converted to text successfully. Total pages processed: {end_page - start_page + 1}")
    return text_list

def download_pdf(url, output_path):
    logger.info(f"Downloading PDF from URL: {url}")
    import urllib.request
    urllib.request.urlretrieve(url, output_path)
    logger.info(f"PDF downloaded and saved to: {output_path}")
