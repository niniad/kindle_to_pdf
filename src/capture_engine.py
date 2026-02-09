import time
import os
import mss
import mss.tools
import cv2
import numpy as np
import pyautogui
import threading
from datetime import datetime

class CaptureEngine:
    def __init__(self, output_dir="captured_images"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.region = None # {'top': y, 'left': x, 'width': w, 'height': h}
        self.stop_event = threading.Event()
        self.saved_files = []
        self.last_image_data = None
    
    def set_region(self, x, y, width, height):
        # mss requires integers
        self.region = {
            'top': int(y), 
            'left': int(x), 
            'width': int(width), 
            'height': int(height)
        }
        print(f"Region set to: {self.region}")

    def start_capture(self, direction='right', wait_time=1.5, callback_status=None):
        """
        Runs the capture loop.
        direction: 'left' or 'right'
        wait_time: seconds to wait after page turn
        callback_status: function(msg, count) to update UI
        """
        self.stop_event.clear()
        self.saved_files = []
        self.last_image_data = None
        consecutive_duplicates = 0
        duplicate_limit = 3  # Stop after 3 times no change
        
        # Mapping UI direction to key
        # "右→左 (縦書き)" means we want to go PREVIOUS page? No,
        # Kindle app:
        #  Next page in vertical writing (Right to Left flow) is usually LEFT ARROW?
        #  Next page in horizontal writing (Left to Right flow) is RIGHT ARROW.
        # Let's trust user input or standard:
        #  Usually "Next Page" is what we want.
        #  If Vertical (Right to Left binding), Next Page is Left Arrow.
        #  If Horizontal (Left to Right binding), Next Page is Right Arrow.
        
        
        # Determine key to press based on direction selection
        key_to_press = 'left'
        
        if "右" in direction:
             key_to_press = 'right'
        elif "PageDown" in direction:
             key_to_press = 'pagedown'
        
        # Safety click to ensure focus on the application
        if self.region:
             center_x = self.region['left'] + self.region['width'] // 2
             center_y = self.region['top'] + self.region['height'] // 2
             
             # Safety click to ensure focus on the application
             # Click the center of the region once at the start to focus window
             print(f"Clicking at {center_x}, {center_y} to focus window...")
             pyautogui.click(center_x, center_y)
             time.sleep(0.5)

        print(f"Starting capture loop. Key: {key_to_press}, Region: {self.region}")

        with mss.mss() as sct:
            page_count = 1
            while not self.stop_event.is_set():
                if not self.region:
                    if callback_status: callback_status("エラー: 範囲が設定されていません", 0)
                    break

                # 1. Capture
                try:
                    sct_img = sct.grab(self.region)
                    # Convert to numpy array for OpenCV
                    img_np = np.array(sct_img)
                    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
                except Exception as e:
                    print(f"Capture failed: {e}")
                    break

                # 2. Compare with previous
                is_duplicate = False
                if self.last_image_data is not None:
                    diff = cv2.absdiff(self.last_image_data, img_bgr)
                    non_zero_count = np.count_nonzero(diff)
                    total_pixels = img_bgr.size
                    similarity = 1 - (non_zero_count / total_pixels)
                    
                    if similarity > 0.99: # 99% similar
                        is_duplicate = True
                        consecutive_duplicates += 1
                        print(f"Duplicate detected ({consecutive_duplicates}/{duplicate_limit})")
                    else:
                        consecutive_duplicates = 0

                # 3. Save or Stop
                if consecutive_duplicates >= duplicate_limit:
                    if callback_status: callback_status("完了 (最終ページ到達)", len(self.saved_files))
                    break
                
                if not is_duplicate:
                    # Retry checking duplicate to avoid fast loading spinners? No, simple logic for now.
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    filename = os.path.join(self.output_dir, f"page_{page_count:04d}_{timestamp}.png")
                    mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)
                    self.saved_files.append(filename)
                    self.last_image_data = img_bgr
                    if callback_status: callback_status(f"キャプチャ済み: {page_count} ページ", len(self.saved_files))
                    page_count += 1
                
                # 4. Turn Page (More robust key press)
                # Ensure focus? Maybe not every time.
                print(f"Pressing {key_to_press}...")
                pyautogui.keyDown(key_to_press)
                time.sleep(0.1) # Hold key for 100ms
                pyautogui.keyUp(key_to_press)
                
                # 5. Wait
                time.sleep(float(wait_time))
            
            # End of loop
            print("Capture stopped.")

    def stop(self):
        self.stop_event.set()
