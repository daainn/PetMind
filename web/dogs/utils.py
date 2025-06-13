import os
import json
import re
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
async_client = AsyncOpenAI(api_key=openai_api_key)

DIMENSION_MAP = {
    1: "E/I", 2: "E/I", 3: "E/I",
    4: "S/N", 5: "S/N", 6: "S/N",
    7: "T/F", 8: "T/F", 9: "T/F",
    10: "J/P", 11: "J/P", 12: "J/P",
}

SCENE_HINT = {
    1: "산책 중 다른 강아지를 만났을 때",
    2: "집에 손님이 찾아왔을 때",
    3: "반려견이 혼자 남겨졌을 때",
    4: "처음 가보는 장소에 도착했을 때",
    5: "새로운 장난감을 받았을 때",
    6: "집 밖에서 새로운 냄새를 맡았을 때",
    7: "다른 강아지들과 놀 때",
    8: "보호자가 외출 준비를 할 때",
    9: "새로운 명령어를 배울 때",
    10: "놀이 시간을 준비할 때",
    11: "집 안을 정리할 때",
    12: "하루 일과가 갑자기 바뀌었을 때",
}

def extract_json(text: str) -> str:
    match = re.search(r"```json\s*(\{.*?\}|\[\s*\{.*?\}\s*\])\s*```", text, re.DOTALL)
    if match:
        return match.group(1)

    fallback = re.search(r"(\{.*?\}|\[\s*\{.*?\}\s*\])", text, re.DOTALL)
    if fallback:
        return fallback.group(1)

    return "[]"

async def get_test_questions(test_id: int):
    dimension = DIMENSION_MAP.get(test_id, "E/I")
    scene = SCENE_HINT.get(test_id, "일상적인 상황에서")

    prompt = f"""
당신은 반려견 성격 유형 검사를 만드는 전문가입니다.
다음 조건을 만족하는 객관식 질문 1개를 JSON 배열 형식으로 출력하세요:

조건:
1. 성격 축: {dimension} (예: E/I, S/N, T/F, J/P)
2. 질문은 반려견 보호자가 객관식으로 답할 수 있는 형태여야 합니다.
3. 각 질문은 선택지 2개로 구성되어야 하며, 성격의 양극을 반영해야 합니다.
4. 질문은 "{scene}" 상황을 기준으로 반려견의 행동을 구체적으로 묻는 내용이어야 합니다.
5. 질문 표현은 이전과 겹치지 않도록 다양한 어휘와 문장 구조를 사용해주세요.
6. 행동이나 감정 표현을 다채롭고 생동감 있게 묘사해주세요.

반드시 출력은 아래처럼 ```json 코드블록 형식으로 출력하세요:

```json
[
  {{
    "question": "문항 내용",
    "name": "q{test_id}_1",
    "options": [
      {{"value": "{dimension[0]}", "text": "선택지 1"}},
      {{"value": "{dimension[-1]}", "text": "선택지 2"}}
    ]
  }}
]
"""

    try:
        response = await async_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 반려견 성격검사 문항을 만드는 도우미입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
        )

        raw = response.choices[0].message.content.strip()
        print(f"📥 GPT 응답 (test_id={test_id}):\n{raw}\n")
        json_text = extract_json(raw)
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 파싱 오류 (test_id={test_id}):", e)
            return []

    except Exception as e:
        print("❌ GPT API 오류:", e)
        return []

async def generate_character_from_type(mbti_type: str):
    prompt = f"""
당신은 반려견 성격 분석 전문가입니다. 성격 유형 {mbti_type}에 해당하는 강아지의 성격을 보호자에게 설명해주세요.

조건:
1. 설명은 반려견 입장에서 2~3문장 정도로 짧게 해주세요. (예: "나는 낯선 사람보다 혼자 있는 걸 더 좋아해요!")
2. 따뜻하고 귀여운 말투로 작성해주세요. 전문용어는 피해주세요.
3. 마지막에 보호자가 쉽게 이해할 수 있도록 #해시태그 3개를 추가해주세요.

출력 형식은 반드시 아래처럼 ```json 코드 블록 안에 작성하세요:

```json
{{
  "type": "{mbti_type}",
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

        try:
            parsed = json.loads(json_text)

            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed[0]
            elif isinstance(parsed, dict):
                return parsed
            else:
                raise ValueError("응답이 유효한 JSON 형식이 아닙니다.")

        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ JSON 파싱 오류 (MBTI={mbti_type}):", e)
            return {
                "type": mbti_type,
                "character": "설명 생성 실패 😥",
                "hashtags": []
            }

    except Exception as e:
        print("❌ GPT 응답 오류:", e)
        return {
            "type": mbti_type,
            "character": "설명 생성 실패 😥",
            "hashtags": []
        }