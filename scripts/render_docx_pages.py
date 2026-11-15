import pypdfium2 as pdfium
import os
import glob
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

def render_pages():
    output_dir = Path("docs/images/page_screenshots")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_list = glob.glob("docs/*.pdf")
    if not pdf_list:
        print("No PDF file found in docs/")
        return
    pdf_path = pdf_list[0]
    print(f"Loading PDF from {pdf_path}...")
    pdf = pdfium.PdfDocument(pdf_path)
    print(f"Total pages: {len(pdf)}")

    for idx, page in enumerate(pdf):
        page_num = idx + 1
        bitmap = page.render(scale=2.0)
        pil_image = bitmap.to_pil()
        out_path = output_dir / f"page_{page_num:02d}.png"
        pil_image.save(str(out_path))
        print(f"Rendered Page {page_num:02d} -> {out_path}")

    # Remove extra page_22.png if total pages is 21
    extra_page = output_dir / f"page_{len(pdf)+1:02d}.png"
    if extra_page.exists():
        extra_page.unlink()
        print(f"Cleaned up stale {extra_page}")

    print(f"\n✓ Successfully rendered all {len(pdf)} pages to {output_dir}/")

if __name__ == "__main__":
    render_pages()
