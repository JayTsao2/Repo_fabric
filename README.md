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
│   │   │   │   ├── fabric/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── create_fabric.py
│   │   │   │   │   ├── update_fabric.py
│   │   │   │   │   └── delete_fabric.py
│   │   │   │   ├── vrf/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── create_vrf.py
│   │   │   │   │   ├── update_vrf.py
│   │   │   │   │   ├── delete_vrf.py
│   │   │   │   │   └── attach_vrf.py
│   │   │   │   ├── network/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── config_utils.py
│   │   │   │   └── common_utils.py
│   │   │   ├── resources/
│   │   │   ├── fabric_cli.py
│   │   │   ├── vrf_cli.py
│   │   │   └── network_cli.py
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
                
            * 📂 **`/scripts/cisco/12.2.2/modules/vrf`**
                * 用途: VRF 管理模組，包含建立、更新、刪除、附加、分離功能。
                
            * � **`/scripts/cisco/12.2.2/modules/network`**
                * 用途: Network 管理模組，提供統一的網路 CRUD 操作與交換器附加功能。
            
            * 📄 **`/scripts/cisco/12.2.2/modules/config_utils.py`**
                * 用途: 配置工具函數模組，提供 YAML 載入與驗證功能。
                
            * �📄 **`/scripts/cisco/12.2.2/modules/common_utils.py`**
                * 用途: 共用工具函數模組，提供跨模組的共同功能。
            
        * 📂 **`/scripts/cisco/12.2.2/resources`**
            * 用途: 配置檔案、模板、欄位映射等資源檔案。
            
        * 📄 **`/scripts/cisco/12.2.2/fabric_cli.py`**
            * 用途: Fabric 管理命令列介面工具。
            
        * 📄 **`/scripts/cisco/12.2.2/vrf_cli.py`**
            * 用途: VRF 管理命令列介面工具。
            
        * 📄 **`/scripts/cisco/12.2.2/network_cli.py`**
            * 用途: Network 管理命令列介面工具。
        
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

#### [VRF CLI](scripts/cisco/12.2.2/vrf_cli.py)
**VRF 管理命令列介面工具 (VRF Management CLI Tool)**

**功能說明 (Features):**
- 🏗️ **建立 VRF**: 從 YAML 配置檔案建立 VRF
- 🔧 **更新 VRF**: 更新現有 VRF 配置
- 🗑️ **刪除 VRF**: 安全刪除 VRF
- 🔗 **附加 VRF**: 將 VRF 附加到指定交換器
- 🔌 **分離 VRF**: 從指定交換器分離 VRF
- 📋 **自動偵測**: 自動從交換器介面配置中偵測 VRF

**使用方式 (Usage):**
```bash
# 在 scripts/cisco/12.2.2/ 目錄下執行
python vrf_cli.py create <vrf_name> <fabric_name>     # 建立特定 VRF
python vrf_cli.py update <vrf_name> <fabric_name>     # 更新特定 VRF
python vrf_cli.py delete <vrf_name>                   # 刪除特定 VRF
python vrf_cli.py attach <fabric_name> <switch_role> <switch_name>   # 附加 VRF 到交換器
python vrf_cli.py detach <fabric_name> <switch_role> <switch_name>   # 從交換器分離 VRF

# 範例
python vrf_cli.py attach Site3-Test leaf Site1-L3    # 附加 VRF 到指定 leaf 交換器
python vrf_cli.py detach Site3-Test leaf Site1-L3    # 從指定 leaf 交換器分離 VRF

# 顯示幫助資訊
python vrf_cli.py --help
```

#### [VRF Builder Modules](scripts/cisco/12.2.2/modules/vrf/)
**模組化 VRF 管理系統 (Modular VRF Management System)**

**模組結構 (Module Structure):**

##### 1. 核心模組 (`__init__.py`)
- `VRFTemplate` - VRF 模板枚舉
- `VRFConfig` - 配置路徑資料類別
- `VRFBuilder` - 主要建置類別
- `VRFPayloadGenerator` - API 資料產生器
- `BaseVRFMethods` - 基礎方法類別

##### 2. 建立模組 (`create_vrf.py`)
- `VRFCreator` - VRF 建立操作類別
  - `create_vrf(vrf_name)` - VRF 建立方法

