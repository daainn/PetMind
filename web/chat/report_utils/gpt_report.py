import re
from openai import OpenAI
from datetime import date, timedelta
from dotenv import load_dotenv
import os


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_prompt(dog_profile, history):
    next_date = (date.today() + timedelta(days=7)).strftime('%Y년 %m월 %d일')

    system_prompt = (
        "너는 반려견 상담 리포트를 요약해주는 요약 전문 모델이야. "
        "보호자에게 전달하는 **친절하고 정리된 요약문** 형태로 작성해줘. "
        "어렵고 전문적인 용어는 피하고 쉽게 설명해줘. "
        "아래 형식을 그대로 따르고 예시는 절대 출력하지 마. "
        "각 문단별 3~4줄 정도로 작성하고, 문단의 시작에 절대 띄어쓰기는 하지마."
    )

    oneshot_example = """
**우리 마루는요**  
마루, 5살, 푸들, 함께 산 지 3년 미만, 중성화 완료, 아파트에 살아요.
마루는 5살 푸들이며 함께한 지 3년이 채 되지 않았어요. 최근 들어 산책 중 소리에 민감한 반응을 일으키는데 특히 어린 아이들의 소리를 경계하는 것으로 보여요. 이런 변화는 휴식 부족, 스트레스의 문제일 수 있어요.

**보호자님에게 드리는 조언**  
1. 고주파 소리에 대한 민감성 완화 훈련이 필요합니다.  
2. 휴식 공간 마련을 권장합니다.  

**다음 상담 시에는**  
- 다음 상담일: 2025년 06월 06일  
- 관찰 포인트: 자극 반응 및 훈련 성공 여부를 기록해주세요.
"""

    user_content = f"""
{oneshot_example}

반려견 정보:
이름: {dog_profile['name']}
품종: {dog_profile['breed_name']}
나이: {dog_profile['age']}
성별: {dog_profile['gender']}
중성화 여부: {dog_profile['neutered']}
질병 여부: {dog_profile['disease_history']}
동거 기간: {dog_profile['living_period']}
주거형태: {dog_profile['housing_type']}

리포트 형식:
**우리 {dog_profile['name']}는요**
**보호자님에게 드리는 조언**
**다음 상담 시에는**
- 다음 상담일: {next_date}
"""
    for msg in history:
        user_content += f"{msg['role'].capitalize()}: {msg['content']}\n"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

def generate_response(messages):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=2048,
    )
    return response.choices[0].message.content.strip()

def clean_and_split(text):
    lines = text.splitlines()
    if lines and "요약리포트" in lines[0]:
        text = "\n".join(lines[1:])
    cleaned = re.sub(r"<.*?>", "", text).strip()
    intro = re.search(r"\*\*우리 .*?는요\*\*\s*(.*?)(?=\*\*보호자님에게 드리는 조언\*\*)", cleaned, re.DOTALL)
    advice = re.search(r"\*\*보호자님에게 드리는 조언\*\*\s*(.*?)(?=\*\*다음 상담 시에는\*\*)", cleaned, re.DOTALL)
    next_ = re.search(r"\*\*다음 상담 시에는\*\*\s*(.*)", cleaned, re.DOTALL)

    def strip_leading_spaces(t):
        return "\n".join([line.lstrip() for line in t.strip().splitlines()])

    intro_text = strip_leading_spaces(intro.group(1)) if intro else None
    advice_text = strip_leading_spaces(advice.group(1)) if advice else None
    next_text = strip_leading_spaces(next_.group(1)) if next_ else None

    is_split_success = bool(intro_text and advice_text and next_text)

    return intro_text, advice_text, next_text, is_split_success
