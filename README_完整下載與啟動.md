# 台灣真實地理資料版｜第一人稱航空飛行模擬器 Pro（v8 地圖＋降落強化）

## 重要說明
這是**可載入真實地理資料的整合版專案**，保留原模擬器的飛機、飛行物理、機場、天氣、儀表、自動駕駛及其他系統，新增動態地面比例尺與外部台灣地理資料載入器。

本版本已附上由使用者提供的 2026 全臺 20 公尺網格高程 GeoTIFF 轉換而成的概覽地形 `data/taiwan-map.json`，並另附近場 20m 串流圖磚。概覽網格為 640×1600（本資料範圍內約 314 m × 236 m／格）；飛機周圍會再按需載入 20m 圖磚，因此不是將整個 20m 原始資料一次轉成超大型 GPU 網格。官方索引 CSV 將該筆資源列為「不分幅_台灣20MDEM(2026)／數值高程模型資料」；雖然 CSV 檔名含 DTM 字樣，仍未能僅憑索引確認該影像是裸地 DTM 或含地表物 DSM，請勿將其宣稱為已驗證裸地模型。原始影像範圍未涵蓋澎湖馬公機場位置，澎湖與部分外海島嶼沿用專案程序化島嶼模型。

## 一、下載本專案
1. 下載 `Taiwan_FlightSim_RealMap_Package.zip`。
2. 在 Windows 對 ZIP 按右鍵 →「全部解壓縮」。
3. 解壓後確認資料夾內有 `index.html`、`data`、`tools`、`run_windows.bat`。

## 二、取得地形資料（本版本已附轉換結果）
本壓縮包已內含 `data/taiwan-map.json`，解壓後即可載入目前轉換完成的高程網格，不需要再次下載才能看到本版地形。若要重新產生或替換資料，請將確認過的 GeoTIFF 放入 `source_data/dem/`，再依下方步驟執行。原始 757 MB GeoTIFF 不重複放入本專案壓縮包，以避免檔案膨脹；請保留使用者原始高程 ZIP 作為來源備份。

1. 安裝 Python 3.10 或更新版本，並在專案根目錄開啟 PowerShell。
2. 第一次使用先建立虛擬環境並安裝套件：

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. 若要下載其他官方圖幅，可執行以下命令。下載後請逐筆核對官方圖資名稱與類型，確定是裸地 DTM 後再使用；索引中名稱含 DEM 或未明確標示 DTM 的資料不可直接宣稱為裸地地形。

```powershell
.venv\Scripts\python.exe tools\download_official_dtm_index.py --out-dir source_data\dem
```

4. 也可以先在瀏覽器查看官方資料集： https://data.gov.tw/dataset/178729
5. 此資料集免費，採政府資料開放授權條款第 1 版；各圖幅產製年份可能不同。
6. 下載完成後，工具會把 ZIP 內的 GeoTIFF 解壓到 `source_data/dem/extracted/`。若資源提供 CSV 點位資料而不是 GeoTIFF，請用 QGIS「加入分隔文字圖層」匯入東坐標、北坐標及高程欄位，再依資料座標系統匯出成 EPSG:3826 GeoTIFF。
7. 確認 `source_data/dem/` 內有 `.tif`／`.tiff` 圖幅。新版轉換工具會遞迴讀取多個圖幅，直接合併成同一張台灣地形，不必先手動鑲嵌。

官方 DTM 說明平台（20 公尺資料免申請）：https://dtm.moi.gov.tw/

若自動下載連結需要登入、回傳網頁或平台調整欄位，程式會跳過該連結；此時請從官方資料集頁面手動下載相應圖幅，不要把 HTML 網頁或 DSM 表面模型當成 DTM 裸地地形。若 CSV 內容或檔名未清楚標示 DTM／DSM，請先在官方頁面核對資料名稱再使用。2026 官方資料集頁面：https://data.gov.tw/dataset/178729；官方 2025 DTM 備援資料集：https://data.gov.tw/dataset/176927。

## 三、取得植被／土地覆蓋資料
建議使用研究團隊公開的台灣 2023 土地覆蓋資料：
https://zenodo.org/records/14033363
下載 `2023_all_grid_wgs84.zip`，解壓後先檢查資料內的分類欄位與圖例。轉成 GeoTIFF 後，請在 QGIS「重分類」為本工具使用的代碼：1 森林、2 灌叢／草地、3 農地、4 建成區、5 水體／濕地、6 裸地／岩地、0 其他／未分類，再放入 `source_data/landcover/`。**不要直接把原始分類值當成 1–6，否則植被顏色與分布會錯誤。**