**高層邏輯流程 (High-Level Logic Flow):**
1. 從 `5_segment/vrf.yaml` 載入 VRF 配置
2. 載入預設配置和欄位映射
3. 合併配置並生成 API payload
4. 透過 NDFC API 建立 VRF
5. 驗證建立結果

##### 3. 更新模組 (`update_vrf.py`)
- `VRFUpdater` - VRF 更新操作類別
  - `update_vrf(vrf_name)` - VRF 更新方法

**高層邏輯流程 (High-Level Logic Flow):**
1. 從 `5_segment/vrf.yaml` 載入更新後的 VRF 配置
2. 載入預設配置和欄位映射
3. 合併配置並生成 API payload
4. 透過 NDFC API 更新現有 VRF
5. 驗證更新結果

##### 4. 刪除模組 (`delete_vrf.py`)
- `VRFDeleter` - VRF 刪除操作類別
  - `delete_vrf(vrf_name)` - VRF 刪除方法

**高層邏輯流程 (High-Level Logic Flow):**
1. 從配置中查找指定的 VRF
2. 驗證 VRF 存在性
3. 透過 NDFC API 刪除 VRF
4. 驗證刪除結果

##### 5. 附加/分離模組 (`attach_vrf.py`)
- `VRFAttachment` - VRF 附加/分離操作類別
  - `manage_vrf_by_switch(fabric_name, switch_role, switch_name, operation)` - 主要附加/分離方法

**高層邏輯流程 (High-Level Logic Flow):**
1. **載入交換器配置**: 從 `3_node/{fabric}/{role}/{switch}.yaml` 載入交換器配置
2. **VRF 自動偵測**: 掃描交換器介面，尋找具有 `int_routed_host` policy 的介面
3. **提取 VRF 資訊**: 從匹配介面的 `Interface VRF` 欄位提取 VRF 名稱
4. **驗證 VRF 存在性**: 在 `5_segment/vrf.yaml` 中驗證 VRF 配置
5. **生成 API Payload**: 建立包含交換器序號、VLAN ID 等資訊的 payload
6. **執行操作**: 透過 NDFC API 執行附加 (deployment=true) 或分離 (deployment=false) 操作
7. **驗證結果**: 確認操作成功完成

**Console 輸出範例:**
```
=== Attaching VRF to switch: Site1-L3 ===
📋 Found interface Ethernet1/4 with policy 'int_routed_host' and VRF 'bluevrf'
Found VRF bluevrf in Site1-L3 (9J9UDVX8MMA) in Site3-Test
✅ SUCCESS: Vrf Attach - bluevrf (VLAN 2000) to Site1-L3
```

#### [Network CLI](scripts/cisco/12.2.2/network_cli.py)
**Network 管理命令列介面工具 (Network Management CLI Tool)**

**功能說明 (Features):**
- 🏗️ **建立 Network**: 從 YAML 配置檔案建立 Network
- 🔧 **更新 Network**: 更新現有 Network 配置
- 🗑️ **刪除 Network**: 安全刪除 Network
- 🔗 **附加 Network**: 將 Network 附加到指定交換器介面
- 🔌 **分離 Network**: 從指定交換器介面分離 Network
- 📋 **自動偵測**: 自動從交換器介面配置中偵測 Network 與 VLAN 對應

**使用方式 (Usage):**
```bash
# 在 scripts/cisco/12.2.2/ 目錄下執行
python network_cli.py create <fabric_name> <network_name>     # 建立特定 Network
python network_cli.py update <fabric_name> <network_name>     # 更新特定 Network
python network_cli.py delete <fabric_name> <network_name>     # 刪除特定 Network
python network_cli.py attach <fabric_name> <switch_role> <switch_name>   # 附加 Network 到交換器
python network_cli.py detach <fabric_name> <switch_role> <switch_name>   # 從交換器分離 Network

# 範例
python network_cli.py create Site1-Greenfield VLAN_101        # 建立 VLAN_101 Network
python network_cli.py attach Site1-Greenfield leaf Site1-L1   # 附加 Network 到指定 leaf 交換器
python network_cli.py detach Site1-Greenfield leaf Site1-L1   # 從指定 leaf 交換器分離 Network

# 顯示幫助資訊
python network_cli.py --help
```

#### [Network Manager Module](scripts/cisco/12.2.2/modules/network/)
**統一 Network 管理系統 (Unified Network Management System)**

**模組結構 (Module Structure):**

