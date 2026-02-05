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

        self.title("Kindle Capture to NotebookLM")
        self.geometry("400x650")

        self.capture_engine = CaptureEngine()
        self.pdf_generator = PDFGenerator()
        
        self._setup_ui()
        
    def _setup_ui(self):
        # 1. Inputs
        self.frame_inputs = ctk.CTkFrame(self)
        self.frame_inputs.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(self.frame_inputs, text="Book Title:").pack(anchor="w", padx=5)
        self.entry_title = ctk.CTkEntry(self.frame_inputs)
        self.entry_title.pack(fill="x", padx=5, pady=(0, 10))

        ctk.CTkLabel(self.frame_inputs, text="Author (Optional):").pack(anchor="w", padx=5)
        self.entry_author = ctk.CTkEntry(self.frame_inputs)
        self.entry_author.pack(fill="x", padx=5, pady=(0, 10))
        
        # 2. Settings
        self.frame_settings = ctk.CTkFrame(self)
        self.frame_settings.pack(pady=5, padx=10, fill="x")

        # Direction
        ctk.CTkLabel(self.frame_settings, text="Page Direction:").pack(anchor="w", padx=5)
        self.var_direction = ctk.StringVar(value="Right -> Left (Vertical)")
        self.opt_direction = ctk.CTkOptionMenu(self.frame_settings, variable=self.var_direction, 
                                               values=["Right -> Left (Vertical)", "Left -> Right (Horizontal)"])
        self.opt_direction.pack(fill="x", padx=5, pady=(0, 10))
        
        # Aspect Ratio
        ctk.CTkLabel(self.frame_settings, text="Capture Aspect Ratio:").pack(anchor="w", padx=5)
        self.var_aspect = ctk.StringVar(value="Free Select")
        self.opt_aspect = ctk.CTkOptionMenu(self.frame_settings, variable=self.var_aspect,
                                            values=["Free Select", "A4/A5/B6 (1:1.41)", "Kindle PW (3:4)"])
        self.opt_aspect.pack(fill="x", padx=5, pady=(0, 10))

        # Wait Time
        ctk.CTkLabel(self.frame_settings, text="Wait Time (ms):").pack(anchor="w", padx=5)
        self.entry_wait = ctk.CTkEntry(self.frame_settings)
        self.entry_wait.insert(0, "1500")
        self.entry_wait.pack(fill="x", padx=5, pady=(0, 10))

        # 3. Actions
        self.frame_actions = ctk.CTkFrame(self)
        self.frame_actions.pack(pady=10, padx=10, fill="x")

        self.btn_region = ctk.CTkButton(self.frame_actions, text="Select Capture Region", command=self.select_region, fg_color="#E0aaff", text_color="black")
        self.btn_region.pack(fill="x", padx=5, pady=5)
        
        self.lbl_region_status = ctk.CTkLabel(self.frame_actions, text="Region: Not Set", text_color="gray")
        self.lbl_region_status.pack()

        self.btn_start = ctk.CTkButton(self.frame_actions, text="Start Auto Capture (5s Delay)", command=self.start_capture_flow, fg_color="#36D399", text_color="black")
        self.btn_start.pack(fill="x", padx=5, pady=10)

        self.btn_stop = ctk.CTkButton(self.frame_actions, text="Stop", command=self.stop_capture, fg_color="#F87272", text_color="black", state="disabled")
        self.btn_stop.pack(fill="x", padx=5, pady=5)
        
        self.btn_pdf = ctk.CTkButton(self.frame_actions, text="Generate PDF", command=self.generate_pdf, fg_color="#3ABFF8", text_color="black", state="disabled")
        self.btn_pdf.pack(fill="x", padx=5, pady=10)

        # 4. Logs
        self.lbl_status = ctk.CTkLabel(self, text="Ready", wraplength=380)
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
        self.lbl_region_status.configure(text=f"Region: x={x}, y={y}, {w}x{h}")

    def start_capture_flow(self):
        if not self.entry_title.get():
            self.lbl_status.configure(text="Error: Title is required!")
            return
        if not self.capture_engine.region:
            self.lbl_status.configure(text="Error: Select Region first!")
            return

        self.btn_start.configure(state="disabled")
        self.btn_region.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.btn_pdf.configure(state="disabled")
        
        # Countdown thread
        threading.Thread(target=self._countdown_and_start).start()

    def _countdown_and_start(self):
        for i in range(5, 0, -1):
            self.lbl_status.configure(text=f"Starting in {i} seconds... Focus Kindle NOW!")
            time.sleep(1)
            
        self.lbl_status.configure(text="Capturing... (Do not move mouse over region)")
        
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
            self.lbl_status.configure(text=f"Capture Finished. {saved} pages ready to PDF.")
        else:
            self.lbl_status.configure(text="Capture Finished. No pages saved.")

    def generate_pdf(self):
        self.lbl_status.configure(text="Generating PDF...")
        threading.Thread(target=self._generate_pdf_worker).start()

    def _generate_pdf_worker(self):
        files = self.capture_engine.saved_files
        title = self.entry_title.get()
        author = self.entry_author.get()
        
        pdfs = self.pdf_generator.generate(files, title, author)
        
        msg = f"Generated {len(pdfs)} PDF(s) in output_pdfs/"
        self.lbl_status.configure(text=msg)
        print(msg)

if __name__ == "__main__":
    app = App()
    app.mainloop()
