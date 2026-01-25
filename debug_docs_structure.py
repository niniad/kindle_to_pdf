import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

# --- Config ---
SCOPES = ['https://www.googleapis.com/auth/drive'] # Drive scope covers Docs API if we have full access
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
IMAGE_DIR = 'captured_images'

def get_services():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    import urllib3
    import requests
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing credentials...")
            session = requests.Session()
            session.verify = False
            creds.refresh(Request(session=session))
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            # SSL fix for flow
            flow.oauth2session.verify = False
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    drive_service = build('drive', 'v3', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)
    return drive_service, docs_service

def upload_image_for_ocr(service, file_path):
    file_name = os.path.basename(file_path)
    file_metadata = {
        'name': file_name,
        'mimeType': 'application/vnd.google-apps.document'
    }
    media = MediaFileUpload(file_path, mimetype='image/png', resumable=True)
    
    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        return file.get('id')
    except Exception as e:
        print(f"Upload error: {e}")
        return None

def inspect_doc_structure(service, document_id):
    try:
        doc = service.documents().get(documentId=document_id).execute()
        content = doc.get('body').get('content')
        
        print(f"--- Document Structure for {document_id} ---")
        for element in content:
            if 'paragraph' in element:
                style = element['paragraph']['paragraphStyle'].get('namedStyleType')
                text_elements = element['paragraph']['elements']
                text = ""
                for te in text_elements:
                    if 'textRun' in te:
                        text += te['textRun']['content']
                
                text = text.strip()
                if text:
                    print(f"Style: {style} | Text: {text[:50]}...")
    except Exception as e:
        print(f"Docs API Error: {e}")

def delete_file(service, file_id):
    try:
        service.files().delete(fileId=file_id).execute()
    except Exception as e:
        print(f"Delete error: {e}")

def main():
    print("Starting main...")
    if not os.path.exists(IMAGE_DIR):
        print("Image dir not found")
        return

    images = sorted([f for f in os.listdir(IMAGE_DIR) if f.endswith('.png')])
    if not images:
        print("No images found")
        return

    # Test with the first image
    image_path = os.path.join(IMAGE_DIR, images[0])
    print(f"Testing with {image_path}")

    try:
        print("Getting services...")
        drive_service, docs_service = get_services()
        print("Services obtained.")
        
        print("Uploading image...")
        doc_id = upload_image_for_ocr(drive_service, image_path)
        if doc_id:
            print(f"Uploaded. Doc ID: {doc_id}")
            inspect_doc_structure(docs_service, doc_id)
            print("Deleting file...")
            delete_file(drive_service, doc_id)
            print("Done.")
        else:
            print("Upload failed.")
    except Exception as e:
        print(f"An error occurred in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
