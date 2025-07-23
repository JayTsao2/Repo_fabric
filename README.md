# Fabric Builder

## 專案資料夾結構 (Project Directory Structure)

```
.
├── scripts/
│   ├── cisco/
│   │   ├── 12.1.2e/
│   │   ├── 12.2.2/
│   │   │   ├── api/
│   │   │   ├── modules/
│   │   │   │   └── fabric/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── create_fabric.py
│   │   │   │       ├── update_fabric.py
│   │   │   │       └── delete_fabric.py
│   │   │   ├── resources/
│   │   │   ├── fabric_cli.py
│   │   │   └── config_utils.py
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
            
        * 📂 **`/scripts/cisco/12.2.2/modules`**
            * 用途: 模組化功能組織，包含 fabric、VRF、network、policy、switch 等模組。
            
            * 📂 **`/scripts/cisco/12.2.2/modules/fabric`**
                * 用途: Fabric 管理模組，包含建立、更新、刪除功能。
            
        * 📂 **`/scripts/cisco/12.2.2/resources`**
            * 用途: 配置檔案、模板、欄位映射等資源檔案。
            
        * � **`/scripts/cisco/12.2.2/build_fabric.py`**
            * 用途: 原始版本的 Fabric 建置工具 (已重構為模組化架構)。
            
        * 📄 **`/scripts/cisco/12.2.2/fabric_cli.py`**
            * 用途: Fabric 管理命令列介面工具。
            
        * 📄 **`/scripts/cisco/12.2.2/config_utils.py`**
            * 用途: 配置處理工具函數庫。
        
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
## Scripts
### Cisco NDFC 12.2.2

#### [Fabric CLI](scripts/cisco/12.2.2/fabric_cli.py)
**Fabric 管理命令列介面工具 (Fabric Management CLI Tool)**

**功能說明 (Features):**
- 🏗️ **建立 Fabric**: 支援各種類型的 fabric 建立
- 🔧 **更新 Fabric**: 更新現有 fabric 配置
- 🗑️ **刪除 Fabric**: 安全刪除 fabric (含確認提示)
- 📋 **自動類型偵測**: 自動從 YAML 配置檔案偵測 fabric 類型

**使用方式 (Usage):**
```bash
# 在 scripts/cisco/12.2.2/ 目錄下執行
python fabric_cli.py create <fabric_name>   # 建立特定 fabric
python fabric_cli.py update <fabric_name>   # 更新特定 fabric
python fabric_cli.py delete <fabric_name>   # 刪除特定 fabric (需確認)

