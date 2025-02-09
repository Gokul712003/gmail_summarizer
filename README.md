# Gmail Summarizer Setup Instructions

## Prerequisites
1. Python 3.8 or higher
2. Google Cloud Console account

## Setup Steps

1. Create a Google Cloud Project:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gmail API for your project

2. Create OAuth 2.0 Credentials:
   - In the Google Cloud Console, go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the credentials and save as `credentials.json` in the project directory

3. Set up environment variables:
   ```bash
   GOOGLE_API_KEY=your_api_key_here
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the script:
   ```bash
   python gmail_summarizer.py
   ```

The first time you run the script, it will open a browser window for OAuth authentication.
