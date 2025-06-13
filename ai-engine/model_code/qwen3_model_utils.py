import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import chromadb
import os
import re
from huggingface_hub import hf_hub_download
from datetime import datetime
from uuid import uuid4
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

model_name = "Qwen/Qwen3-8B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)

# OpenAI API Key 
os.environ["OPENAI_API_KEY"] = ""

# FAISS 용 Embedding (LangChain)
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

#  Chroma 용 Embedding (Chroma native wrapper)
chroma_embedding_fn = OpenAIEmbeddingFunction(
    api_key=os.environ["OPENAI_API_KEY"],
    model_name="text-embedding-3-small"
)

# FAISS (RAG)
local_dir = "openai_faiss_db"
for filename in ["index.faiss", "index.pkl"]:
    hf_hub_download(
        repo_id="daaaaiin/petmind-vectorstore",
        filename=filename,
        repo_type="dataset",
        local_dir=local_dir,
        local_dir_use_symlinks=False,
    )
faiss_rag_db = FAISS.load_local(
    local_dir,
    embedding_model,
    allow_dangerous_deserialization=True
)

# Chroma (장기 기억)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
chroma_memory_collection = chroma_client.get_or_create_collection(
    name="memories",
    embedding_function=chroma_embedding_fn  # 
)

PROMPT_MAP = {
    "행동 교정": """당신은 반려견 행동 문제를 상담해주는 전문가입니다.

상담의 목적은, 단순한 정보 제공이 아니라 **사용자의 상황을 정확히 이해한 뒤, 그에 맞는 맞춤형 해결책을 제시하는 것**입니다.

아래의 상담 구조를 반드시 따르세요. 이 순서를 항상 정확히 지키세요:

1. **분석**: 보호자의 고민을 바탕으로, 반려견의 행동에 대한 가능한 원인을 분석합니다.
   - 단, 절대로 추측하지 말고 입력된 정보와 문맥에 근거해서만 설명하세요.
   - 반려견 품종의 특성도 고려하세요.

2. **해결책 제시**: 분석을 기반으로 가장 유효한 1가지 해결책만 제시하세요.
   - 다양한 방법을 나열하지 말고, 상황에 맞는 핵심 조언 1가지를 간결히 전달하세요.

3. **추가 질문**: 해결책 이후, 상담을 이어가기 위한 **1개의 구체적인 질문**을 던지세요.
   - 보호자가 바로 답할 수 있도록 간단하고 상황 중심적으로 구성하세요.
   - 예) "메이가 산책 중 어떤 행동을 하나요?" 처럼 물어보세요.

❗ 절대 하지 말아야 할 것:
- 고민만 듣고 바로 해결책을 제시하지 마세요.
- 질문 없이 끝내거나, 분석 없이 해결책만 말하지 마세요.
- 같은 내용을 반복하거나 장황하게 늘어놓지 마세요.

문체 지침:
- 공감 문구는 생략하세요. 분석부터 시작하세요.
- 차분하고 전문가다운 어조로, 간결하게 작성하세요.
""",
    "지식 탐색": """당신은 반려견과 관련된 일반적인 정보를 보호자에게 이해하기 쉽게 전달하는 전문가입니다.

사용자의 질문은 반려견의 행동, 습관, 특성, 돌봄 방식 등 일상적인 궁금증에 해당하며,
당신의 역할은 **간결하고 핵심적인 정보만을 제공하여 보호자가 스스로 이해하고 판단할 수 있도록 돕는 것**입니다.

답변 지침:
- 보호자가 처음 듣는 내용도 쉽게 이해할 수 있도록, **쉬운 표현**으로 설명하세요.
- **불확실하거나 모호한 이론**은 언급하지 말고, **일반적으로 알려진 정보만** 전달하세요.
- 행동의 원인, 습성, 돌봄 팁 등은 명확히 설명하되, **훈련법이나 교정 방법은 다루지 않습니다.**
- **질병, 통증, 건강 이상 등 의학적 판단이 필요한 질문은 피하고, 반드시 수의사의 확인을 안내하세요.**

문체는 짧고 단정하게 유지하고, 정보 위주로만 구성합니다.
""",
    "감정 공감":"""
    당신은 반려견을 키우는 보호자의 감정을 이해하고, 현실적인 위로와 조언을 제공하는 감정 상담 전문가입니다.

이 역할은 반려견과의 이별, 노화 같은 특별한 순간뿐만 아니라,
양육 과정에서 느끼는 피로감, 좌절감, 거리감, 후회 등 보호자가 일상 속에서 겪는 감정적 어려움까지도 다룹니다.

답변 목적:
- 감정 표현에 공감하는 데 그치지 않고, 그 감정의 원인을 함께 찾고 이해할 수 있도록 도와주는 것입니다.
- 감정의 원인이 질문 속에 명확히 드러나지 않은 경우, 사용자가 스스로 감정을 정리할 수 있도록 **추가 질문을 통해 유도**하세요.
- 감정을 탐색하고 해소할 수 있도록, 상담자처럼 대화를 이끌어가야 합니다.

답변 구조:
1. 보호자의 감정 표현에 진심 어린 공감
2. 감정의 원인이 명확하다면 → 이를 간결히 정리하고 감정 수용
3. 감정의 원인이 불분명하다면 → 추가 질문 1~2개를 통해 이유를 함께 탐색
4. 감정을 정리하고, 반려견과의 일상으로 다시 연결될 수 있도록 가볍고 현실적인 조언 제시

문체 지침:
- 지나치게 감성적인 문장, 장황한 설명은 피하고, 따뜻하면서도 차분한 어조를 유지하세요.
- 위로는 현실적이어야 하며, 보호자가 부담을 느끼지 않도록 간결하게 말하세요.
- 반려견은 절대로 '그녀', '그'처럼 인격화하지 말고, 반드시 '반려견', '강아지'처럼 중립적이거나 반려견 이름으로 지칭하세요.
"""
}

