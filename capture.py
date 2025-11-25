import pyautogui
import time
import os

# --- 設定 ---
total_pages = 500        # 本のページ数（少し多めに設定してもOK）
save_dir = "captured_images"  # 保存フォルダ名
# -------------

# フェイルセーフ機能有効化（マウスを四隅に移動で強制終了）
pyautogui.FAILSAFE = True

# 保存用フォルダを作成
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

print("【開始】10秒以内にKindleを開いて全画面にしてください。")
print("中断したいときは、マウスを画面の四隅のどこかに素早く動かしてください（フェイルセーフ機能）。")

time.sleep(10)  # 準備時間

for i in range(1, total_pages + 1):
    # ファイル名 (page_001.png, page_002.png...)
    filename = f"{save_dir}/page_{i:03d}.png"
    
    # スクリーンショットを撮って保存
    pyautogui.screenshot(filename)
    print(f"保存完了: {filename}")
    
    # 次のページへ (左矢印キーを押す)
    pyautogui.press('left')
    
    # ページの表示待ち（PCが遅い場合はここを1.0などに増やす）
    time.sleep(0.5) 

print("【終了】すべての撮影が完了しました。")