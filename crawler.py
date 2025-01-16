import base64
import json
import logging
import os
import re

import numpy as np

from io import BytesIO
from time import sleep

from paddleocr import PaddleOCR
from PIL import Image, ImageEnhance
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# =============== 1. Selenium & Driver 基本設定 ===============
chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
)
chrome_options.add_argument("--headless")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# =============== 2. PaddleOCR 初始化 ===============
ocr = PaddleOCR(use_angle_cls=True, lang="ch")
logger = logging.getLogger("ppocr")
logger.setLevel(logging.ERROR)

# =============== 3. 輔助函式定義 ===============
def sanitize_filename(filename: str) -> str:
    """移除檔名中無法使用的字元"""
    return re.sub(r'[\/\\:*?"<>|]', '_', filename)

INIT_DATA_TEMPLATE = {
    "title": None,
    "address_image_base64": None,
    "city": None,
    "district": None,
    "poster_identity": None,
    "poster_name": None,
    "phone_number": None,
    "area_image_base64": None,
    "floor_image_base64": None,
    "rent_image_base64": None,
    "house_type": None,
    "house_type_1": None,
    "address": None,
}
def init_data():
    """產生每個 URL 的空白字典結構"""
    return INIT_DATA_TEMPLATE.copy()

def ocr_text_from_file(file_path: str):
    """
    使用 PaddleOCR 辨識檔案路徑指定的圖片。
    回傳文字陣列，如果沒有文字或發生錯誤，回傳空陣列。
    """
    try:
        with Image.open(file_path) as img:
            img_array = np.array(img)

        # 使用 PaddleOCR 辨識文字
        result = ocr.ocr(img_array, cls=True)
        print("PaddleOCR raw result:", result)

        # 確認回傳結果結構
        if not result or len(result) == 0 or not isinstance(result, list) or len(result[0]) == 0:
            print("未檢測到任何文字")
            return []

        # 取出結果的第一層（真正的文字區塊清單）
        result_lines = result[0]

        # 提取文字內容
        text_list = [
            line[1][0]  # 取文字內容
            for line in result_lines
            if len(line) > 1 and len(line[1]) > 0  # 確保結構正確
        ]

        return text_list
    except Exception as e:
        print(f"OCR 發生錯誤: {e}")
        return []

def ocr_text(base64_str):
    """
    使用 PaddleOCR 辨識 base64 格式圖片中的文字，回傳文字陣列。
    :param base64_str: base64 格式的圖片字串，格式需以 'data:image/png;base64,' 開頭
    :return: 辨識出的文字陣列，如果沒有文字或發生錯誤，回傳空陣列
    """
    if base64_str and base64_str.startswith("data:image/png;base64,"):
        try:
            # 解碼 base64 圖片
            img_data = base64.b64decode(base64_str.replace("data:image/png;base64,", ""))
            with Image.open(BytesIO(img_data)) as img:
                img_array = np.array(img)

            # 使用 PaddleOCR 辨識文字
            result = ocr.ocr(img_array, cls=True)
            print("PaddleOCR raw result:", result)

            # 確認回傳結果結構
            if not result or len(result) == 0 or not isinstance(result, list) or len(result[0]) == 0:
                print("未檢測到任何文字")
                return []

            # 取出結果的第一層（真正的文字區塊）
            result_lines = result[0]

            # 提取文字內容
            text_list = [
                line[1][0]
                for line in result_lines
                if len(line) > 1 and len(line[1]) > 0
            ]
            return text_list

        except Exception as e:
            print(f"OCR 發生錯誤: {e}")
            return []
    else:
        print("無效的 base64 字串")
        return []

# =============== 4. 讀取 URL & 主程式邏輯 ===============
with open("url.txt", "r") as url_file:
    urls = [u.strip() for u in url_file.readlines()]

final_results = []
max_retries = 5

area_file_counter = 1
address_file_counter = 1

