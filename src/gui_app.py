import customtkinter as ctk
import tkinter as tk
import threading
import time
from capture_engine import CaptureEngine
from pdf_writer import PDFGenerator

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SnippingTool(tk.Toplevel):
    def __init__(self, parent, callback, aspect_ratio=None):
        super().__init__(parent)
        self.callback = callback
        self.aspect_ratio = aspect_ratio # height / width, e.g. 1.414 for A4
        self.font_main = ("Meiryo UI", 12)

        
        self.attributes('-fullscreen', True)
        self.attributes('-alpha', 0.3)
        self.attributes('-topmost', True)
        self.configure(cursor="cross")

        self.canvas = tk.Canvas(self, cursor="cross", bg="grey")
        self.canvas.pack(fill="both", expand=True)

        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Escape>", lambda e: self.destroy())

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=3)

    def on_drag(self, event):
        cur_x, cur_y = event.x, event.y
        
        if self.aspect_ratio:
            # Enforce aspect ratio
            width = cur_x - self.start_x
            height = int(abs(width) * self.aspect_ratio)
            
            # Determine direction of drag to set correct sign for height
            if cur_y < self.start_y:
                 height = -height
            
            cur_y = self.start_y + height

        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_release(self, event):
        if self.start_x is None: return
        
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        
        if self.aspect_ratio:
            # Re-calculate correct y2 based on x2 to ensure ratio captures exactly
            width = x2 - x1
            height = int(width * self.aspect_ratio)
            y2 = y1 + height

        width = x2 - x1
        height = y2 - y1

        if width < 10 or height < 10:
            self.destroy()
            return

        self.callback(x1, y1, width, height)
        self.destroy()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Kindleキャプチャ to NotebookLM")
        self.geometry("450x650")
        
        # フォント設定（日本語対応）
        self.font_title = ("Meiryo UI", 14, "bold")
        self.font_label = ("Meiryo UI", 12)
        self.font_entry = ("Meiryo UI", 12)
        self.font_button = ("Meiryo UI", 12, "bold")


        self.capture_engine = CaptureEngine()
        self.pdf_generator = PDFGenerator()
        
        self._setup_ui()
        
    def _setup_ui(self):
        # 1. Inputs
        self.frame_inputs = ctk.CTkFrame(self)
        self.frame_inputs.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(self.frame_inputs, text="本のタイトル:", font=self.font_label).pack(anchor="w", padx=5)
        self.entry_title = ctk.CTkEntry(self.frame_inputs, font=self.font_entry)
        self.entry_title.pack(fill="x", padx=5, pady=(0, 10))

        ctk.CTkLabel(self.frame_inputs, text="著者 (任意):", font=self.font_label).pack(anchor="w", padx=5)
        self.entry_author = ctk.CTkEntry(self.frame_inputs, font=self.font_entry)
        self.entry_author.pack(fill="x", padx=5, pady=(0, 10))
        
        # 2. Settings
        self.frame_settings = ctk.CTkFrame(self)
        self.frame_settings.pack(pady=5, padx=10, fill="x")

        # Direction
        # Direction
        ctk.CTkLabel(self.frame_settings, text="ページめくり方向:", font=self.font_label).pack(anchor="w", padx=5)
        self.var_direction = ctk.StringVar(value="左へ (縦書き/右綴じ)")
        self.opt_direction = ctk.CTkOptionMenu(self.frame_settings, variable=self.var_direction, 
                                               values=["左へ (縦書き/右綴じ)", "右へ (横書き/左綴じ)"],
                                               font=self.font_entry)
        self.opt_direction.pack(fill="x", padx=5, pady=(0, 10))
        
        # Aspect Ratio
        # Aspect Ratio
        ctk.CTkLabel(self.frame_settings, text="キャプチャ範囲の比率:", font=self.font_label).pack(anchor="w", padx=5)
        self.var_aspect = ctk.StringVar(value="自由選択")
        self.opt_aspect = ctk.CTkOptionMenu(self.frame_settings, variable=self.var_aspect,
                                            values=["自由選択", "A4/A5/B6 (1:1.41)", "Kindle PW (3:4)"],
                                            font=self.font_entry)
        self.opt_aspect.pack(fill="x", padx=5, pady=(0, 10))

        # Wait Time
        # Wait Time
        ctk.CTkLabel(self.frame_settings, text="待機時間 (ミリ秒):", font=self.font_label).pack(anchor="w", padx=5)
        self.entry_wait = ctk.CTkEntry(self.frame_settings, font=self.font_entry)
        self.entry_wait.insert(0, "1500")
        self.entry_wait.pack(fill="x", padx=5, pady=(0, 10))

        # 3. Actions
        self.frame_actions = ctk.CTkFrame(self)
        self.frame_actions.pack(pady=10, padx=10, fill="x")

        self.btn_region = ctk.CTkButton(self.frame_actions, text="キャプチャ範囲を選択", command=self.select_region, fg_color="#E0aaff", text_color="black", font=self.font_button)
        self.btn_region.pack(fill="x", padx=5, pady=5)
        
        self.lbl_region_status = ctk.CTkLabel(self.frame_actions, text="範囲: 未設定", text_color="gray", font=self.font_label)
        self.lbl_region_status.pack()

        self.btn_start = ctk.CTkButton(self.frame_actions, text="自動キャプチャ開始 (5秒後)", command=self.start_capture_flow, fg_color="#36D399", text_color="black", font=self.font_button)
        self.btn_start.pack(fill="x", padx=5, pady=10)

        self.btn_stop = ctk.CTkButton(self.frame_actions, text="停止", command=self.stop_capture, fg_color="#F87272", text_color="black", state="disabled", font=self.font_button)
        self.btn_stop.pack(fill="x", padx=5, pady=5)
        
        self.btn_pdf = ctk.CTkButton(self.frame_actions, text="PDF生成", command=self.generate_pdf, fg_color="#3ABFF8", text_color="black", state="disabled", font=self.font_button)
        self.btn_pdf.pack(fill="x", padx=5, pady=10)

        self.btn_clear = ctk.CTkButton(self.frame_actions, text="保存済画像全消去", command=self.clear_images, fg_color="#FB70A9", text_color="black", font=self.font_button)
        self.btn_clear.pack(fill="x", padx=5, pady=5)

        # 4. Logs
        self.lbl_status = ctk.CTkLabel(self, text="準備完了", wraplength=430, font=self.font_label)
        self.lbl_status.pack(pady=10)

    def select_region(self):
        ratio = None
        sel = self.var_aspect.get()
        if "A4" in sel: ratio = 1.414
        elif "Kindle" in sel: ratio = 4/3 # 1.333
        
        self.withdraw() # Hide main
        SnippingTool(self, self._on_region_selected, aspect_ratio=ratio)
    
    def _on_region_selected(self, x, y, w, h):
        self.deiconify() # Show main
        self.capture_engine.set_region(x, y, w, h)
        self.lbl_region_status.configure(text=f"範囲: x={x}, y={y}, {w}x{h}")

    def start_capture_flow(self):
        if not self.entry_title.get():
            self.lbl_status.configure(text="エラー: タイトルを入力してください！")
            return
        if not self.capture_engine.region:
            self.lbl_status.configure(text="エラー: 先にキャプチャ範囲を選択してください！")
            return

        self.btn_start.configure(state="disabled")
        self.btn_region.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.btn_pdf.configure(state="disabled")
        
        # Countdown thread
        threading.Thread(target=self._countdown_and_start).start()

    def _countdown_and_start(self):
        for i in range(5, 0, -1):
            self.lbl_status.configure(text=f"{i} 秒後に開始します... Kindleウィンドウをアクティブにしてください！")
            time.sleep(1)
            
        self.lbl_status.configure(text="キャプチャ中... (マウスを動かさないでください)")
        
        # Parse settings
        direction = self.var_direction.get()
        wait_ms = int(self.entry_wait.get())
        wait_sec = wait_ms / 1000.0
        
        # If Right->Left (Vertical), we press LEFT key to go to next page?
        # Standard Kindle for PC: Left Arrow goes to Next Page in Vertical mode (Right-side binding).
        # We'll pass the string to engine and let it decide or key mapping
        
        self.capture_engine.start_capture(
            direction=direction,
            wait_time=wait_sec,
            callback_status=self._update_status
        )
        
        # After loop callback
        self.after(0, self._on_capture_finished)

    def _update_status(self, msg, count):
        self.lbl_status.configure(text=f"{msg} (Total: {count})")

    def stop_capture(self):
        self.capture_engine.stop()

    def _on_capture_finished(self):
        self.btn_start.configure(state="normal")
        self.btn_region.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        
        saved = len(self.capture_engine.saved_files)
        if saved > 0:
            self.btn_pdf.configure(state="normal")
            self.lbl_status.configure(text=f"キャプチャ完了。 {saved} ページ保存されました。PDF生成可能です。")
        else:
            self.lbl_status.configure(text="キャプチャ終了。 保存されたページはありません。")

    def generate_pdf(self):
        self.lbl_status.configure(text="PDF生成中...")
        threading.Thread(target=self._generate_pdf_worker).start()

    def _generate_pdf_worker(self):
        files = self.capture_engine.saved_files
        title = self.entry_title.get()
        author = self.entry_author.get()
        
        pdfs = self.pdf_generator.generate(files, title, author)
        
        msg = f"PDF生成完了: {len(pdfs)} 件作成しました (output_pdfs/)"
        self.lbl_status.configure(text=msg)
        print(msg)

    def clear_images(self):
        # Confirm dialogue? Tkinter messagebox?
        # For simplicity, just delete and show status.
        import os
        import glob
        
        files = glob.glob(os.path.join(self.capture_engine.output_dir, "*"))
        count = 0
        for f in files:
            try:
                os.remove(f)
                count += 1
            except Exception as e:
                print(f"Error deleting {f}: {e}")
        
        self.capture_engine.saved_files = [] 
        self.lbl_status.configure(text=f"画像を削除しました ({count} ファイル)")
        self.btn_pdf.configure(state="disabled")


if __name__ == "__main__":
    app = App()
    app.mainloop()
