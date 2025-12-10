# YouTube API 認證設置指南

本指南將幫助您設置 YouTube Data API v3 的 OAuth 2.0 認證，以便上傳影片。

## 步驟 1: 創建 Google Cloud 專案

前往 Google Cloud Console 創建新專案。

## 步驟 2: 啟用 YouTube Data API v3

在 API 資料庫中搜尋並啟用 YouTube Data API v3。

## 步驟 3: 創建 OAuth 2.0 憑證

1. 配置 OAuth 同意畫面
2. 創建 OAuth 2.0 客戶端 ID
3. 下載憑證 JSON 文件
4. 重命名為 `youtube_credentials.json`
5. 放入專案根目錄

## 配額說明

- 每日配額: 10,000 單位
- 影片上傳: 1,600 單位/次
- 約可上傳: 6 個影片/天

查看完整指南請參考專案文檔。
