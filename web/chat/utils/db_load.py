from chat.models import Chat, Message

def load_chat_and_profile(chat_id):
    try:
        chat = Chat.objects.select_related("dog").get(id=chat_id)
    except Chat.DoesNotExist:
        return None, None

    dog = chat.dog
    if not dog:
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