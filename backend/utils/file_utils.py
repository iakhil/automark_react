import os
import uuid
import time
import cloudinary
from cloudinary import uploader
import fitz  # PyMuPDF
from flask import current_app, request
from werkzeug.utils import secure_filename
import io
from PyPDF2 import PdfReader
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

def ensure_cloudinary_config():
    """
    Ensure Cloudinary is properly configured with credentials from environment
    
    Returns:
        bool: True if configured successfully, False otherwise
    """
    load_dotenv()  # Load .env into os.environ
    
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
    api_key    = os.getenv('CLOUDINARY_API_KEY')
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
    
    if not (cloud_name and api_key and api_secret):
        print("Cloudinary credentials not found in environment variables")
        return False
    
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )
    
    # Verify configuration via attributes, not dict.get()
    cfg = cloudinary.config()
    if not cfg.api_key:
        print("Cloudinary configuration failed")
        return False
        
    print(f"Cloudinary configured successfully with cloud_name: {cfg.cloud_name}")
    return True

def allowed_file(filename):
    """
    Check if a file has an allowed extension
    
    Args:
        filename (str): The name of the file to check
        
    Returns:
        bool: True if the file has an allowed extension, False otherwise
    """
    if not filename:
        return False
    
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    )

def save_file(file, directory='uploads'):
    """
    Save a file either to Cloudinary (if configured) or to local storage
    
    Args:
        file: File to save
        directory: Directory to save the file in (for local storage)
        
    Returns:
        str: URL of the saved file
    """
    # Generate unique filename
    _, ext = os.path.splitext(file.filename)
    unique_filename = f"{str(uuid.uuid4())}{ext}"
    
    # Try Cloudinary first
    try:
        print(f"Uploading file: {file.filename} to Cloudinary")
        
        if not ensure_cloudinary_config():
            raise ValueError("Failed to configure Cloudinary")
        
        file.seek(0)
        # You can upload the FileStorage directly
        upload_folder = f"{directory}/{unique_filename.split('.')[0]}"
        print(f"Attempting Cloudinary upload to folder: {upload_folder}")
        
        response = uploader.upload(
            file,
            resource_type="auto",
            folder=upload_folder,
            use_filename=True,
            unique_filename=True
        )
        
        print(f"File successfully uploaded to Cloudinary: {response['secure_url']}")
        return response['secure_url']
        
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        current_app.logger.warning(f"Failed to upload to Cloudinary, falling back to local storage: {e}")
        
        # Fall back to local storage
        os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], directory), exist_ok=True)
        file.seek(0)
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], directory, unique_filename)
        file.save(file_path)
        
        base_url = request.host_url.rstrip('/')
        file_url = f"{base_url}/uploads/{directory}/{unique_filename}"
        
        print(f"File saved locally: {file_path}")
        current_app.logger.info(f"File saved locally at: {file_path}")
        return file_url

def create_session_with_retry():
    """
    Create a requests session with retry capability
    
    Returns:
        requests.Session: Session with retry capability
    """
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def convert_pdf_to_image_and_upload(pdf_file, folder):
    """
    Convert PDF to images and upload to Cloudinary
    
    Args:
        pdf_file: The PDF file object
        folder (str): Cloudinary folder to upload to
        
    Returns:
        list: List of URLs for the uploaded images
    """
    try:
        if not ensure_cloudinary_config():
            raise ValueError("Failed to configure Cloudinary")
        
        pdf_file.seek(0)
        pdf_content = pdf_file.read()
        print(f"PDF content read, size: {len(pdf_content)} bytes")
        
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        uploaded_urls = []
        print(f"PDF opened successfully, {pdf_document.page_count} pages found")

        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            
            from PIL import Image
            img_data = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            img_byte_array = io.BytesIO()
            img_data.save(img_byte_array, format='JPEG', quality=95)
            img_byte_array.seek(0)
            
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    upload_result = uploader.upload(
                        img_byte_array,
                        folder=folder,
                        quality='auto:best',
                        fetch_format='auto',
                        timeout=30,
                        public_id=f"{secure_filename(pdf_file.filename).rsplit('.', 1)[0]}_page_{page_num + 1}"
                    )
                    uploaded_urls.append(upload_result['url'])
                    break
                except Exception as upload_error:
                    if attempt == max_attempts - 1:
                        raise upload_error
                    time.sleep(2 ** attempt)
        
        pdf_document.close()
        return uploaded_urls

    except Exception as e:
        print(f"PDF processing error: {e}")
        raise Exception(f"Failed to process the PDF file: {e}")

def extract_pdf_text(pdf_file):
    """
    Extract text from a PDF file
    
    Args:
        pdf_file: The PDF file object
        
    Returns:
        str: Extracted text from the PDF
    """
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_rubric_text(pdf_url):
    """
    Extract text from a PDF file at the given URL
    
    Args:
        pdf_url (str): URL of the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    try:
        session = create_session_with_retry()
        response = session.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        pdf_content = response.content
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        
        text = ""
        for page_num in range(pdf_document.page_count):
            text += pdf_document[page_num].get_text()
        
        pdf_document.close()
        return text
        
    except Exception as e:
        print(f"Rubric extraction error: {e}")
        raise Exception(f"Failed to process rubric: {e}")
