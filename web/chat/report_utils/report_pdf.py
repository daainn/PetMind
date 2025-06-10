import os
import tempfile
import img2pdf
import time
from django.template.loader import render_to_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from django.conf import settings
import base64
import mimetypes
from urllib.parse import unquote


def generate_pdf_from_context(context, pdf_filename="report.pdf"):
    html_str = render_to_string("chat/report_template.html", context)
    html_str = html_str.replace(
        "/static/css/", f"file://{os.path.join(settings.BASE_DIR, 'static/css/')}"
    )
    html_str = html_str.replace(
        "/static/images/", f"file://{os.path.join(settings.BASE_DIR, 'static/images/')}"
    )


    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as tmp_html:
        tmp_html.write(html_str)
        html_path = tmp_html.name

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_img:
        image_path = tmp_img.name

    pdf_fd, pdf_path = tempfile.mkstemp(suffix='.pdf')
    os.close(pdf_fd)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=794,1123")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("file://" + html_path)
    time.sleep(2)
    driver.save_screenshot(image_path)
    driver.quit()

    with open(pdf_path, "wb") as f:
        f.write(img2pdf.convert(image_path))

    os.remove(html_path)
    os.remove(image_path)

    return pdf_path


def get_base64_image(image_path):
    decoded_path = unquote(image_path)
    full_path = os.path.join(settings.MEDIA_ROOT, decoded_path)

    if not os.path.exists(full_path):
        print(f"❌ [오류] 파일이 존재하지 않음: {full_path}")
        return None, None

    try:
        with open(full_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode("utf-8")
            mime_type, _ = mimetypes.guess_type(full_path)
            return encoded, mime_type or "image/jpeg"

    except Exception as e:
        print(f"❌ [예외] 이미지 인코딩 실패\n에러: {e}")
        return None, None
