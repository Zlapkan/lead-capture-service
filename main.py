# main.py
import functions_framework
import os
import json
from datetime import datetime, timezone
import gspread
from google.oauth2.service_account import Credentials
import requests

# --- Configuration ---
SHEET_ID = os.environ.get('SHEET_ID')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
RESEND_SENDER_EMAIL = os.environ.get('RESEND_SENDER_EMAIL')
SERVICE_ACCOUNT_JSON = os.environ.get('SERVICE_ACCOUNT_JSON')

# --- Helper Functions ---
def get_google_sheets_client():
    """Initializes the gspread client using an alternative authentication flow."""
    if not SERVICE_ACCOUNT_JSON:
        raise ValueError("SERVICE_ACCOUNT_JSON environment variable is not set.")
    try:
        creds_json = json.loads(SERVICE_ACCOUNT_JSON)
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']
        credentials = Credentials.from_service_account_info(creds_json, scopes=scopes)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        raise ValueError(f"Failed to get Google Sheets client with alternative auth: {e}") from e

def process_quiz_answers(answers):
    """Processes quiz answers into a string."""
    if isinstance(answers, (list, dict)):
        return json.dumps(answers)
    return str(answers)

# --- Cloud Function Entry Point ---
@functions_framework.http
def process_quiz_submission(request):
    """Processes quiz submissions and handles CORS."""
    cors_headers = {'Access-Control-Allow-Origin': '*'}

    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    if request.method != 'POST':
        return ('Only POST requests are accepted', 405, cors_headers)

    try:
        data = request.get_json(silent=True)
        if not data:
            return ('Invalid request: No JSON payload received.', 400, cors_headers)
        name = data.get('name')
        email = data.get('email')
        quiz_answers = data.get('quizAnswers')
        if not all([name, email, quiz_answers is not None]):
            missing = [k for k, v in {'name': name, 'email': email, 'quizAnswers': quiz_answers}.items() if v is None]
            return (f'Missing required fields: {", ".join(missing)}.', 400, cors_headers)
    except Exception as e:
        print(f"Error parsing request JSON: {e}")
        return ('Invalid JSON format in request body.', 400, cors_headers)

    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    processed_result = process_quiz_answers(quiz_answers)

    try:
        gs_client = get_google_sheets_client()
        sheet = gs_client.open_by_id(SHEET_ID)
        worksheet = sheet.sheet1
        worksheet.append_row([timestamp, name, email, processed_result])
        print(f"Successfully appended data to Google Sheet ID: {SHEET_ID}")
    except Exception as e:
        print(f"CRITICAL ERROR during Google Sheets operation: {e}")
        return (f"An unexpected error occurred while updating the sheet: {e}", 500, cors_headers)

    try:
        if not RESEND_API_KEY:
            print("Resend API key is not configured. Skipping email.")
        else:
            payload = {
                "from": RESEND_SENDER_EMAIL,
                "to": [email],
                "subject": f"Welcome, {name}! Here are your quiz results.",
                "html": f"<p>Hi {name},</p><p>Thank you for submitting the quiz!</p><p>Your recorded answers: {processed_result}</p>"
            }
            headers = { "Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json" }
            response = requests.post("https://api.resend.com/emails", headers=headers, json=payload)
            response.raise_for_status()
            print(f"Email sent successfully to {email} via Resend.")
    except Exception as e:
        print(f"Error sending email via Resend: {e}")
        pass

    return ('Quiz submission processed successfully.', 200, cors_headers)

