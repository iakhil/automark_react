import os
import uuid
import time
import cloudinary
import cloudinary.uploader
import fitz  # PyMuPDF
from flask import current_app, request
from werkzeug.utils import secure_filename
import io
from PyPDF2 import PdfReader
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

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
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_file(file, directory='uploads'):
    """
    Save a file either to Cloudinary (if configured) or to local storage
    
    Args:
        file: File to save
        directory: Directory to save the file in (for local storage)
        
    Returns:
        str: URL of the saved file
    """
    # Load environment variables first
    load_dotenv()
    
    # Generate unique filename
    _, ext = os.path.splitext(file.filename)
    unique_filename = f"{str(uuid.uuid4())}{ext}"
    
    # Try to upload to Cloudinary first
    try:
        print(f"Uploading file: {file.filename} to Cloudinary")
        
        # Ensure Cloudinary configuration is set
        # This will explicitly set the cloudinary configuration directly in this function
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
        api_key = os.environ.get('CLOUDINARY_API_KEY')
        api_secret = os.environ.get('CLOUDINARY_API_SECRET')
        
        if not cloud_name or not api_key or not api_secret:
            print("Cloudinary credentials not found in environment variables")
            raise ValueError("Cloudinary credentials not found in environment variables")
        
        # Configure cloudinary directly
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Check if configured correctly
        if not cloudinary.config().get('api_key'):
            raise ValueError("Cloudinary API key not configured properly")
        
        # Debug the configuration being used
        print(f"Using Cloudinary configuration - cloud_name: {cloud_name}")
        
        # Reset file position to beginning to ensure we can read the entire file
        file.seek(0)
        
        # Upload to Cloudinary with folder structure
        upload_folder = f"{directory}/{unique_filename.split('.')[0]}"
        response = cloudinary.uploader.upload(
            file,
            resource_type="auto",
            folder=upload_folder,
            use_filename=True,
            unique_filename=True
        )
        
        # Return Cloudinary URL
        print(f"File successfully uploaded to Cloudinary: {response['secure_url']}")
        return response['secure_url']
        
    except Exception as e:
        # Log the error
        print(f"Cloudinary upload error: {str(e)}")
        current_app.logger.warning(f"Failed to upload to Cloudinary, falling back to local storage: {str(e)}")
        
        # Fall back to local file storage
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], directory), exist_ok=True)
            
            # Reset file position to beginning
            file.seek(0)
            
            # Save file locally
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], directory, unique_filename)
            file.save(file_path)
            
            # Generate URL for the file
            base_url = request.host_url.rstrip('/')
            file_url = f"{base_url}/uploads/{directory}/{unique_filename}"
            
            print(f"File saved locally: {file_path}")
            current_app.logger.info(f"File saved locally at: {file_path}")
            
            return file_url
            
        except Exception as local_error:
            current_app.logger.error(f"Failed to save file locally: {str(local_error)}")
            raise

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
        # Load environment variables
        load_dotenv()
        
        # Ensure Cloudinary configuration is set
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
        api_key = os.environ.get('CLOUDINARY_API_KEY')
        api_secret = os.environ.get('CLOUDINARY_API_SECRET')
        
        if not cloud_name or not api_key or not api_secret:
            print("Cloudinary credentials not found in environment variables")
            raise ValueError("Cloudinary credentials not found in environment variables")
        
        # Configure cloudinary directly
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Check if configured correctly
        if not cloudinary.config().get('api_key'):
            raise ValueError("Cloudinary API key not configured properly")
            
        # Debug the configuration being used
        print(f"Using Cloudinary configuration - cloud_name: {cloud_name}")
        
        # Read PDF content
        pdf_content = pdf_file.read()
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        uploaded_urls = []

        # Convert each page to image
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            
            # Get page as image with higher resolution
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            
            try:
                # Convert to PIL Image
                from PIL import Image
                img_data = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Save image to bytes
                img_byte_array = io.BytesIO()
                img_data.save(img_byte_array, format='JPEG', quality=95)
                img_byte_array.seek(0)
    
                # Upload to Cloudinary with retries
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        upload_result = cloudinary.uploader.upload(
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
            except ImportError:
                print("PIL/Pillow is not installed. Cannot convert PDF to images.")
                raise

        pdf_document.close()
        return uploaded_urls

    except Exception as e:
        print(f"PDF processing error: {str(e)}")
        raise Exception(f"Failed to process the PDF file: {str(e)}")

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
        text += page.extract_text()
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
        # Create session with retry mechanism
        session = create_session_with_retry()
        
        # Download PDF with retry mechanism
        response = session.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Read PDF content
        pdf_content = response.content
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        
        text = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            text += page.get_text()
        
        pdf_document.close()
        return text
        
    except Exception as e:
        print(f"Rubric extraction error: {str(e)}")
        raise Exception(f"Failed to process rubric: {str(e)}") 