# NetworkManager
- `sync(fabric_name: str)` - 完全同步 Network（刪除多餘、更新現有、創建缺失的 Network）
  - 比較 YAML 配置與 fabric 中現有 Network
  - 自動刪除 fabric 中多餘的 Network
  - 更新既存 Network 的配置
  - 創建缺失的 Network
- `create_network(fabric_name: str, network_name: str)` - 建立網路
  - 自動載入 Network 配置並建構 API payload
  - 支援 Layer 2 Only 和 Layer 3 網路
  - 合併企業預設配置與 Network 特定配置
  - 套用欄位映射轉換為 NDFC API 格式
- `update_network(fabric_name: str, network_name: str)` - 更新網路
- `delete_network(fabric_name: str, network_name: str)` - 刪除網路
- `attach_networks(fabric_name: str, role: str, switch_name: str)` - 將網路附加到交換器
  - 自動載入交換器配置和 Network 附加配置
  - 解析介面清單並建構附加 payload
  - 支援多個 Network 同時附加
- `detach_networks(fabric_name: str, role: str, switch_name: str)` - 從交換器分離網路

## NetworkManager 配置檔案結構
NetworkManager 使用 YAML 配置檔案來管理 Network 資訊：
- **Network 配置路徑**: `network_configs/5_segment/network.yaml`
- **企業預設配置**: `resources/corp_defaults/cisco_network.yaml`
- **欄位映射配置**: `resources/field_mapping/cisco_network.yaml`
- **交換器配置路徑**: `network_configs/3_node/{fabric_name}/{role}/{switch_name}.yaml`

### Network 配置檔案格式
```yaml
Network:
  - Network Name: "bluenet1"
    Fabric: "Site1"
    VLAN Name: "bluenet1_vlan"
    VLAN ID: 101
    Network ID: 30001
    Interface Description: "Blue Network Interface"
    VRF Name: "bluevrf"
    Layer 2 Only: false
    # Additional network-specific configurations
```

### Network 附加配置
交換器 YAML 檔案中的 Network 附加配置：
```yaml
Network Attachment:
  - Network Name: "bluenet1"
    Interface: "Ethernet1/1,Ethernet1/2"
  - Network Name: "rednet1"
    Interface: "Ethernet1/3-5"
```

## NetworkManager 特色功能
- **YAML 驅動配置**: 所有操作基於結構化 YAML 配置檔案
- **Layer 2/3 支援**: 支援純 Layer 2 網路和 Layer 3 網路配置
- **企業預設整合**: 自動合併企業預設配置與 Network 特定配置
- **欄位映射**: 自動將 YAML 配置轉換為 NDFC API 所需格式
- **智能同步**: 比較現有配置與目標配置，執行增量更新
- **VRF 整合**: 自動處理 Network 與 VRF 的關聯
- **延遲載入**: 配置檔案只在需要時載入，提升效能
- **錯誤處理**: 完善的檔案存在性檢查和配置驗證
- **介面解析**: 支援介面範圍表示法（如 Ethernet1/1-5）

## Network 同步流程
1. 獲取 fabric 中現有的所有 Network
2. 載入 YAML 配置中的目標 Network 清單
3. 識別需要刪除的 Network（存在於 fabric 但不在 YAML 中）
4. 識別需要建立的 Network（存在於 YAML 但不在 fabric 中）
5. 識別需要更新的 Network（同時存在於兩者中）
6. 按順序執行刪除、更新、建立操作

## Network 附加流程
1. 載入交換器配置檔案
2. 解析 Network Attachment 配置區段
3. 為每個 Network 建構附加 payload
4. 解析介面清單（支援範圍和清單格式）
5. 呼叫 NDFC API 執行附加操作

## Layer 2 Only 網路處理
- 當 `Layer 2 Only: true` 時，VRF Name 自動設為 "NA"
- 支援純 Layer 2 VLAN 擴展
- 不需要配置 Layer 3 閘道資訊

## 配置檔案範例

### Network 主配置檔案 (network_configs/5_segment/network.yaml)
```yaml
Network:
  - Network Name: "bluenet1"
    Fabric: "Site1"
    VLAN Name: "blue_vlan_101"
    VLAN ID: 101
    Network ID: 30001
    Interface Description: "Blue production network"
    VRF Name: "bluevrf"
    Layer 2 Only: false
  
  - Network Name: "mgmt_net"
    Fabric: "Site1"
    VLAN Name: "mgmt_vlan_999"
    VLAN ID: 999
    Network ID: 30999
    Interface Description: "Management network"
    VRF Name: "mgmtvrf"
    Layer 2 Only: true
  
  - Network Name: "rednet1"
    Fabric: "Site1"
    VLAN Name: "red_vlan_102"
    VLAN ID: 102
    Network ID: 30002
    Interface Description: "Red test network"
    VRF Name: "redvrf"
    Layer 2 Only: false
```

### 交換器 Network 附加配置
```yaml
# In switch YAML file: network_configs/3_node/Site1/leaf/Site1-L1.yaml
Network Attachment:
  - Network Name: "bluenet1"
    Interface: "Ethernet1/1,Ethernet1/2,Ethernet1/10-15"
  - Network Name: "rednet1"
    Interface: "Ethernet1/3,Ethernet1/4"
  - Network Name: "mgmt_net"
    Interface: "Ethernet1/48"
```

## 使用範例
```python
from modules.network import NetworkManager

network_manager = NetworkManager()

# 同步所有 Network
network_manager.sync("Site1")

# 建立特定 Network
network_manager.create_network("Site1", "bluenet1")

# 更新 Network
network_manager.update_network("Site1", "bluenet1")

# 附加 Network 到交換器
network_manager.attach_networks("Site1", "leaf", "Site1-L1")

# 從交換器分離 Network
network_manager.detach_networks("Site1", "leaf", "Site1-L1")

# 刪除 Network
network_manager.delete_network("Site1", "bluenet1")
```

## 與 VRF 的整合
NetworkManager 與 VRFManager 密切整合：
1. Network 建立前會檢查相關 VRF 是否存在
2. Layer 3 Network 需要指定有效的 VRF
3. Layer 2 Only Network 自動設定 VRF 為 "NA"
4. Network 刪除時會檢查相關依賴關係

## 錯誤處理
- 檔案不存在時提供明確錯誤訊息
- YAML 格式錯誤時顯示詳細資訊
- API 呼叫失敗時記錄錯誤詳情
- 配置驗證失敗時提供修正建議