也可透過國土測繪中心圖資服務雲查閱國土利用現況調查圖層（WMS／WMTS）：
https://maps.nlsc.gov.tw/S09SOA/homePage.action
國土利用現況調查向量資料部分服務需申請或申購；服務雲公開圖層可依其服務條款介接，不應大量抓取或私自快取圖磚。

## 四、取得建築物資料
可使用 Humanitarian Data Exchange 的 Taiwan building footprints（由 OpenStreetMap 建物輪廓彙整）：
https://data.humdata.org/
在網站搜尋 `Taiwan buildings`，下載 GeoJSON／GeoPackage／Shapefile 格式，放入 `source_data/buildings/`。

注意：OSM 建物資料覆蓋率依地區不同，未繪製的建物不會自動變成真實建物。若需要更完整的官方 3D 建物模型，國土測繪中心 2025 年成果目前涵蓋部分縣市，部分資料需透過國土測繪圖資 e 商城申購：
https://whgis-nlsc.moi.gov.tw/
官方公告：https://www.nlsc.gov.tw/En/NLSC_Content.aspx?n=2109&s=339862

## 五、準備資料夾
在專案根目錄建立：

```text
source_data/
  dem/        # 台灣 DTM GeoTIFF
  landcover/  # 土地覆蓋 GeoTIFF（可選）
  buildings/  # 建物 GeoJSON（可選）
data/
  taiwan-map.json  # 由工具產生
```

## 六、安裝資料處理工具（Windows）
1. 安裝 Python 3.10 或更新版本。
2. 在專案資料夾空白處按右鍵開啟 PowerShell。
3. 執行：

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 七、產生遊戲地圖資料
新版工具會自動合併 `source_data\dem` 中的所有 GeoTIFF 圖幅。先只產生地形：

```powershell
.venv\Scripts\python.exe tools\prepare_map_data.py --dem-dir source_data\dem --out data\taiwan-map.json
```

若已準備好土地覆蓋及建物資料：

```powershell
.venv\Scripts\python.exe tools\prepare_map_data.py --dem-dir source_data\dem --landcover-dir source_data\landcover --buildings-dir source_data\buildings --out data\taiwan-map.json
```

若想提高地形網格密度，可自行調整輸出網格（會增加檔案大小、顯示卡負擔及記憶體用量）：

```powershell
.venv\Scripts\python.exe tools\prepare_map_data.py --dem-dir source_data\dem --width 900 --height 2200 --out data\taiwan-map.json
```

工具會先將所有 DTM 圖幅投影至 TWD97 / TM2 zone 121（EPSG:3826），再合併並轉成模擬器本地座標（1 遊戲單位 = 10 公尺）。預設輸出 640×1600 網格，建物預設最多保留 100,000 棟，這是為了兼顧手機／內顯效能而對原始 20 公尺資料降採樣；實際輸出格距會由程式寫入 JSON metadata。若提高 width／height，地形細節會增加，但也會顯著增加瀏覽器記憶體及 GPU 負擔。機場座標會由官方資料座標重新定位，跑道高度會依當地 DTM 高程校正。

## 八、啟動遊戲
**不要直接雙擊 index.html**，因為瀏覽器可能阻擋本機 JSON 載入。

Windows（建議，不必執行批次檔）：解壓後進入專案資料夾，在資料夾空白處開啟 PowerShell，執行：

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

再開啟 `http://127.0.0.1:8000/`。若找不到 `python`，改試 `py -m http.server 8000 --bind 127.0.0.1`。停止伺服器時回到 PowerShell 按 Ctrl+C。

也可雙擊 `run_windows.bat`；新版會依序尋找 `py` 或 `python`。若 Windows 封鎖批次檔，請勿停用防毒或系統安全功能，改用上述 PowerShell 指令，並保留封鎖訊息供判斷。完整步驟見 `START_HERE.txt`。

手機使用：將整個資料夾放在可提供 HTTPS 靜態網站的空間（例如 GitHub Pages），確保 `index.html` 與 `data/taiwan-map.json` 的相對路徑不變，再用 HTTPS 網址開啟。若只在手機本機解壓，需使用支援本機 HTTP 伺服器的方式，不能用 `file://` 直接開啟。