# 顯示幫助資訊
python fabric_cli.py --help
```

**支援的 Fabric 類型:**
- ✅ **VXLAN EVPN Fabric**: 資料中心 VXLAN EVPN 架構
- ✅ **Multi-Site Domain (MSD)**: 多站點網域管理
- ✅ **Inter-Site Network (ISN)**: 站點間網路連接

#### [Fabric Builder Modules](scripts/cisco/12.2.2/modules/fabric/)
**模組化 Fabric 管理系統 (Modular Fabric Management System)**

**模組結構 (Module Structure):**

##### 1. 核心模組 (`__init__.py`)
- `FabricType` - Fabric 類型枚舉
- `FabricConfig` - 配置路徑資料類別
- `FreeformPaths` - Freeform 配置路徑
- `ChildFabrics` - 子 Fabric 容器
- `FabricBuilder` - 主要建置類別
- `PayloadGenerator` - API 資料產生器
- `BaseFabricMethods` - 基礎方法類別

##### 2. 建立模組 (`create_fabric.py`)
- `FabricCreator` - Fabric 建立操作類別
  - `build_fabric(fabric_name)` - 通用 fabric 建立方法
  - `build_vxlan_evpn_fabric()` - VXLAN EVPN fabric 建立
  - `build_multi_site_domain()` - MSD 建立
  - `build_inter_site_network()` - ISN 建立
  - `add_child_fabrics_to_msd()` - 添加子 fabric 到 MSD
  - `remove_child_fabrics_from_msd()` - 從 MSD 移除子 fabric

##### 3. 更新模組 (`update_fabric.py`)
- `FabricUpdater` - Fabric 更新操作類別
  - `update_fabric(fabric_name)` - 通用 fabric 更新方法
  - `update_vxlan_evpn_fabric()` - VXLAN EVPN fabric 更新
  - `update_multi_site_domain()` - MSD 更新
  - `update_inter_site_network()` - ISN 更新

##### 4. 刪除模組 (`delete_fabric.py`)
- `FabricDeleter` - Fabric 刪除操作類別
  - `delete_fabric(fabric_name)` - 通用 fabric 刪除方法

##### Note
- AAA Freeform config = AAA_SERVER_CONF
- Spine Freeform config = EXTRA_CONF_SPINE
- Leaf Freeform config = EXTRA_CONF_LEAF

#### API Interfaces

##### [Fabric](scripts/cisco/12.2.2/api/fabric.py)
- `create_fabric(fabric_name, template_name, payload_data)` - 使用直接傳遞的 payload 資料創建 fabric
- `update_fabric(fabric_name, template_name, payload_data)` - 使用直接傳遞的 payload 資料更新 fabric
- `get_fabric(fabric_name, fabric_dir)` - 讀取 fabric 配置
- `delete_fabric(fabric_name)` - 刪除 fabric
- `recalculate_config(fabric_name)` - 重新計算 fabric 配置
- `deploy_fabric_config(fabric_name)` - 部署 fabric 配置
- `add_MSD(parent_fabric_name, child_fabric_name)` - 將子 fabric 添加到 Multi-Site Domain
- `remove_MSD(parent_fabric_name, child_fabric_name)` - 從 Multi-Site Domain 移除子 fabric

##### [Switch](scripts/cisco/12.2.2/api/switch.py)
- Switch read / delete
- Switch discover (add)
- Read switch pending config
- Read switch diff config 
- Change discovery IP / rediscover IP 尚未測試
##### Interface
- 尚未測試
##### [Policy](scripts/cisco/12.2.2/api/policy.py)
- Policy read / update / delete
##### [Network](scripts/cisco/12.2.2/api/network.py)
- Network create / read / update / delete
- Network attachment read / update
    - deployment = true 是接, deployment = false 是拔掉
    - Issue: 如果同時放 switchPorts, detachSwitchPorts, deployment = true 還是會拔掉放在 detachSwitchPorts 的 ports
    - 接的時候要將 deployment 設定成 true 並確定沒有 detachSwitchPorts 出現
    - 拔的時候要將 deployment 設定成 false 並確定有放 detachSwitchPorts
- Preview network (generate pending config)
- Deploy network
##### [VRF](scripts/cisco/12.2.2/api/vrf.py)
- VRF create / read / update / delete
- VRF attachment read / update

#### 腳本執行環境 (Script Execution Environment)
- **Python 3.x** 環境
- **工作目錄**: `scripts/cisco/12.2.2/`
- **CLI 工具**: `fabric_cli.py` (推薦使用)
- **模組目錄**: `scripts/cisco/12.2.2/modules/fabric/`
- **API 模組目錄**: `scripts/cisco/12.2.2/api/`
- **工具函數**: `config_utils.py`
- **主要依賴**: `yaml`, `json`, `requests`, `pathlib`, `dataclasses`, `argparse`

#### 使用方式 (Usage)

**推薦使用 CLI 工具 (Recommended CLI Usage):**
```bash
# 在 scripts/cisco/12.2.2/ 目錄下執行
python fabric_cli.py create Site1-Greenfield
python fabric_cli.py create MSD-Test
python fabric_cli.py create ISN-Test
python fabric_cli.py update Site1-Greenfield
python fabric_cli.py delete ISN-Test  # 需要確認
```

**程式化使用模組 (Programmatic Module Usage):**
```python
# 在 scripts/cisco/12.2.2/ 目錄下執行
from modules.fabric.create_fabric import FabricCreator
from modules.fabric.update_fabric import FabricUpdater
from modules.fabric.delete_fabric import FabricDeleter

# 建立 fabric
creator = FabricCreator()
creator.build_fabric("Site1-Greenfield")

# 更新 fabric
updater = FabricUpdater() 
updater.update_fabric("Site1-Greenfield")

# 刪除 fabric
deleter = FabricDeleter()
deleter.delete_fabric("Site1-Greenfield")
```

**Legacy 使用方式 (Legacy Usage):**
```python
# 使用原始 build_fabric.py (不推薦)
from build_fabric import FabricBuilderMethods
fabric_methods = FabricBuilderMethods()
fabric_methods.build_vxlan_evpn_fabric("Site1-Greenfield")
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
### 已完成項目 (Completed Items)
- ✅ **Fabric 模組化重構**: 將原始 `build_fabric.py` 重構為模組化架構
  - 建立 `modules/fabric/` 目錄結構
  - 分離 create、update、delete 功能到獨立模組
  - 建立 `fabric_cli.py` 命令列介面
  - 簡化 delete 功能，移除不必要的類型複雜性
  - 移除 bulk 操作，專注於單一 fabric 操作

### 進行中項目 (Work in Progress)
- 根據 5_segment 內部的檔案打造出讀取 yaml 檔案以及 resources/ 檔案建立 network / VRF 配置
- 根據 3_node 內部的檔案打造出讀取 yaml 檔案以及 resources 檔案建立 Switch 配置
- 根據 5_segment 內部的檔案打造出能夠自動化建造、調整 network / VRF 的 CI/CD 流程
- 根據 1_vxlan_evpn 內部的檔案打造出能夠自動化建造、調整 fabric 的 CI/CD 流程
- 根據 3_node 內部的檔案打造出能夠自動化建造、調整 fabric 的 CI/CD 流程
- 透過 Nornir / NAPALM 等套件打造出能夠獲取 inventory/ 內部檔案的 Switch 資訊

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