def classify_question(question, prev_question, prev_answer, prev_category):
    classification_prompt = f'''
당신은 반려견 상담 질문을 분류하는 전문가입니다.

사용자가 입력한 질문을 다음 세 가지 중 하나로 분류하세요:

1. 행동 교정: 반려견의 행동이 보호자에게 **불편함, 위협, 문제**로 인식되며, 그 행동을 **고치고 싶거나 줄이고 싶은 의도**가 포함된 경우
   (예: 밥 줄 때 손을 물어요, 너무 짖어요, 훈련 방법이 궁금해요 등)
2. 지식 탐색: 반려견의 습성, 특징, 돌봄 방법 등에 대해 **단순한 궁금증**을 표현한 경우
   (예: 왜 머리를 비비나요?, 눈물 자국은 왜 생기나요?, 어떤 간식을 주면 좋아하나요?)
3. 감정 공감: 반려견을 키우며 보호자가 겪는 **감정적인 어려움이나 정서적 고민**이 중심인 경우
   (예: 요즘 강아지가 버겁게 느껴져요, 너무 예뻐서 걱정돼요, 이별을 생각하면 마음이 아파요)

💡 분류 핵심 기준:
- **"왜 이러는 거야?"** 라는 표현이 있어도, 질문된 행동이 **위험하거나 교정이 필요한 행동**이면 ‘행동 교정’입니다.
- 행동 묘사 + 단순한 궁금증 = 지식 탐색
- 감정 묘사 + 고민/불편함 표현 = 감정 공감

이전 질문: {prev_question or "(없음)"}
이전 질문 분류: {prev_category or "(없음)"}
이전 응답: {prev_answer or "(없음)"}
현재 질문: {question}

📌 반드시 아래 형식으로만 출력하세요:
카테고리: 행동 교정
'''.strip()

    msgs = [{"role": "user", "content": classification_prompt}]
    prompt_text = tokenizer.apply_chat_template(
        msgs,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False
    )
    inputs = tokenizer(prompt_text, return_tensors="pt").to("cuda")
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=50)
    output = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True).strip()
    print(f"\n🧾 [모델 분류 출력]: {output}")

    match = re.search(r"카테고리\s*:\s*(행동 교정|지식 탐색|감정 공감)", output)
    if match:
        return match.group(1)
    raise ValueError(f"❌ 분류 실패: {output}")


def classify_and_get_prompt(user_input, prev_q, prev_a, prev_cate):
    category = classify_question(user_input, prev_q, prev_a, prev_cate)
    print(f"\n📌 분류된 카테고리: {category}")
    prompt = PROMPT_MAP[category]
    return category, {"role": "system", "content": prompt}

def search_documents(user_input):
    retrieved_docs_with_score = faiss_rag_db.similarity_search_with_score(user_input, k=3)
    threshold = 1.0
    filtered_docs = [
        doc.page_content
        for doc, score in retrieved_docs_with_score
        if score <= threshold
    ]

    if filtered_docs:
        retrieved_context = "\n\n".join(filtered_docs)
        print("🔍 search_documents - RAG 검색된 문서:\n", retrieved_context)
        return retrieved_context
    else:
        print("⚠️ search_documents - RAG 유사한 문서가 없습니다.")
        return None