## 九、20 公尺近場地形串流（本次加強）
- `data/taiwan-map.json` 保留原本全資料範圍的低密度概覽地形，讓遠距離地貌仍可顯示。
- 新增 `data/terrain20m/index.json` 與 `data/terrain20m/*.bin`：將使用者提供的 20m GeoTIFF 切成 256×256 高程圖磚，以 Int16 二進位格式保存，飛機附近才按需載入。
- 目前產生 1,525 個有效圖磚，二進位原始大小約 199.9 MB；桌面版載入飛機周圍最多 5×5 圖磚，低效能／手機版最多 3×3，離開範圍的圖磚會釋放 GPU 資源。
- 20m 圖磚會覆蓋概覽地形，並優先用於近場地表高度查詢；未載入的遠處仍使用概覽網格。
- 已檢查全部圖磚檔案尺寸，並隨機抽查 100 個像素與原始 GeoTIFF 比對，數值一致。
- 原始 GeoTIFF 範圍有限，20m 圖磚只在該資料涵蓋區域有效；澎湖馬公機場仍不在此影像範圍內。這不是全台每個地區都具備 20m 高程。
- 本次只加入真實高程，不代表已加入真實土地覆蓋、道路、河川或建築物；目前沒有可驗證的相應資料來源。

## 十、比例尺與資料狀態
右下角比例尺會依飛機高度與目前相機視角估算地面距離。由於透視相機與地面仰角影響，這是畫面中心附近的近似比例尺，不是整個透視畫面每個位置都相同的固定比例尺。比例尺面板下方會顯示「真實高程資料已載入」或「示意地形（尚未載入外部高程資料）」，方便確認目前是否真的使用地理資料。

本版本目前附有高程網格，尚未附土地覆蓋與建物圖資，因此不代表已完成全台植被或建築物重建。若日後加入已分類的土地覆蓋與建物資料，工具可將其轉換為遊戲座標（1 遊戲單位 = 10 公尺）。行動裝置／低功耗裝置會自動降低地形網格頂點數。


## 十一、自動降落修正（v4）
- 自動降落先飛向跑道前方 8 km 的固定初始進場定位點（IAF），進入定位點附近後才截獲最後進場。
- 最後進場使用跑道中心線偏差產生有限航向修正，不再持續追逐跑道入口後方的動態目標點；這是針對飛過入口後反向追點、繞圈的修正。
- 進場仍使用原本飛機速度、升力、俯仰與垂直速度模型；這些物理交互作用尚未完成真實瀏覽器端到端驗證。
- 新增 `tools/test_autoland_guidance_v4.py`：576 組簡化 2D 導引情境全部進入 IAF／最後進場走廊。此測試不包含真實飛行物理、下滑高度、拉平、接地或滑跑，不能視為已證明能成功降落。
- 1x／5x／10x／20x 倍速保留原設定。各機型、各機場仍需實際測試。

## 地圖真實度現況與下一階段
目前可確認的資料只有使用者提供的 20m 高程 DEM；`buildings` 為空，`landcoverTileCount=0`，所以本版本還沒有真實道路、建築物、河川向量或土地覆蓋。v6 修正的是地形配色與碰撞一致性，不應把它描述成完整真實世界地圖。
若要提高真實度，下一階段需整合有授權的道路／水系／建築向量資料，並補上實際土地覆蓋及機場跑道／滑行道資料。這些資料目前尚未打包進本版。

## 資料與精度限制
- 原始 DTM 是 20 公尺網格；模擬器預設輸出為較低密度的即時渲染網格，並非每個 20 公尺高程點都會直接成為 3D 頂點。若要保留更細節，請提高輸出網格密度並確認裝置效能足夠。
- 2026 DTM 資料集中的圖幅產製年份可能不一致。
- 植被分類的精度取決於土地覆蓋資料年份、分類方法及其空間解析度。
- OSM 建物輪廓不是完整官方建物清冊；建物高度缺失時，工具會用保守的預設高度估算。
- 官方 3D 建物成果只涵蓋公告範圍，且部分成果需申購，因此不能保證全台每棟建築都是真實 3D 模型。
- 專案不會大量下載或快取 NLSC 的受限制圖磚。

## 來源
- 內政部 2026 全台 20m DTM：https://data.gov.tw/dataset/178729
- 內政部 DTM 平台：https://dtm.moi.gov.tw/
- 國土測繪圖資服務雲：https://maps.nlsc.gov.tw/S09SOA/homePage.action
- Taiwan 2023 land-cover data：https://zenodo.org/records/14033363
- NLSC 3D Building Model 公告：https://www.nlsc.gov.tw/En/NLSC_Content.aspx?n=2109&s=339862
- HDX：https://data.humdata.org/

