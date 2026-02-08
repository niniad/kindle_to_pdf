import shutil
import os
import time

def cleanup():
    # Directories to remove
    dirs = ["build", "dist", ".venv", "captured_images"]
    # Files to remove
    files = ["KindlePDFCapture.spec", "hello_test.py", "hello_test.spec", "run_app_standalone.bat", "run_capture_app.bat"]

    base_dir = r"c:\Users\ninni\Documents\projects\kindle_to_pdf"
    
    # 1. Remove Directories
    for d in dirs:
        path = os.path.join(base_dir, d)
        if os.path.exists(path):
            print(f"Removing directory: {d}")
            try:
                shutil.rmtree(path)
            except Exception as e:
                print(f"Failed to remove {d}: {e}")

    # 2. Remove Files
    for f in files:
        path = os.path.join(base_dir, f)
        if os.path.exists(path):
            print(f"Removing file: {f}")
            try:
                os.remove(path)
            except Exception as e:
                print(f"Failed to remove {f}: {e}")
                
    # 3. Re-create captured_images
    os.makedirs(os.path.join(base_dir, "captured_images"), exist_ok=True)
    
    print("Cleanup finished.")

if __name__ == "__main__":
    cleanup()
