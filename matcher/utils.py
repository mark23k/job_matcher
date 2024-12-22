import os
import logging
import openai
import pdfplumber
import docx
from django.core.mail import send_mail
from django.conf import settings

# Set up logging
logger = logging.getLogger(__name__)

# Function to handle CV content extraction for different file types
def extract_pdf_content(file_path):
    """Extract content from a PDF file."""
    try:
        with pdfplumber.open(file_path) as pdf:
            content = ''
            for page in pdf.pages:
                content += page.extract_text() or ''
        return content
    except Exception as e:
        logger.error(f"Error extracting content from PDF file '{file_path}': {e}")
        return None

def extract_docx_content(file_path):
    """Extract content from a DOCX file."""
    try:
        doc = docx.Document(file_path)
        content = ''
        for para in doc.paragraphs:
            content += para.text
        return content
    except Exception as e:
        logger.error(f"Error extracting content from DOCX file '{file_path}': {e}")
        return None

def summarize_cv(cv_file):
    file_path = cv_file.path
    content = None

    if not os.path.isfile(file_path):
        logger.error(f"CV file does not exist at {file_path}")
        return f"CV file does not exist at {file_path}"

    # Extract content based on file type (same as before)
    if file_path.endswith('.pdf'):
        content = extract_pdf_content(file_path)
    elif file_path.endswith('.docx'):
        content = extract_docx_content(file_path)
    else:
        logger.warning(f"Unsupported CV file type: {file_path}")
        return "Unsupported CV file type."

    if not content:
        logger.error(f"Unable to extract content from {file_path}")
        return "Unable to extract content from CV."

    # Summarize the content using OpenAI's GPT-3.5-turbo model
    try:
        openai.api_key = settings.OPENAI_API_KEY
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Summarize the following CV content:\n\n{content}"}
            ],
            max_tokens=200,
            temperature=0.7,
        )
        return response['choices'][0]['message']['content'].strip()
    except openai.error.OpenAIError as e:
        logger.error(f"Error summarizing CV with OpenAI: {e}")
        return f"Error summarizing CV: {e}"



# Function to send a bulk email
def send_bulk_email(summaries):
    """Send bulk email with candidate CV summaries."""
    subject = "CV Summary Mail Shot"
    message = ""

    # Prepare the email content with all summaries
    for summary in summaries:
        candidate_name = summary.get('candidate_name', 'Unknown')
        summary_text = summary.get('summary', 'No summary available')
        candidate = summary.get('candidate', None)

        # Add candidate summary to the email message
        if candidate is None:
            message += f"{candidate_name}: No candidate data available\n\n"
        else:
            message += f"{candidate_name}: {summary_text}\n\n"

    # Collect recipient emails from the summaries
    recipient_list = [summary['candidate'].email for summary in summaries if summary['candidate'].email]

    if not recipient_list:
        logger.warning("No valid email addresses found in summaries.")
        return

    # Send email to recipients
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
            html_message=message  # Send HTML content for better formatting
        )
        logger.info(f"Bulk email sent successfully to {len(recipient_list)} recipients.")
    except Exception as e:
        logger.error(f"Error sending bulk email: {e}")
