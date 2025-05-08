import requests
from io import BytesIO
from base64 import b64encode
from openai import OpenAI
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Cloudinary links for the files
question_paper_url = 'https://res.cloudinary.com/dewujwyee/image/upload/v1736466749/teachers/amswhrv3fi7btptsuoqa.pdf'
marking_scheme_url = 'https://res.cloudinary.com/dewujwyee/image/upload/v1736889748/teachers/rubrics/EnglishCore-MS_page_1.jpg'
student_response_url = 'https://res.cloudinary.com/dewujwyee/image/upload/v1736889761/teachers/answer_sheets/GARGEE_PRAKASH_ENGLISH_ANSWERSHEET_12_January_2025_page_1.jpg'

# Prompt for grading
prompt = (
    "You are a teacher grading a student's work. "
    "Here's the question paper, marking scheme, and the student's response. "
    "Evaluate the student's response based on the provided materials, assign a score for each individual question."
)

# Function to download a file
def download_file(url, filename):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to download file from {url}")
    file_bytes = BytesIO(response.content)
    file_bytes.name = filename
    return file_bytes

# Function to extract text from a PDF file
def extract_pdf_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Function to convert an image URL to a base64-encoded data URL
def convert_image_to_base64(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to download image from {url}")
    
    # Get the image MIME type from headers
    content_type = response.headers.get('Content-Type')  # e.g., 'image/jpeg'
    if not content_type or not content_type.startswith('image/'):
        raise Exception(f"Invalid image type: {content_type}")
    
    # Convert image to base64
    base64_data = b64encode(response.content).decode('utf-8')
    
    # Return the full data URL
    return f"data:{content_type};base64,{base64_data}"

# Step 1: Download and prepare files
question_paper = download_file(question_paper_url, "question_paper.pdf")
marking_scheme_base64 = convert_image_to_base64(marking_scheme_url)
student_response_base64 = convert_image_to_base64(student_response_url)

# Step 2: Extract text from the question paper PDF
question_paper_text = extract_pdf_text(question_paper)

# Step 3: Use Chat Completion API
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "text", "text": f"Question Paper:\n{question_paper_text}"},
                {"type": "image_url", "image_url": {"url": marking_scheme_base64}},
                {"type": "image_url", "image_url": {"url": student_response_base64}},
            ],
        }
    ],
    max_tokens=500,
)

# Step 4: Extract and print the response
grading_result = response.choices[0].message.content
print("Grading Results:\n", grading_result)
