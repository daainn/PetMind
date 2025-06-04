import os
import django
import tempfile
import img2pdf
import time
from datetime import datetime
from django.template.loader import render_to_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from chat.models import Chat, Message
from dogs.models import DogProfile
from chat.utils.gpt_report import build_prompt, generate_response, clean_and_split
from django.conf import settings

# === Django 세팅 ===
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "petmind.settings")
django.setup()

# === [1] DB에서 데이터 불러오기 ===
def load_chat_and_profile(chat_id):
    try:
        chat = Chat.objects.select_related("dog").get(id=chat_id)
    except Chat.DoesNotExist:
        print("❌ 해당 chat_id로 데이터를 찾을 수 없습니다.")
        return None, None
    except ValueError:
        print("❌ chat_id는 int 형식이어야 합니다. UUID 아님!")
        return None, None

    dog = chat.dog
    if not dog:
        print("⚠️ 연결된 dog 정보가 없습니다.")
        return None, None

    dog_dict = {
        "name": dog.name,
        "age": dog.age,
        "breed_name": dog.breed_name,
        "gender": dog.gender,
        "neutered": dog.neutered,
        "disease_history": dog.disease_history,
        "living_period": dog.living_period,
        "housing_type": dog.housing_type,
    }

    messages = Message.objects.filter(chat_id=chat_id).order_by("created_at")
    history = [
        {"role": "user" if msg.sender == "user" else "assistant", "content": msg.message}
        for msg in messages
    ]

    return dog_dict, history


# === [2] 테스트 실행 ===
if __name__ == "__main__":
    chat_id = 1  # ✅ 여기에 정수형 ID만 넣어야 합니다.

    # 미리 존재 확인
    try:
        Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        print(f"❌ chat_id={chat_id} 는 존재하지 않습니다.")
        exit()

    dog, history = load_chat_and_profile(chat_id)

    if not dog or not history:
        print("❌ chat_id에 연결된 정보가 충분하지 않습니다.")
        exit()

    messages = build_prompt(dog, history)
    raw_output = generate_response(messages)
    intro, advice, next_ = clean_and_split(raw_output)

    context = {
        "dog_name": dog["name"],
        "age": dog["age"],
        "breed_name": dog["breed_name"],
        "gender_display": dog["gender"],
        "neutered": dog["neutered"],
        "disease_history": dog["disease_history"],
        "living_period": dog["living_period"],
        "housing_type": dog["housing_type"],
        "profile_image_url": "file://" + os.path.join(settings.BASE_DIR, "static/images/sample_dog.jpg"),
        "start_date": "2025-06-01",
        "end_date": "2025-06-07",
        "intro_text": intro,
        "advice_text": advice,
        "next_text": next_,
        "llm_response_html": raw_output,
        "request": None,
    }

    # 날짜 범위 계산
    start = datetime.strptime(context["start_date"], "%Y-%m-%d")
    end = datetime.strptime(context["end_date"], "%Y-%m-%d")
    context["day_range"] = (end - start).days + 1

    html_str = render_to_string("chat/report_template.html", context)
    html_str = html_str.replace("/static/css/", f"file://{os.path.join(settings.BASE_DIR, 'static/css/')}")
    html_str = html_str.replace("/static/images/", f"file://{os.path.join(settings.BASE_DIR, 'static/images/')}")

     # [1] 임시 HTML 파일 생성 (driver가 data:text/html 바로 못 읽을 경우)
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as tmp_html:
        tmp_html.write(html_str)
        html_path = tmp_html.name

    # [2] 임시 PNG 파일 경로 (파일을 만들지만, 아래서 바로 삭제)
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_img:
        image_path = tmp_img.name

    pdf_path = os.path.join(settings.BASE_DIR, "report_test.pdf")

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

    # [3] PDF 저장
    with open(pdf_path, "wb") as f:
        f.write(img2pdf.convert(image_path))

    # [4] 임시 파일 삭제
    os.remove(html_path)
    os.remove(image_path)

    print(f"✅ PDF 생성 완료: {pdf_path}")


