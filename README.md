# Fabric Builder

## 專案資料夾結構 (Project Directory Structure)

```
.
├── network_configs/
│   ├── 1_vxlan_evpn/
│   ├── 3_node/
│   └── 5_segment/
├── scripts/
│   ├── cisco/
│   │   ├── 12.1.2e/
│   │   ├── 12.2.2/
│   │   └── 12.3/
│   ├── inventory/
│   └── logs/
├── .gitignore
├── requirements.txt
└── README.md
```

### 資料夾用途說明

* **`/scripts`**

    * 用途: 放置提供給 GitLab CI/CD 等工具執行流程的腳本 (Scripts)，以及所有 API 請求相關的邏輯與模組。
    
    * **`/scripts/cisco`**
        * 用途: 放置 Cisco 相關的 API 請求邏輯與模組，按版本分類。
        
    * **`/scripts/inventory`**
        * 用途: 透過 Nornir、NAPALM 等工具進行設備資訊的獲取與管理。

    * **`/scripts/logs`**
        * 用途: 放置 API 執行的回傳值

* **`/network_configs`**

    * 用途: 放置讓網路工程師能夠自主修改、用以簡易配置網路的 YAML 定義檔案。
    
    * **`/network_configs/1_vxlan_evpn`**
        * 用途: VXLAN EVPN 架構相關的網路配置
        
    * **`/network_configs/3_node`**
        * 用途: 單節點設備相關的配置
        
    * **`/network_configs/5_segment`**
        * 用途: 網段相關的配置

## Network Config
- 需求: 讓網路工程師可以簡單的設定
- Need to check types

## Cisco NDFC 12.2.2
- Check [README.md](scripts/cisco/12.2.2/README.md) for API interfaces and CLI tools

## Gitlab Flow
1. 網路工程師修改 Network config
2. 讀取 Network config 並透過 API / scripts 產生 `pending_config.txt`
    ```
    hostname1:
    command1
    command2
    --------
    hostname2:
    command1
    command2
    ...
    ```
3. 在 Gitlab 上產生 Network config diff 以及展示出 `pending_config.txt`
4. Reviewer check & approve
5. 透過 API / scripts deploy changes
6. 透過 API / scripts 產生報告


## Current Issue

## Future works
### 短期目標 (Short-term Goals)
- 🎯 **完整測試套件**: 建立自動化測試框架
- 🎯 **配置驗證**: 增加 YAML 配置檔案的格式驗證
- 🎯 **日誌系統**: 改善日誌記錄和監控機制
- 🎯 **錯誤恢復**: 增加失敗操作的自動恢復機制
- 🚀 **CI/CD 整合**: 完整的 GitLab CI/CD pipeline 整合

### 中長期目標 (Medium to Long-term Goals)
- 🚀 **Web UI**: 透過 Jinja2 產生網頁直接讓工程師填寫配置
- 🚀 **配置模板庫**: 建立標準化的網路配置模板
- 🚀 **多版本支援**: 支援 NDFC 12.1.2e 和 12.3 版本
- 🚀 **自動化部署**: 完全自動化的網路部署流程
- 🚀 **監控整合**: 與網路監控系統的整合


## 說明影片

**NDFC Fabric / Child Fabric / Multi-Site / Free Form**
https://youtu.be/XEMBwHlYooA

**Add Switch / Set Role / Recaculate & Deploy / Change Mode**
https://youtu.be/0ZNgtebdc3A

**VRF Create / Attach / Detach / Delete**
https://youtu.be/y8kl2KT0cNo

**Network Create / Attach / Detach / Delete**
https://youtu.be/iIEqcQEvCMU






