# Fabric Builder

## 專案資料夾結構 (Project Directory Structure)

```
.
├── scripts/
│   ├── cisco/
│   │   ├── 12.1.2e/
│   │   ├── 12.2.2/
│   │   │   ├── api/
│   │   │   ├── resources/
│   │   │   └── build_fabric.py
│   │   └── 12.3/
│   ├── inventory/
│   └── logs/
├── network_configs/
│   ├── 1_vxlan_evpn/
│   ├── 2_bgp_fabric/
│   ├── 3_node/
│   └── 5_segment/
├── .gitignore
├── requirements.txt
└── spec.md
```

### 資料夾用途說明

* 📂 **`/scripts`**

    * 用途: 放置提供給 GitLab CI/CD 等工具執行流程的腳本 (Scripts)，以及所有 API 請求相關的邏輯與模組。
    
    * 📂 **`/scripts/cisco`**
        * 用途: 放置 Cisco 相關的 API 請求邏輯與模組，按版本分類。
        
        * 📂 **`/scripts/cisco/12.2.2/api`**
            * 用途: Cisco NDFC 12.2.2 版本的 API 操作模組。
            
        * 📂 **`/scripts/cisco/12.2.2/resources`**
            * 用途: 配置檔案、模板、欄位映射等資源檔案。
            
        * 📂 **`/scripts/cisco/12.2.2/build_fabric.py`**
            * 用途: 自動化 Fabric 建置工具。
        
    * 📂 **`/scripts/inventory`**
        * 用途: 透過 Nornir、NAPALM 等工具進行設備資訊的獲取與管理。

    * 📂 **`/scripts/logs`**
        * 用途: 放置 API 執行的回傳值

* 📂 **`/network_configs`**

    * 用途: 放置讓網路工程師能夠自主修改、用以簡易配置網路的 YAML 定義檔案。
    
    * 📂 **`/network_configs/1_vxlan_evpn`**
        * 用途: VXLAN EVPN 架構相關的網路配置
        
    * 📂 **`/network_configs/2_bgp_fabric`**
        * 用途: BGP Fabric 架構相關的網路配置
        
    * 📂 **`/network_configs/3_node`**
        * 用途: 單節點設備相關的配置
        
    * 📂 **`/network_configs/5_segment`**
        * 用途: 網段相關的配置

## Network Config
- 需求: 讓網路工程師可以簡單的設定
- Need to check types
## API Interfaces
### Cisco NDFC 12.2.2

#### [Fabric](scripts/cisco/12.2.2/api/fabric.py)
**純 API 介面 (Pure API Interface)**
- `create_fabric(fabric_name, template_name, payload_data)` - 使用直接傳遞的 payload 資料創建 fabric
- `update_fabric(fabric_name, template_name, payload_data)` - 使用直接傳遞的 payload 資料更新 fabric
- `get_fabric(fabric_name, fabric_dir)` - 讀取 fabric 配置
- `delete_fabric(fabric_name)` - 刪除 fabric
- `recalculate_config(fabric_name)` - 重新計算 fabric 配置
- `deploy_fabric_config(fabric_name)` - 部署 fabric 配置
- `add_MSD(parent_fabric_name, child_fabric_name)` - 將子 fabric 添加到 Multi-Site Domain
- `remove_MSD(parent_fabric_name, child_fabric_name)` - 從 Multi-Site Domain 移除子 fabric

#### [Fabric Builder](scripts/cisco/12.2.2/build_fabric.py)
**自動化網路 Fabric 配置工具 (Automated Network Fabric Configuration Tool)**

**核心功能 (Core Functions):**

##### 1. VXLAN EVPN Fabric 建置
- `build_vxlan_evpn_fabric(fabric_site_name)` - 建立資料中心 VXLAN EVPN Fabric
  - 自動解析 YAML 配置檔案
  - 處理 freeform 配置 (AAA, Leaf, Spine, Banner)
  - 支援 Easy_Fabric 模板
  - 配置合併與欄位映射

