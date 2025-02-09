import os
import json
import pickle
from datetime import datetime
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import google.generativeai as genai
from dotenv import load_dotenv
from langgraph.graph import Graph
from typing import Dict, List
import logging

# Load environment variables
load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']  # Updated scope
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def authenticate_gmail():
    creds = None
    try:
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                logger.info("Getting new credentials")
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError(
                        "credentials.json file not found. Please download it from Google Cloud Console"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES) 
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        return build('gmail', 'v1', credentials=creds)
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise

def fetch_unread_emails(service):
    results = service.users().messages().list(
        userId='me', 
        labelIds=['UNREAD'], 
        maxResults=5
    ).execute()
    
    messages = []
    if 'messages' in results:
        for message in results['messages']:
            msg = service.users().messages().get(
                userId='me', 
                id=message['id'], 
                format='full'
            ).execute()
            
            payload = msg['payload']
            headers = payload['headers']
            
            subject = next(h['value'] for h in headers if h['name'] == 'Subject')
            sender = next(h['value'] for h in headers if h['name'] == 'From')
            
            if 'parts' in payload:
                body = payload['parts'][0]['body'].get('data', '')
            else:
                body = payload['body'].get('data', '')
            
            # Clean HTML content
            if body:
                soup = BeautifulSoup(body, 'html.parser')
                clean_text = soup.get_text()
            else:
                clean_text = "No content"
                
            messages.append({
                'sender': sender,
                'subject': subject,
                'content': clean_text
            })
    
    return messages

def summarize_with_gemini(email_data: Dict) -> str:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Summarize this email in 5 sentences:
    From: {email_data['sender']}
    Subject: {email_data['subject']}
    Content: {email_data['content']}
    """
    
    for attempt in range(4):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if attempt == 3:
                return f"Failed to summarize: {str(e)}"
            continue

def save_summaries(summaries: List[Dict]):
    filename = 'email_summaries.json'
    current_data = {'summaries': []}
    
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            current_data = json.load(f)
    
    for summary in summaries:
        summary['timestamp'] = datetime.now().isoformat()
        current_data['summaries'].append(summary)
    
    with open(filename, 'w') as f:
        json.dump(current_data, f, indent=2)

def main():
    # Initialize Gmail API
    service = authenticate_gmail()
    
    # Fetch unread emails
    emails = fetch_unread_emails(service)
    
    # Process and summarize emails
    summaries = []
    for email in emails:
        summary = summarize_with_gemini(email)
        summaries.append({
            'sender': email['sender'],
            'subject': email['subject'],
            'summary': summary
        })
    
    # Save summaries
    save_summaries(summaries)
    print(f"Processed {len(summaries)} emails")

if __name__ == "__main__":
    main()
