# 591 租屋資訊爬蟲工具

## 📌 概述

此工具結合 Selenium 與 PaddleOCR（百度開發的文字辨識模型，對於中文字辨識準確度較高），能夠自動化爬取 `591 租屋網`的房屋資訊，包括`標題`、`地址`、`城市`、`區域`、`聯絡人身份`、`聯絡人名稱`、`電話號碼`、`房屋格局`、`房屋類型`、`坪數`、`所在樓層`、`總樓層`與`租金`等資料。

❗️注意，由於此版本對於辨識圖片中文文字的部分，依然具有一定的不精準度，因此在使用上需自行檢核結果。

<br>

## 📌 功能

- **租屋資訊爬取**：自動訪問 591 租屋網，爬取房屋資訊及圖片。
- **圖片文字辨識**：因網頁上的部分資訊（如地址、坪數、樓層、租金）是以圖片的方式保存，因此使用 PaddleOCR 對圖片中的文字進行辨識，提取關鍵數據。
- **資料存檔**：將爬取的資訊以 JSON 格式儲存。
- **圖片處理與儲存**：由於對於中文文字辨識的準確率尚待提升，因此在爬取坪數及地址圖片並進行對比度和亮度的增強處理後，保存為本機檔案，方便作為後續核對校正使用。
- **錯誤處理與重試**：因網站的反爬蟲機制，不會每次爬取資料都這麽順利，因此進行多次嘗試（最多 5 次）以提高爬取資訊的完整度。

<br>

## 📌 運作流程

1. **初始化設定**：
   - 配置 Selenium WebDriver。
   - 初始化 PaddleOCR 用於圖片文字辨識。

2. **連結讀取與處理**：
   - 從本機檔案 `url.txt` 讀取目標連結清單。

3. **爬取資料**：
   - 自動訪問每個連結，定位關鍵元素，提取文本和圖片資訊。
   - 圖片經處理後進行 OCR 辨識。

4. **圖片儲存與文字辨識**：
   - 將圖片保存至本機，並使用 PaddleOCR 提取文字內容。

5. **資料整合與輸出**：
   - 將所有爬取結果整合成結構化資料，儲存為 JSON 檔案。

<br>

## 📌 程式架構

```bash
project/
├── crawler.py                  # 主程式，包含爬蟲與文字辨識邏輯
├── url.txt                  # 存放目標連結清單
├── output.json              # 儲存最終結果的 JSON 檔案
├── area_image_base64/       # 儲存坪數圖片（程式執行後產生）
└── address_image_base64/    # 儲存地址圖片（程式執行後產生）
```

<br>

## 📌 環境設定與執行指令

### 1. 環境設定

- 確保系統安裝了以下套件：
  - Python
  - 必要套件：

```bash
pip install selenium webdriver-manager paddleocr Pillow numpy
```

- 程式會自動安裝相對應的 ChromeDriver。

<br>

### 2. 執行程式

在專案目錄下執行以下指令：

```bash
python crawler.py
```

執行後，爬取結果將儲存於 `output.json` 檔案。

<br>

## 📌 程式邏輯

### 1. 資料處理邏輯

- **元素定位與爬取**：
  - 定位目標元素並爬取資訊，包括：標題、城市、區域、發文者身份與名稱、電話號碼。
  - 爬取圖片資訊作為 Base64 字串。

- **圖片處理與文字辨識**：
  - 對圖片進行亮度與對比度增強，提升辨識效果。
  - 使用 PaddleOCR 對圖片文字進行解析，提取坪數、樓層與租金資訊。

- **錯誤處理與重試**：
  - 每個連結最多嘗試 5 次，若關鍵資訊無法取得，將記錄錯誤。

### 2. 資料輸出

- 最終結果以 JSON 格式保存，結構範例如下：

```json
[
  {
    "title": "清靜套房",
    "address": "台北市大安區復興南路",
    "city": "台北市",
    "district": "大安區",
    "poster_identity": "房東",
    "poster_name": "王先生",
    "phone_number": "0912345678",
    "house_type": "套房",
    "house_type_1": "獨立套房",
    "area": "10坪",
    "floor_height": "3F",
    "total_floors": "5F",
    "rent": "15,000"
  }
]
```

<br>

## 📌 常見問題與錯誤排除

### 1. 無法啟動 WebDriver
- 確認已安裝 Chrome 瀏覽器。
- 檢查是否已安裝 `webdriver-manager` 套件。

### 2. OCR 辨識失敗
- 確保圖片清晰度足夠，並嘗試調整亮度或對比度參數。

### 3. 程式執行過程中斷
- 檢查網頁結構是否更新（591 租屋網的反爬蟲機制似乎經常修改），必要時更新元素定位的 CSS 選擇器，如果無法排除，可以在 GitHub 上與我聯繫，我會再找時間更新程式碼。

<br>

## 📌 版本資訊

### v0.9.2
- 2025/1/16更新。
- 實現基本的租屋資訊爬取功能。
- 支援圖片處理與文字辨識。
- 輸出結構化 JSON 資料。

### 未來改進方向
- 測試其他 OCR 工具，以及影像前處理方法，提升對於中文字的辨識率。