##### 1. 核心模組 (`__init__.py`)
- `NetworkTemplateConfig` - Network 模板配置資料類別
- `NetworkPayload` - API 請求資料結構類別
- `NetworkManager` - 統一 Network 管理類別

**核心類別說明 (Core Classes):**

##### NetworkTemplateConfig (資料類別)
- **用途**: 結構化的 Network 模板配置，包含所有必要欄位
- **功能**: 
  - `to_json()` - 轉換為 JSON 字串供 API 使用
  - `apply_defaults()` - 應用企業預設值與欄位映射

##### NetworkPayload (資料類別)
- **用途**: API 請求的完整資料結構
- **功能**:
  - `to_dict()` - 轉換為字典供 API 呼叫使用
  - 包含所有 NDFC API 所需的欄位

##### NetworkManager (主要管理類別)
**建立方法:**
- `create_network(fabric_name, network_name)` - Network 建立方法

**更新方法:**
- `update_network(fabric_name, network_name)` - Network 更新方法

**刪除方法:**
- `delete_network(fabric_name, network_name)` - Network 刪除方法

**附加/分離方法:**
- `attach_networks(fabric_name, role, switch_name)` - Network 附加方法
- `detach_networks(fabric_name, role, switch_name)` - Network 分離方法

**高層邏輯流程 (High-Level Logic Flow):**

**Network CRUD 操作:**
1. 從 `5_segment/network.yaml` 載入 Network 配置
2. 載入企業預設配置和欄位映射 (`resources/corp_defaults/`, `resources/_field_mapping/`)
3. 建立 `NetworkTemplateConfig` 和 `NetworkPayload` 資料結構
4. 合併配置並生成完整的 API payload
5. 透過 NDFC API 執行 Network 操作
6. 驗證操作結果

**Network 附加/分離操作:**
1. **載入交換器配置**: 從 `3_node/{fabric}/{role}/{switch}.yaml` 載入交換器配置
2. **介面自動偵測**: 掃描交換器介面，尋找具有 `int_access_host` 或 `int_trunk_host` policy 的介面
3. **Network 對應**: 
   - **Access 介面**: 從 `Access Vlan` 欄位提取 VLAN ID，對應到 Network
   - **Trunk 介面**: 從 `Trunk Allowed Vlans` 欄位提取多個 VLAN ID，對應到多個 Network
4. **驗證 Network 存在性**: 在 `5_segment/network.yaml` 中驗證 Network 配置
5. **執行操作**: 透過 NDFC API 執行附加或分離操作
6. **驗證結果**: 確認所有操作成功完成

**Console 輸出範例:**
```
Attaching networks to Site1-L1 (leaf) in Site1-Greenfield...
✅ Attached VLAN_101 to Ethernet1/1 (ACCESS)
✅ Attached VLAN_200 to Ethernet1/2 (TRUNK)
✅ Attached VLAN_300 to Ethernet1/2 (TRUNK)
✅ Success: Attached 3 network interfaces for Site1-L1
```

#### Network 配置檔案結構 (Network Configuration File Structure)
**Network 主配置**: `network_configs/5_segment/network.yaml`
```yaml
Network:
  - Fabric: Site1-Greenfield
    Network Name: VLAN_101
    Layer 2 Only: false
    VRF Name: VRF_101
    Network ID: 30101
    VLAN ID: 101
    IPv4 Gateway/NetMask: 10.1.1.1/24
    VLAN Name: VLAN_101
    Interface Description: "User Network 101"
```

**交換器配置**: `network_configs/3_node/{fabric}/{role}/{switch}.yaml`
```yaml
Serial Number: 9ABCDEFGHIJ
Interface:
  - Ethernet1/1:
      policy: int_access_host
      Access Vlan: 101
      Interface Description: "Access port for VLAN 101"
  - Ethernet1/2:
      policy: int_trunk_host
      Trunk Allowed Vlans: "200,300,400"
      Interface Description: "Trunk port for multiple VLANs"
```

#### VRF 配置檔案結構 (VRF Configuration File Structure)
**VRF 主配置**: `network_configs/5_segment/vrf.yaml`
```yaml
VRF:
  - VRF Name: bluevrf
    Fabric: Site3-Test
    VRF ID: 50001
    VLAN ID: 2000
    General Parameters:
      VRF Description: "Blue VRF for testing"
```

