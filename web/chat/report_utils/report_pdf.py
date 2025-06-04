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

