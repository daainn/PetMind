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
        "아래 형식을 그대로 따라야 해. 어렵고 전문적인 용어는 피하고 쉽게 설명해줘."
    )

    oneshot_example = """
**우리 마루는요**  
마루는 5살 푸들로 소리에 민감한 성격입니다. 아파트에서 아이들 소리에 반응하여 자주 짖습니다.

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

상담 히스토리:
"""
    for msg in history:
        user_content += f"{msg['role'].capitalize()}: {msg['content']}\n"

    user_content += f"""
형식을 반드시 지켜주세요.
"""

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
    cleaned = re.sub(r"<.*?>", "", text).strip()
    intro = re.search(r"\*\*우리 .*?는요\*\*\s*(.*?)(?=\*\*보호자님에게 드리는 조언\*\*)", cleaned, re.DOTALL)
    advice = re.search(r"\*\*보호자님에게 드리는 조언\*\*\s*(.*?)(?=\*\*다음 상담 시에는\*\*)", cleaned, re.DOTALL)
    next_ = re.search(r"\*\*다음 상담 시에는\*\*\s*(.*)", cleaned, re.DOTALL)

    def strip_leading_spaces(t): return "\n".join([line.lstrip() for line in t.strip().splitlines()])
    return (
        strip_leading_spaces(intro.group(1)) if intro else "[추출 실패]",
        strip_leading_spaces(advice.group(1)) if advice else "[추출 실패]",
        strip_leading_spaces(next_.group(1)) if next_ else "[추출 실패]"
    )