**交換器配置**: `network_configs/3_node/{fabric}/{role}/{switch}.yaml`
```yaml
Serial Number: 9J9UDVX8MMA
Interface:
  - Ethernet1/4:
      policy: int_routed_host
      Interface VRF: bluevrf
      Interface IP: 10.192.1.1
      IP Netmask Length: 24
```

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

**VRF CLI 使用方式 (VRF CLI Usage):**
```bash
# 在 scripts/cisco/12.2.2/ 目錄下執行
python vrf_cli.py create bluevrf Site3-Test
python vrf_cli.py update bluevrf Site3-Test
python vrf_cli.py delete bluevrf
python vrf_cli.py attach Site3-Test leaf Site1-L3
python vrf_cli.py detach Site3-Test leaf Site1-L3
```

**Network CLI 使用方式 (Network CLI Usage):**
```bash
# 在 scripts/cisco/12.2.2/ 目錄下執行
python network_cli.py create Site1-Greenfield VLAN_101
python network_cli.py update Site1-Greenfield VLAN_101
python network_cli.py delete Site1-Greenfield VLAN_101
python network_cli.py attach Site1-Greenfield leaf Site1-L1
python network_cli.py detach Site1-Greenfield leaf Site1-L1
```

**程式化使用模組 (Programmatic Module Usage):**
```python
# 在 scripts/cisco/12.2.2/ 目錄下執行

# Fabric 模組
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

# VRF 模組
from modules.vrf.create_vrf import VRFCreator
from modules.vrf.update_vrf import VRFUpdater
from modules.vrf.delete_vrf import VRFDeleter
from modules.vrf.attach_vrf import VRFAttachment

# 建立 VRF
vrf_creator = VRFCreator()
vrf_creator.create_vrf("bluevrf")

# 更新 VRF
vrf_updater = VRFUpdater()
vrf_updater.update_vrf("bluevrf")

# 刪除 VRF
vrf_deleter = VRFDeleter()
vrf_deleter.delete_vrf("bluevrf")

# 附加/分離 VRF
vrf_attachment = VRFAttachment()
vrf_attachment.manage_vrf_by_switch("Site3-Test", "leaf", "Site1-L3", "attach")
vrf_attachment.manage_vrf_by_switch("Site3-Test", "leaf", "Site1-L3", "detach")

# Network 模組
from modules.network import NetworkManager

# 建立統一 Network 管理器
network_manager = NetworkManager()

# 建立 Network
network_manager.create_network("Site1-Greenfield", "VLAN_101")

# 更新 Network
network_manager.update_network("Site1-Greenfield", "VLAN_101")

# 刪除 Network
network_manager.delete_network("Site1-Greenfield", "VLAN_101")

# 附加/分離 Network
network_manager.attach_networks("Site1-Greenfield", "leaf", "Site1-L1")
network_manager.detach_networks("Site1-Greenfield", "leaf", "Site1-L1")
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

- ✅ **VRF 模組化系統**: 完整的 VRF 管理系統
  - 建立 `modules/vrf/` 目錄結構
  - 分離 create、update、delete、attach、detach 功能到獨立模組
  - 建立 `vrf_cli.py` 命令列介面
  - YAML 配置驅動的 VRF 管理
  - 自動化 VRF 偵測和交換器附加/分離功能
  - 支援基於介面配置的智能 VRF 發現

- ✅ **Network 統一管理系統**: 完整的 Network 管理系統
  - 建立 `modules/network/` 統一模組架構
  - 單一 `NetworkManager` 類別提供所有 CRUD 操作
  - 建立 `network_cli.py` 命令列介面
  - YAML 配置驅動的 Network 管理
  - 自動化 Network 偵測和交換器介面附加/分離功能
  - 支援 Access 和 Trunk 介面的智能 VLAN 對應
  - 資料類別架構 (`NetworkTemplateConfig`, `NetworkPayload`) 提供型別安全
  - 簡化的函數傳播鏈，提升效能和維護性

### 進行中項目 (Work in Progress)
- 根據 3_node 內部的檔案打造出讀取 yaml 檔案以及 resources 檔案建立 Switch 配置
- 根據 1_vxlan_evpn 內部的檔案打造出能夠自動化建造、調整 fabric 的 CI/CD 流程
- 根據 3_node 內部的檔案打造出能夠自動化建造、調整 fabric 的 CI/CD 流程
- 根據 5_segment 內部的檔案打造出能夠自動化建造、調整 network 的 CI/CD 流程
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