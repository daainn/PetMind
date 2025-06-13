import base64
import tempfile
import os
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
async_client = AsyncOpenAI(api_key=openai_api_key)

def format_dog_info(dog_info: dict) -> str:
    lines = []
    labels = {
        "name": "이름",
        "breed": "견종",
        "age": "나이",
        "gender": "성별",
        "neutered": "중성화 여부",
        "disease": "질병 이력",
        "disease_desc": "질병 상세",
        "period": "함께 산 기간",
        "housing": "주거 형태",
        "personality": "성격 유형"
    }

    for key, label in labels.items():
        val = dog_info.get(key)
        if val and val != "모름":
            if key == "neutered":
                val = "예" if val else "아니오"
            lines.append(f"• {label}: {val}")

    return "\n".join(lines)


async def call_gpt4o_with_images_stream(question: str, image_paths: list):
    try:
        image_messages = []
        for path in image_paths[:3]:
            with open(path, "rb") as f:
                base64_img = base64.b64encode(f.read()).decode("utf-8")
                image_messages.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_img}"
                    }
                })

        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 반려견 행동 상담 전문가입니다. "
                    "주어진 이미지와 보호자의 질문을 바탕으로 "
                    "반려견의 행동을 분석하고, 보호자가 실천 가능한 "
                    "훈육 방법과 환경 개선 조언을 함께 제시하세요. "
                    "모든 답변은 반드시 **한국어로 작성하세요.**"
                )
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": question}] + image_messages
            }
        ]

        response = await async_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1024,
            stream=True
        )

        return response

    except Exception as e:
        print("❌ GPT-4o 스트리밍 실패:", e)
        return None


def get_image_response(image_files, question="강아지가 왜 이런 행동을 하나요?", dog_info=None):
    try:
        image_paths = []

        for img in image_files[:3]:
            suffix = os.path.splitext(img.name)[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                for chunk in img.chunks():
                    tmp.write(chunk)
                image_paths.append(tmp.name)

        if dog_info:
            profile_text = format_dog_info(dog_info)
            question = f"[보호자 질문]\n{question}\n\n[반려견 프로필]\n{profile_text}"

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(call_gpt4o_with_images_stream(question, image_paths))

        final_answer = ""
        async def collect_chunks():
            nonlocal final_answer
            async for chunk in response:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    final_answer += delta.content

        loop.run_until_complete(collect_chunks())

        return final_answer.strip()

    except Exception as e:
        print("❌ 이미지 응답 실패:", e)
        return "이미지를 분석하는 중 문제가 발생했어요."
    
    finally:

        for path in image_paths:
            try:
                os.remove(path)
            except Exception:
                pass

    
async def call_gpt_stream_with_images(image_files, question="강아지가 왜 이런 행동을 하나요?"):
    image_messages = []
    temp_paths = []

    for img in image_files[:3]:
        suffix = os.path.splitext(img.name)[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in img.chunks():
                tmp.write(chunk)
            temp_paths.append(tmp.name)

    try:
        for path in temp_paths:
            with open(path, "rb") as f:
                base64_img = base64.b64encode(f.read()).decode("utf-8")
                image_messages.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_img}"
                    }
                })

        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 반려견 행동 상담 전문가입니다. "
                    "이미지와 보호자의 질문을 바탕으로 실천 가능한 훈육 조언을 제공하세요. "
                    "**한국어**로 작성해주세요."
                )
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": question}] + image_messages
            }
        ]

        stream = await async_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True,
            max_tokens=1024,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                yield delta.content

    finally:
        for path in temp_paths:
            try:
                os.remove(path)
            except Exception:
                pass