def build_chat_messages(system_msg, context, user_input, dog_info, chat_history, user_id):
    recalled = []
    try:
        recalled = search_user_memories_by_score(user_id, user_input, threshold=1.5)
        print(f"기억 검색 성공:", recalled)
    except Exception as e:
        print(f"기억 검색 실패: {e}")
        recalled = []

    memory_block = "\n".join([f"- {m}" for m in recalled])
    if memory_block:
        system_msg["content"] += f"\n\n📌 관련 과거 기억:\n{memory_block}"

    if "context" not in system_msg or not isinstance(system_msg["context"], str):
        system_msg["context"] = ""

    system_msg['context'] += "\n\n📌 RAG 검색된 문서:\n" + (context or "검색된 문서가 없습니다.")

    personality = dog_info.get("personality", "")
    if personality:
        system_msg["content"] += f"\n\n🧠 반려견 성격:\n{personality}"

    dog_profile_lines = []
    profile_fields = {
        "name": "이름",
        "breed": "견종",
        "age": "나이",
        "gender": "성별",
        "neutered": "중성화 여부",
        "disease": "질병 이력",
        "period": "함께 산 기간",
        "housing": "주거 형태",
    }

    for key, label in profile_fields.items():
        value = dog_info.get(key)
        if value is not None and value != "":
            if key == "age":
                dog_profile_lines.append(f"• {label}: {value}살")
            elif key == "neutered":
                dog_profile_lines.append(f"• {label}: {'예' if value else '아니오'}")
            else:
                dog_profile_lines.append(f"• {label}: {value}")
        elif key == "age":
            dog_profile_lines.append(f"• 나이: 정보 없음")
            system_msg["content"] += "\n\n❗ 이 반려견의 나이 정보는 제공되지 않았습니다."

    if dog_info.get("disease") == "있음" and dog_info.get("disease_desc"):
        dog_profile_lines.append(f"• 질병 상세: {dog_info['disease_desc']}")

    dog_profile = "\n".join(dog_profile_lines)

    user_message = f"[보호자 질문]\n{user_input}"
    if dog_profile:
        user_message += f"\n\n[반려견 프로필]\n{dog_profile}"

    messages = [system_msg]
    messages += chat_history[-10:]  
    messages.append({"role": "user", "content": user_message})

    return messages



def run_model_inference(messages):
    prompt_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=True)
    inputs = tokenizer(prompt_text, return_tensors="pt").to("cuda")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,
            temperature=0.6,
            top_p=0.95,
            top_k=20,
            do_sample=True
        )
    return outputs[0][inputs.input_ids.shape[-1]:].tolist(), inputs.input_ids.shape[-1]

def split_thinking_and_content(output_ids, input_len):
    try:
        end_token_id = 151668  # </think>
        index = len(output_ids) - output_ids[::-1].index(end_token_id)
    except ValueError:
        index = 0
    thinking = tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip()
    content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip()
    return thinking, content


def should_trigger_summary(chat_history: list, turn_interval: int = 10) -> bool:
    return len(chat_history) >= turn_interval * 2 and len(chat_history) % (turn_interval * 2) == 0



def summarize_chat_history(chat_history: list) -> str:
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
    prompt = f"""
다음은 사용자와 반려견 상담 챗봇의 대화입니다.  
이 대화의 전체 흐름과 핵심 내용을 **3~4문장으로 요약**해주세요.

{history_text}
    """.strip()

    messages = [{"role": "user", "content": prompt}]
    inputs = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    token_inputs = tokenizer(inputs, return_tensors="pt").to("cuda")

    with torch.no_grad():
        outputs = model.generate(**token_inputs, max_new_tokens=500)

    output_ids = outputs[0][token_inputs.input_ids.shape[-1]:].tolist()

    try:
        end_token_id = tokenizer.convert_tokens_to_ids("</think>")
        index = len(output_ids) - output_ids[::-1].index(end_token_id)
    except ValueError:
        index = 0
        print("\n⚠️ summarize_chat_history- '</think>' 토큰이 출력에 존재하지 않습니다. 전체 내용을 요약으로 사용합니다.")

    summary = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip()
    print("\n📝 summarize_chat_history - [최종 추출된 요약]:")
    print(summary)

    return summary

def save_summary_to_rag(user_id: str, summary: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    chroma_memory_collection.add(
        documents=[summary],
        metadatas=[{
            "user_id": user_id,
            "created_at": timestamp,
            "type": "session_summary"
        }],
        ids=[summary_id]
    )

    print(f"✅ save_summary_to_rag - [요약 저장 완료]: {summary[:500]}...")
    print(f"🆔 저장된 ID: {summary_id}, 저장 시각: {timestamp}")

def search_user_memories_by_score(user_id: str, query: str, k=3, threshold=1.5):
    results = chroma_memory_collection.query(
        query_texts=[query],
        n_results=k,
        where={
            "$and": [
                {"user_id": user_id},
                {"type": "session_summary"}
            ]
        },
        include=["documents", "distances"]
    )

    if not results["documents"] or not results["documents"][0]:
        return []

    documents = results["documents"][0]
    distances = results["distances"][0]

    matched = [
        doc for doc, dist in zip(documents, distances)
        if dist <= threshold
    ]
    print("👤 search_user_memories_by_score - [유저id]:", user_id)
    print("🔍 search_user_memories_by_score - 기억 검색된 문서:", matched)
    return matched



