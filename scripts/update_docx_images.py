import zipfile
import os
import shutil
import sys
import docx

sys.stdout.reconfigure(encoding='utf-8')

DOCX_PATH = "docs/Báo cáo SOA.docx"
BACKUP_PATH = "docs/Báo cáo SOA_backup_old_images.docx"
TEMP_DOCX = "docs/Báo cáo SOA_temp.docx"

IMAGE_MAPPING = {
    "word/media/image7.png": "docs/images/hinh_5_1_login.png",
    "word/media/image8.png": "docs/images/hinh_5_2_dashboard.png",
    "word/media/image9.png": "docs/images/hinh_5_3_tuition_search.png",
    "word/media/image10.png": "docs/images/hinh_5_4_otp_verify.png",
    "word/media/image11.png": "docs/images/hinh_5_5_email_otp.png",
    "word/media/image12.png": "docs/images/hinh_5_6_receipt_history.png",
}

def update_docx():
    print(f"Creating backup of {DOCX_PATH} -> {BACKUP_PATH}...")
    shutil.copy2(DOCX_PATH, BACKUP_PATH)

    # Read all files from the original zip and replace target media
    with zipfile.ZipFile(DOCX_PATH, 'r') as zin:
        with zipfile.ZipFile(TEMP_DOCX, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename in IMAGE_MAPPING:
                    new_img_path = IMAGE_MAPPING[item.filename]
                    with open(new_img_path, 'rb') as f_img:
                        new_data = f_img.read()
                    zout.writestr(item, new_data)
                    print(f"✓ Replaced {item.filename} with {new_img_path} ({len(new_data):,} bytes)")
                else:
                    zout.writestr(item, zin.read(item.filename))

    # Overwrite original with updated temp
    shutil.move(TEMP_DOCX, DOCX_PATH)
    print(f"✓ Successfully updated all images in {DOCX_PATH}!")

    # Verify with python-docx
    doc = docx.Document(DOCX_PATH)
    print(f"Verification: Document opened successfully. Total paragraphs: {len(doc.paragraphs)}, Total inline shapes: {len(doc.inline_shapes)}")

if __name__ == "__main__":
    update_docx()
