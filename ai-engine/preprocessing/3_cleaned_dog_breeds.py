import pandas as pd
import re

# CSV 로드
df = pd.read_csv("3_dog_breeds.csv")

# 'category' 컬럼 제거
if 'category' in df.columns:
    df = df.drop(columns=['category'])

# 전처리 함수 정의
def clean_text(text):
    if pd.isna(text):
        return ''
    
    text = str(text).lower()

    # 불필요한 문구 제거
    text = text.replace("좋아요", "")
    text = text.replace("페이지 공유하기", "")

    # 줄바꿈 및 다중 공백 제거
    text = re.sub(r'\s+', ' ', text)

    # 특수문자 제거 (단, 마침표는 유지)
    text = re.sub(r'[^가-힣a-z0-9\s.]', '', text)

    return text.strip()

# 모든 셀에 전처리 적용
df = df.applymap(clean_text)

# ✅ CSV 저장
df.to_csv("3_cleaned_dog_breeds.csv", index=False, encoding="utf-8-sig")

# ✅ JSON 저장
df.to_json("3_cleaned_dog_breeds.json", orient="records", force_ascii=False, indent=2)

print("✅ 전처리 완료 → 3_cleaned_dog_breeds.csv / .json 저장 완료")