## 十二、v6 地面碰撞與地形顯示修正
- 若 `data/taiwan-map.json` 無法載入（例如直接以 `file://` 開啟 HTML），畫面會顯示程序化示意島嶼；舊版地面碰撞卻回傳 0 高度，可能造成飛機穿過畫面中的山地。v6 已讓示意地形的碰撞高度使用相同程序化地形公式。
- 飛出真實 DTM 範圍時，也會改用程序化地形碰撞，不再一律視為海平面。
- 機場平坦區及程序化河道已納入碰撞高度近似。
- 目前資料的 `landcoverTileCount=0`，先前佔位陣列中的 5 被錯當成水體分類，可能讓整個島看起來像水面。v6 只有在真正載入土地覆蓋資料時才使用分類色，否則改依高程著色。
- 這些修正仍需要在實際瀏覽器、不同機場與不同機型測試；尚不能宣稱已完成全機型自動降落驗證。

## 十三、繁體中文塔台語音（v5）
- 塔台無線電與自動降落階段播報已改為繁體中文（台灣），包含進場、下滑道、拉平、觸地及滑跑提示。
- 語音使用瀏覽器內建的 Speech Synthesis，優先選擇 `zh-TW`，其次為繁體中文語音，再其次才使用其他中文語音。
- 若電腦／瀏覽器沒有可用的中文語音，畫面上的塔台文字仍會顯示中文，但語音可能無法以中文朗讀。請確認 Windows 已安裝中文語音，並使用支援語音合成的瀏覽器。
- 目前修改範圍是塔台／自動降落播報；其他音效（例如引擎、環境音）不會因此變成中文。


## 十四、v7 全台官方底圖與機場正射影像
- 全台地形仍以使用者提供的 2026 版 20m DEM 圖磚及概覽網格為高程基礎。
- v7 新增內政部國土測繪中心 WMS 官方底圖（EMAP），執行時將全台底圖影像貼合在地形網格上。
- 桃園 TPE、台中 RMQ、花蓮 HUN、馬公 MZG、台東 TTT、高雄 KHH 六個機場，額外載入以機場為中心、約 12 km × 12 km 的官方通用正射影像（PHOTO2），用來顯示真實地表紋理、道路與建築群外觀。
- 圖資採執行時向 NLSC WMS 服務請求，不大量下載、快取或再散布官方圖磚。需連接網際網路；若服務或瀏覽器跨網域政策阻擋圖片載入，仍會顯示原有真實 DTM 地形與高程著色。
- 右下角標示圖資來源。官方圖資服務說明： https://maps.nlsc.gov.tw/S09SOA/pro/Wms_ajax_main.jsp 。官方服務列出 EMAP（臺灣通用電子地圖）及 PHOTO2（臺灣通用正射影像）圖層，並提供免申請 WMS 介接。
- 目前正射影像是貼圖，不是逐棟 3D 建築模型；v7 尚未加入全台完整建築高度、真實道路立體模型、土地覆蓋分類向量。
- 使用者提供的 20m GeoTIFF 不涵蓋馬公機場，因此澎湖地形仍是原專案的近似離島模型；馬公周邊可嘗試顯示官方正射影像，但不能宣稱已具備 20m 真實地形。
- 官方 2026 DTM 資料集說明其涵蓋臺灣本島及部分離島，並指出 DTM 與 DSM 的表面定義不同；本專案目前仍以提供的 GeoTIFF 來源標籤為依據，未獨立鑑定其是否為裸地 DTM。


## 十五、v8 自動降落與接地檢核加強
- 自動降落啟動時強制切回 1x，避免高倍速在進場階段造成航向、下滑道或接地判定跳過。
- IAF 除了原本的距離捕獲，也加入沿跑道方向的進場門檻判定；即使略過定位點中心，也能在合理範圍內捕獲最後進場，減少追點繞圈。
- 進場速度控制延伸到拉平階段，拉平時降低目標速度但保留有限油門，不再一律直接切斷動力。
- 自動降落新增跑道方向、橫向偏差與接地區檢核；過晚接地、偏離中心區或未對準跑道會判定不合格。手動降落仍保留原有跑道判定規則。
- 自動降落增加機型接地速度上限檢核；目前遊戲內部檢核上限為 Cessna 94 kt、Boeing 737 198 kt，這是遊戲平衡參數，不是航空器操作手冊限制。
- 修正自動降落滑跑結果可能遺失實際觸地垂直速率的問題，現在會保留真實觸地 VS 作為降落評分依據。
- 落地後仍需沿跑道減速至完全停止，才會進入旅客下機與任務完成流程。
- 新增 `tools/test_landing_v8.py`，檢查兩個跑道方向、接地區幾何、偏移／晚接地／航向錯誤與程式關鍵條件。

**測試限制：** v8 通過的是程式語法、幾何與靜態回歸測試；尚未在真實瀏覽器中完成 Cessna 172／Boeing 737 全物理飛行、各機場雙向進場、側風、拉平、接地與滑跑端到端驗證。請勿將本版視為經認證的飛行訓練或真實航空器操作系統。
