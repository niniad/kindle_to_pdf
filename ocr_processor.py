import os
import time
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

# --- 設定 ---
SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
IMAGE_DIR = 'captured_images'
OUTPUT_FILE = 'output.md'
# -------------

def get_drive_service():
    """Google Drive APIのサービスを取得する"""
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def upload_image_for_ocr(service, file_path):
    """画像をアップロードしてOCRを実行する"""
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
        print(f"アップロードエラー ({file_name}): {e}")
        return None

def get_text_from_doc(service, file_id):
    """Googleドキュメントからテキストを取得する"""
    try:
        content = service.files().export(
            fileId=file_id,
            mimeType='text/plain'
        ).execute()
        return content.decode('utf-8')
    except Exception as e:
        print(f"テキスト取得エラー (ID: {file_id}): {e}")
        return ""

def delete_file(service, file_id):
    """ファイルを削除する"""
    try:
        service.files().delete(fileId=file_id).execute()
    except Exception as e:
        print(f"削除エラー (ID: {file_id}): {e}")

def main():
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"エラー: {CREDENTIALS_FILE} が見つかりません。Google Cloud Consoleからダウンロードしてください。")
        return

    if not os.path.exists(IMAGE_DIR):
        print(f"エラー: 画像フォルダ {IMAGE_DIR} が見つかりません。capture.pyを実行してください。")
        return

    service = get_drive_service()
    
    # 画像ファイルリストを取得してソート
    images = sorted([f for f in os.listdir(IMAGE_DIR) if f.endswith('.png')])
    
    if not images:
        print("処理対象の画像がありません。")
        return

    print(f"{len(images)} 枚の画像を処理します...")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for i, image_name in enumerate(images):
            image_path = os.path.join(IMAGE_DIR, image_name)
            print(f"処理中 ({i+1}/{len(images)}): {image_name}")
            
            # 1. アップロード & OCR
            doc_id = upload_image_for_ocr(service, image_path)
            if not doc_id:
                continue
            
            # 2. テキスト抽出
            text = get_text_from_doc(service, doc_id)
            
            # 3. Markdown書き込み
            page_num = i + 1
            f.write(f"## Page {page_num}\n\n")
            f.write(f"![Page {page_num}]({IMAGE_DIR}/{image_name})\n\n")
            f.write(f"{text}\n\n")
            f.write("---\n\n")
            
            # 4. クリーンアップ
            delete_file(service, doc_id)
            
            # API制限対策のウェイト
            time.sleep(1)

    print(f"完了しました。出力先: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
