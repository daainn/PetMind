import os
import tempfile
import img2pdf
import time
from django.template.loader import render_to_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from django.conf import settings


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


import os
import base64
import mimetypes
from django.conf import settings

def get_base64_image(image_path):
    """
    MEDIA_ROOT 하위의 상대 경로 image_path를 base64로 인코딩하여 반환.
    예: image_path='profile_images/1.jpeg'
    """
    full_path = os.path.join(settings.MEDIA_ROOT, image_path)

    try:
        with open(full_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode("utf-8")
            mime_type, _ = mimetypes.guess_type(full_path)
            return encoded, mime_type or "image/jpeg"
    except FileNotFoundError:
        print(f"[오류] 파일을 찾을 수 없습니다: {full_path}")
        return None, None
