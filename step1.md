# 專案規格書：YouTube Shorts 每日爆款自動化監測系統

## 1. 專案概述 (Executive Summary)
本專案旨在建立一套自動化系統，利用 YouTube Data API v3，每日定時抓取並分析特定地區（如台灣 TW）的熱門 Shorts 短影音。系統需具備「低成本（節省 API 額度）」與「高精準（過濾非爆款）」之特性，以協助行銷與創作者決策。

## 2. 系統架構與成本控制 (Architecture & Cost)

### 2.1 API 使用策略
* **資料源：** Google YouTube Data API v3
* **核心方法：** 僅使用 `videos.list` (chart='mostPopular')。
* **禁止事項：** 嚴格禁止使用 `search.list` 進行關鍵字掃描，以避免消耗過多配額 (Quota)。
* **配額預算：** 每日 < 500 點 (Google 免費額度為 10,000 點/日)，系統極為輕量。

### 2.2 運行環境
* **頻率：** 每日 1 次 (建議時間：16:00 GMT+8)。
* **輸出：** CSV 報表 或 通訊軟體推播 (Line/Discord)。

## 3. 數據篩選邏輯 (Data Filtering Logic)

系統需經過四層漏斗篩選，找出真正的爆款：

1.  **第一層：獲取熱門榜 (Raw Data)**
    * 請求 `mostPopular` 榜單前 200 名影片。
    * 地區設定：`regionCode='TW'` (可參數化修改為 US/KR)。

2.  **第二層：Shorts 識別 (Format Filter)**
    * **時長限制：** 解析 ISO 8601 時間格式，僅保留 `Duration <= 60秒` 之影片。

3.  **第三層：內容過濾 (Category Filter)**
    * **排除類別：** `10` (Music)。原因：避免官方 MV Teaser 干擾原創趨勢判斷。
    * **保留類別：** `24` (Entertainment), `20` (Gaming), `23` (Comedy), `17` (Sports) 等。

4.  **第四層：爆發力分析 (Viral Velocity)**
    * **新鮮度：** 僅保留 `發布時間 < 48小時` 的影片。
    * **指標計算：** 計算 `VPH (Views Per Hour) = 總觀看數 / 發布已過小時數`。
    * **排序：** 依據 **VPH** 由高至低排序 (而非總觀看數)。

## 4. 輸出欄位定義 (Output Schema)

| 欄位 (Field) | 說明 (Description) |
| :--- | :--- |
| `Rank` | 依 VPH 排名 |
| `Title` | 影片標題 |
| `Channel` | 頻道名稱 |
| `Views` | 目前總觀看數 |
| `VPH` | **每小時平均觀看數 (核心指標)** |
| `Published_Time` | 上架時間 |
| `URL` | 影片連結 (https://www.youtube.com/shorts/VIDEO_ID) |

---