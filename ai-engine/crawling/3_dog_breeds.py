import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 셀레니움 드라이버 설정
options = webdriver.ChromeOptions()
options.add_argument("--headless") 
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

BASE_URL = "https://www.royalcanin.com/kr/dogs/breeds"
driver.get(BASE_URL)
time.sleep(3)

results = []
index = 1  # 순서 번호

# 전체 1~10페이지 순회
for page in range(1, 11):
    print(f"[+] {page}/10 페이지 견종 링크 수집 중...")
    driver.get(f"{BASE_URL}?page={page}")
    time.sleep(2)

    # 카테고리 → None 고정
    category_text = None

    breed_cards = driver.find_elements(By.CSS_SELECTOR, 'a[data-qa="breed-card-link"]')
    breed_links = [card.get_attribute("href") for card in breed_cards]

    for link in breed_links:
        driver.get(link)
        time.sleep(1)

        try:
            breed_name = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))).text.strip()

            try:
                img_tag = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa="pageheader-image"] img')))
                image_url = img_tag.get_attribute("src")
            except:
                image_url = ""

            try:
                short_p_tags = driver.find_elements(By.CSS_SELECTOR, 'div[data-qa="pageheader-paragraph"] p')
                if not short_p_tags:
                    short_description_elem = driver.find_element(By.CSS_SELECTOR, 'div[data-qa="pageheader-paragraph"]')
                    short_description = short_description_elem.text.strip()
                else:
                    short_description = "\n".join([p.text.strip() for p in short_p_tags if p.text.strip()])
            except:
                short_description = ""

            try:
                # '자세히 보기' 버튼 클릭
                try:
                    detail_btn = driver.find_element(By.XPATH, '//button[contains(text(), "자세히 보기")]')
                    driver.execute_script("arguments[0].click();", detail_btn)
                    time.sleep(1)
                except:
                    pass

                full_desc_tags = driver.find_elements(By.CSS_SELECTOR, "main p")
                full_description = "\n".join([p.text.strip() for p in full_desc_tags if p.text.strip()])
            except:
                full_description = ""

            results.append({
                "index": index,
                "category": category_text,
                "breed_name": breed_name,
                "image_url": image_url,
                "short_description": short_description,
                "full_description": full_description
            })

            print(f"   {index}. {breed_name} 수집 완료")
            index += 1

        except Exception as e:
            print(f"    오류 발생: {link} - {e}")
            continue

# CSV 저장
csv_file = "dog_breeds_3.csv"
with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "index", "category", "breed_name", "image_url", "short_description", "full_description"
    ])
    writer.writeheader()
    writer.writerows(results)

print(f"\n 최종 크롤링 완료! 총 {len(results)}개 견종 저장됨 → {csv_file}")
driver.quit()
