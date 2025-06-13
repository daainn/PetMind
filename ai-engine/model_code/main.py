from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Union

from qwen3_model_utils import (
    classify_and_get_prompt, search_documents, build_chat_messages,
    run_model_inference, split_thinking_and_content,
    should_trigger_summary, summarize_chat_history, save_summary_to_rag
)

app = FastAPI()

class MessageItem(BaseModel):
    role: str
    content: str

class DogInfo(BaseModel):
    name: str
    breed: str
    age: Union[int, str] = "모름"
    gender: Optional[str] = "모름"
    neutered: Optional[str] = "모름"
    disease: Optional[str] = "모름"
    disease_desc: Optional[str] = ""
    period: Optional[str] = "모름"
    housing: Optional[str] = "모름"
    personality: Optional[str] = "모름"
    chat_history: List[MessageItem]
    prev_q: Optional[str]
    prev_a: Optional[str]
    prev_cate: Optional[str]
    is_first_question: bool
    user_id: str    

class InferenceRequest(BaseModel):
    message: str
    dog_info: DogInfo

class InferenceResponse(BaseModel):
    response: str

@app.post("/chat", response_model=InferenceResponse)
def generate_response(request: InferenceRequest):
    question = request.message
    profile = request.dog_info.model_dump()  
    user_id = profile.get("user_id")

    category, system_msg = classify_and_get_prompt(
        question,
        profile.get("prev_q"),
        profile.get("prev_a"),
        profile.get("prev_cate")
    )

    context = search_documents(question)

    messages = build_chat_messages(
        system_msg=system_msg,
        user_input=question,
        context = context,
        dog_info=profile,
        chat_history=profile["chat_history"],
        user_id=user_id
    )

    output_ids, input_len = run_model_inference(messages)
    thinking, answer = split_thinking_and_content(output_ids, input_len)

    profile["chat_history"].append({"role": "user", "content": question})
    profile["chat_history"].append({"role": "assistant", "content": answer})

    if should_trigger_summary(profile["chat_history"]):
        summary = summarize_chat_history(profile["chat_history"])
        save_summary_to_rag(user_id, summary)

    return {"response": answer}
