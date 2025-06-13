import os
import json
import re
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
async_client = AsyncOpenAI(api_key=openai_api_key)

# 각 test_id가 어떤 성격 축에 해당하는지 정의
DIMENSION_MAP = {
    1: "E/I", 2: "E/I", 3: "E/I",
    4: "S/N", 5: "S/N", 6: "S/N",
    7: "T/F", 8: "T/F", 9: "T/F",
    10: "J/P", 11: "J/P", 12: "J/P",
}

def extract_json(text: str) -> str:
    """GPT 응답에서 JSON 블록만 추출"""
    match = re.search(r'\[?\s*\{.*\}\s*\]?', text, re.DOTALL)
    return match.group(0) if match else "[]"

async def get_test_questions(test_id: int):
    """
    test_id에 따라 GPT에게 성격 검사 문항을 생성 요청하고,
    결과를 JSON 형태로 파싱하여 반환합니다.
    """
    dimension = DIMENSION_MAP.get(test_id, "E/I")

    prompt = f"""
당신은 반려견 성격 유형 검사를 만드는 전문가입니다.
다음 조건을 만족하는 질문 1개를 JSON 배열 형식으로 출력하세요:

조건:
1. 성격 축: {dimension} (예: E/I, S/N, T/F, J/P)
2. 질문은 반려견 보호자가 객관식으로 답할 수 있는 형태여야 합니다.
3. 각 질문은 선택지 2개로 구성되어야 하며, 성격의 양극을 나타내야 합니다.
4. 각 질문은 반려견의 행동이나 성향을 구체적으로 묻는 내용이어야 합니다.
5. 출력 형식은 반드시 아래와 같은 JSON 배열로 하세요:

[
  {{
    "question": "산책할 때 어떤가요?",
    "name": "q{test_id}_1",
    "options": [
      {{"value": "E", "text": "다른 강아지나 사람에게 먼저 다가가요"}},
      {{"value": "I", "text": "혼자 조용히 걷는 걸 선호해요"}}
    ]
  }}
]

지금은 test_id={test_id}이고, 주제 성격 축은 {dimension}입니다.
문항 1개를 위의 형식처럼 JSON 배열로 출력해주세요.
"""

    try:
        response = await async_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 반려견 성격검사 문항을 만드는 도우미입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        raw = response.choices[0].message.content.strip()
        print(f"📥 GPT 응답 (test_id={test_id}):\n{raw}\n")
        json_text = extract_json(raw)
        return json.loads(json_text)

    except Exception as e:
        print("❌ GPT API 오류:", e)
        return []
    

async def generate_character_from_type(mbti_type: str):
    prompt = f"""
당신은 반려견 성격 분석 전문가입니다. 성격 유형 {mbti_type}에 해당하는 강아지의 성격을 보호자에게 설명해주세요.

조건:
1. 설명은 반려견 입장에서 2~3문장 정도로 짧게 해주세요. (ex. "나는 낯선 사람보다 혼자 있는 걸 더 좋아해요!")
2. 너무 전문 용어 말고 따뜻하고 귀여운 말투로 작성해주세요.
3. 마지막에 보호자가 이해하기 쉬운 #해시태그 3개를 추가해주세요.

출력 형식 예시:
{{
  "type": "INFP",
  "character": "나는 낯선 환경에선 조심스럽지만, 익숙해지면 보호자에게 무한 애정을 표현해요!",
  "hashtags": ["#소심하지만사랑스러움", "#혼자놀기장인", "#마음여린강아지"]
}}
"""

    try:
        response = await async_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "반려견 성격 분석 도우미입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        raw = response.choices[0].message.content.strip()
        print(f"📥 GPT 응답 (MBTI={mbti_type}):\n{raw}\n")
        json_text = extract_json(raw)
        return json.loads(json_text)

    except Exception as e:
        print("❌ GPT 응답 오류:", e)
        return {
            "type": mbti_type,
            "character": "설명 생성 실패 😥",
            "hashtags": []
        }