##### 2. Multi-Site Domain (MSD) 建置
- `build_multi_site_domain(msd_name)` - 建立多站點網域
  - 支援 MSD_Fabric 模板
  - 自動設定 FABRIC_TYPE="MFD" 和 FF="MSD"
  - 與子 fabric 管理分離

##### 3. Inter-Site Network (ISN) 建置
- `build_inter_site_network(isn_name)` - 建立站點間網路
  - 支援 External_Fabric 模板
  - 自動設定 FABRIC_TYPE="External"
  - 處理 ISN 特有的 freeform 配置

##### 4. 子 Fabric 管理 (Child Fabric Management)
- `add_child_fabrics_to_msd(msd_name)` - 將子 fabric 添加到 MSD
  - 自動從 YAML 配置提取子 fabric 清單
  - 支援一般 fabric 和 ISN fabric
  - 批次處理多個子 fabric
- `remove_child_fabrics_from_msd(msd_name)` - 從 MSD 移除子 fabric
  - 批次移除所有配置的子 fabric
- `link_fabrics(parent_fabric, child_fabric)` - 手動連結個別 fabric

**建議的執行順序 (Recommended Execution Sequence):**
```python
1. build_vxlan_evpn_fabric(fabric_name)  # 建立資料中心 fabric
2. build_multi_site_domain(msd_name)     # 建立 MSD (不含子 fabric)
3. build_inter_site_network(isn_name)    # 建立 ISN
4. add_child_fabrics_to_msd(msd_name)    # 添加子 fabric 到 MSD
```

**支援的配置類型 (Supported Configuration Types):**
- 🏗️ **Easy_Fabric**: VXLAN EVPN 資料中心 fabric
- 🌐 **MSD_Fabric**: Multi-Site Domain 跨站點管理
- 🔗 **External_Fabric**: Inter-Site Network 站點間連接

##### Note
- AAA Freeform config = AAA_SERVER_CONF
- Spine Freeform config = EXTRA_CONF_SPINE
- Leaf Freeform config = EXTRA_CONF_LEAF
#### [Switch](scripts/cisco/12.2.2/api/switch.py)
- Switch read / delete
- Switch discover (add)
- Read switch pending config
- Read switch diff config 
- Change discovery IP / rediscover IP 尚未測試
#### Interface
- 尚未測試
#### [Policy](scripts/cisco/12.2.2/api/policy.py)
- Policy read / update / delete
#### [Network](scripts/cisco/12.2.2/api/network.py)
- Network create / read / update / delete
- Network attachment read / update
    - deployment = true 是接, deployment = false 是拔掉
    - Issue: 如果同時放 switchPorts, detachSwitchPorts, deployment = true 還是會拔掉放在 detachSwitchPorts 的 ports
    - 接的時候要將 deployment 設定成 true 並確定沒有 detachSwitchPorts 出現
    - 拔的時候要將 deployment 設定成 false 並確定有放 detachSwitchPorts
- Preview network (generate pending config)
- Deploy network
#### [VRF](scripts/cisco/12.2.2/api/vrf.py)
- VRF create / read / update / delete
- VRF attachment read / update

## Scripts
### 腳本執行環境 (Script Execution Environment)
- **Python 3.x** 環境
- **工作目錄**: `scripts/cisco/12.2.2/`
- **API 模組目錄**: `scripts/cisco/12.2.2/api/`
- **主要依賴**: `yaml`, `json`, `requests`, `pathlib`, `dataclasses`

### 使用方式 (Usage)
```python
# 初始化 Fabric Builder (在 scripts/cisco/12.2.2/ 目錄下執行)
from build_fabric import FabricBuilderMethods
fabric_methods = FabricBuilderMethods()

# 建置完整的網路架構
fabric_methods.build_vxlan_evpn_fabric("Site1-Greenfield")
fabric_methods.build_multi_site_domain("MSD-Test") 
fabric_methods.build_inter_site_network("ISN-Test")
fabric_methods.add_child_fabrics_to_msd("MSD-Test")
```

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
### 進行中項目 (Work in Progress)
- 🔄 **測試與驗證**: 完整的功能測試和驗證
- 🔄 **文件更新**: API 文檔和使用指南的完善

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