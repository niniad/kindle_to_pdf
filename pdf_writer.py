import os
import img2pdf
from datetime import datetime

class PDFGenerator:
    def __init__(self, output_dir="output_pdfs"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.max_size_bytes = 190 * 1024 * 1024  # 190 MB (keeping safety margin for 200MB limit)

    def generate(self, image_paths, title, author=""):
        if not image_paths:
            print("No images to convert.")
            return []

        base_filename = f"{title}_{author}" if author else title
        # Sanitize filename
        base_filename = "".join([c for c in base_filename if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).rstrip()
        
        pdf_files = []
        current_batch = []
        current_batch_size = 0
        part_num = 1

        for img_path in image_paths:
            try:
                size = os.path.getsize(img_path)
                # If adding this image exceeds limit, write current batch first
                if current_batch and (current_batch_size + size > self.max_size_bytes):
                    self._write_pdf(current_batch, base_filename, part_num, pdf_files)
                    current_batch = []
                    current_batch_size = 0
                    part_num += 1
                
                current_batch.append(img_path)
                current_batch_size += size
            except OSError as e:
                print(f"Error accessing file {img_path}: {e}")

        # Write remaining
        if current_batch:
            self._write_pdf(current_batch, base_filename, part_num, pdf_files)

        return pdf_files

    def _write_pdf(self, images, base_name, part_num, pdf_files_list):
        output_path = os.path.join(self.output_dir, f"{base_name}_part{part_num}.pdf")
        try:
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(images))
            pdf_files_list.append(output_path)
            print(f"Created PDF: {output_path}")
        except Exception as e:
            print(f"Failed to create PDF {output_path}: {e}")