for url in urls:
    final_data = init_data()

    for attempt in range(max_retries):
        data = init_data()
        driver.get(url)

        # 等待關鍵元素(樓層圖片)加載，最多嘗試 retry_attempt < 5 次
        for retry_attempt in range(5):
            found_element = False
            for _ in range(10):
                try:
                    driver.find_element(
                        By.CSS_SELECTOR,
                        "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > "
                        "section.block.info-board > div.pattern > span:nth-child(5) > img",
                    )
                    print(f"成功找到所有必要爬取元素: {url}")
                    found_element = True
                    break
                except:
                    sleep(1)
            if found_element:
                break
            else:
                if retry_attempt < 4:
                    driver.get(url)
                    continue
                print(f"無法找到所有必要爬取元素，再次嘗試載入頁面: {url}")
            break

        # 標題
        try:
            title = driver.find_element(By.TAG_NAME, "title").get_attribute("innerText")
            data["title"] = title.replace(" - 591租屋網", "").strip()
        except:
            pass

        # 城市、區域
        try:
            data["city"] = driver.find_element(By.CSS_SELECTOR, 'a.t5-link[href*="region"]').text
        except:
            pass
        try:
            data["district"] = driver.find_element(By.CSS_SELECTOR, 'a.t5-link[href*="section"]').text
        except:
            pass

        # 發文者身份與名稱
        try:
            poster_identity_text = driver.find_elements(By.CSS_SELECTOR, "span.name")[3].get_attribute("innerText")
            data["poster_identity"] = poster_identity_text.split(":")[0].strip()
            if ":" in poster_identity_text:
                data["poster_name"] = poster_identity_text.split(":")[1].strip()
        except:
            pass

        # 電話
        try:
            data["phone_number"] = driver.find_element(By.CSS_SELECTOR, "section.contact-card > div > div > button > span:nth-child(2) > span").text.strip()
        except:
            pass

        # 坪數、樓層、租金圖片
        try:
            data["area_image_base64"] = driver.find_element(
                By.CSS_SELECTOR,
                "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > "
                "section.block.info-board > div.pattern > span:nth-child(3) > img",
            ).get_attribute("src")
        except:
            pass

        try:
            data["floor_image_base64"] = driver.find_element(
                By.CSS_SELECTOR,
                "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > "
                "section.block.info-board > div.pattern > span:nth-child(5) > img",
            ).get_attribute("src")
        except:
            pass

        try:
            data["rent_image_base64"] = driver.find_element(
                By.CSS_SELECTOR,
                "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > "
                "section.block.info-board > div.house-price > span > strong > img",
            ).get_attribute("src")
        except:
            pass

        try:
            data["address_image_base64"] = driver.find_element(
                By.CSS_SELECTOR,
                "#__nuxt > section:nth-child(3) > section.main-wrapper > "
                "section.main-content > section.block.surround > div.address img",
            ).get_attribute("src")
        except:
            pass

        # 房屋類型
        try:
            data["house_type"] = driver.find_element(
                By.CSS_SELECTOR,
                "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > "
                "section.block.info-board > div.pattern > span:nth-child(1)",
            ).text.strip()
        except:
            pass

        # 房屋型態
        try:
            data["house_type_1"] = driver.find_element(
                By.CSS_SELECTOR, "div.pattern span:last-child"
            ).text.strip()
        except:
            pass

        for k in final_data:
            if data[k] is not None:
                final_data[k] = data[k]

        # 如果關鍵欄位都抓到了，就不再重試
        if all(final_data[k] is not None for k in final_data if k not in ["address"]):
            break
        elif attempt == max_retries - 1:
            print("已達最大嘗試次數，部分資料仍無法取得。")
        else:
            print(f"第 {attempt+1} 次嘗試失敗，重新載入頁面...")
            continue

    # =================== 新增：建立資料夾並將 base64 轉檔存入 ===================
    os.makedirs("area_image_base64", exist_ok=True)
    os.makedirs("address_image_base64", exist_ok=True)

    # 先將標題做清理，避免特殊字元
    sanitized_title = sanitize_filename(final_data["title"] or "無法取得")

    area_file_path = None
    address_file_path = None

    # 儲存 area_image_base64
    if final_data["area_image_base64"] and final_data["area_image_base64"].startswith("data:image/png;base64,"):
        try:
            area_data = base64.b64decode(final_data["area_image_base64"].replace("data:image/png;base64,", ""))
            with Image.open(BytesIO(area_data)) as area_img:

                area_img = ImageEnhance.Contrast(area_img).enhance(2)
                area_img = ImageEnhance.Brightness(area_img).enhance(0.1)

                area_file_path = f"area_image_base64/{area_file_counter}_{sanitized_title}.png"
                area_file_counter += 1
                area_img.save(area_file_path)
        except Exception as e:
            print(f"儲存 area_image_base64 圖片失敗: {e}")
            area_file_path = None

    # 儲存 address_image_base64
    if final_data["address_image_base64"] and final_data["address_image_base64"].startswith("data:image/png;base64,"):
        try:
            address_data = base64.b64decode(final_data["address_image_base64"].replace("data:image/png;base64,", ""))
            with Image.open(BytesIO(address_data)) as address_img:

                address_img = ImageEnhance.Contrast(address_img).enhance(2)
                address_img = ImageEnhance.Brightness(address_img).enhance(0.1)

                address_file_path = f"address_image_base64/{address_file_counter}_{sanitized_title}.png"
                address_file_counter += 1
                address_img.save(address_file_path)
        except Exception as e:
            print(f"儲存 address_image_base64 圖片失敗: {e}")
            address_file_path = None

    # =================== OCR: 坪數 / 樓層 / 租金 圖片 ===================
    area_text_raw = ocr_text(final_data["area_image_base64"])
    floor_text = ocr_text(final_data["floor_image_base64"])
    rent_text_raw = ocr_text(final_data["rent_image_base64"])

    addr_text = []
    if address_file_path is not None:
        addr_text = ocr_text_from_file(address_file_path)
    else:
        addr_text = ocr_text(final_data["address_image_base64"])

    # 樓層
    floor_height, total_floors = None, None
    if floor_text:
        floor_str = "".join(floor_text).replace("l", "/").replace("|", "/")
        if "/" in floor_str:
            parts = floor_str.split("/")
            if len(parts) == 2:
                floor_height, total_floors = parts

    # 租金
    rent_text = []
    if rent_text_raw:
        rent_text = [".".join(t.replace(".", ",") for t in rent_text_raw)]

    # 坪數
    area_text = []
    if area_text_raw:
        area_text = ["址".join(t.replace("址", "坪") for t in area_text_raw)]

    # =================== 將最終結果存入 final_results ===================
    final_results.append(
        {
            "title": final_data["title"] or "無法取得",
            "address": addr_text[0] if addr_text else "無法取得",
            "city": final_data["city"] or "無法取得",
            "district": final_data["district"] or "無法取得",
            "poster_identity": final_data["poster_identity"] or "無法取得",
            "poster_name": final_data["poster_name"] or "無法取得",
            "phone_number": final_data["phone_number"] or "無法取得",
            "house_type": final_data["house_type"] or "無法取得",
            "house_type_1": final_data["house_type_1"] or "無法取得",
            "area": area_text[0] if area_text else "無法取得",
            "floor_height": floor_height or "無法取得",
            "total_floors": total_floors or "無法取得",
            "rent": rent_text[0] if rent_text else "無法取得",
        }
    )

    sleep(5)

# =============== 5. 輸出 JSON ===============
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(final_results, f, ensure_ascii=False, indent=4)

driver.quit()

if __name__ == "__main__":
    ocr = PaddleOCR(
        use_angle_cls=True,
        lang="ch",
        use_gpu=True,
        show_log=False
    )
