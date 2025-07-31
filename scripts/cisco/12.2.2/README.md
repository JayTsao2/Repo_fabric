# 資料夾用途說明

* **`/scripts/cisco/12.2.2/api`**
    * 用途: Cisco NDFC 12.2.2 版本的 API 操作模組。
    
* **`/scripts/cisco/12.2.2/modules`**
    * 用途: 模組化功能組織，包含 fabric、VRF、network、interface、switch 等模組。
    
    * **`/scripts/cisco/12.2.2/modules/fabric`**
        * 用途: Fabric 管理模組，包含建立、更新、刪除功能以及統一管理介面 (FabricManager)。
        
    * **`/scripts/cisco/12.2.2/modules/vrf`**
        * 用途: VRF 管理模組，包含建立、更新、刪除、附加、分離功能以及統一管理介面 (VRFManager)。
        
    * **`/scripts/cisco/12.2.2/modules/network`**
        * 用途: Network 管理模組，提供統一的網路 CRUD 操作與交換器附加功能。
        
    * **`/scripts/cisco/12.2.2/modules/interface`**
        * 用途: Interface 管理模組，提供 YAML 驅動的介面配置更新功能。
        
    * **`/scripts/cisco/12.2.2/modules/switch`**
        * 用途: Switch 管理模組，提供交換器發現、刪除、角色設定、IP 變更等功能。
    
    * **`/scripts/cisco/12.2.2/modules/vpc`**
        * 用途: VPC 管理模組，提供 VPC 配對建立、刪除、政策配置等功能。
    
    * **`/scripts/cisco/12.2.2/modules/config_utils.py`**
        * 用途: 配置工具函數模組，提供 YAML 載入與驗證功能。
    
* **`/scripts/cisco/12.2.2/resources`**
    * 用途: 配置檔案、模板、欄位映射等資源檔案。
    
* **`/scripts/cisco/12.2.2/fabric_cli.py`**
    * 用途: Fabric 管理命令列介面工具，使用 FabricManager 提供統一的操作介面。
    
* **`/scripts/cisco/12.2.2/vrf_cli.py`**
    * 用途: VRF 管理命令列介面工具，使用 VRFManager 提供統一的操作介面。
    
* **`/scripts/cisco/12.2.2/network_cli.py`**
    * 用途: Network 管理命令列介面工具。
    
* **`/scripts/cisco/12.2.2/interface_cli.py`**
    * 用途: Interface 管理命令列介面工具。

* **`/scripts/cisco/12.2.2/switch_cli.py`**
    * 用途: Switch 管理命令列介面工具。
# API Interfaces

## [Fabric](api/fabric.py)
- `create_fabric(fabric_name, template_name, payload_data)` - 使用直接傳遞的 payload 資料創建 fabric
- `update_fabric(fabric_name, template_name, payload_data)` - 使用直接傳遞的 payload 資料更新 fabric
- `get_fabric(fabric_name, fabric_dir)` - 讀取 fabric 配置
- `delete_fabric(fabric_name)` - 刪除 fabric
- `recalculate_config(fabric_name)` - 重新計算 fabric 配置
- `get_pending_config(fabric_name)` - 獲取待部署配置並格式化輸出至 pending.txt
- `deploy_fabric_config(fabric_name)` - 部署 fabric 配置
- `add_MSD(parent_fabric_name, child_fabric_name)` - 將子 fabric 添加到 Multi-Site Domain
- `remove_MSD(parent_fabric_name, child_fabric_name)` - 從 Multi-Site Domain 移除子 fabric

## [Switch](api/switch.py)
- Switch read / delete
- Switch discover (add)
- Read switch pending config
- Read switch diff config 
- Change discovery IP / rediscover IP 尚未測試
## [Interface](api/interface.py)
- `update_interface(fabric_name, policy, interfaces_payload)` - 使用直接傳遞的 payload 資料更新介面配置
- `get_interfaces(serial_number, if_name, template_name, interface_dir, save_by_policy)` - 讀取介面配置，支援按政策分組儲存
## [Policy](api/policy.py)
- Policy read / update / delete
## [Network](api/network.py)
- Network create / read / update / delete
- Network attachment read / update
    - deployment = true 是接, deployment = false 是拔掉
    - Issue: 如果同時放 switchPorts, detachSwitchPorts, deployment = true 還是會拔掉放在 detachSwitchPorts 的 ports
    - 接的時候要將 deployment 設定成 true 並確定沒有 detachSwitchPorts 出現
    - 拔的時候要將 deployment 設定成 false 並確定有放 detachSwitchPorts
- Preview network (generate pending config)
- Deploy network
## [VRF](api/vrf.py)
- VRF create / read / update / delete
- VRF attachment read / update

# CLI Tools

## [Fabric CLI](scripts/cisco/12.2.2/fabric_cli.py)

**使用方式 (Usage):**
```bash
# 在 scripts/cisco/12.2.2/ 目錄下執行
python fabric_cli.py create <fabric_name>      # 建立特定 fabric
python fabric_cli.py update <fabric_name>      # 更新特定 fabric
python fabric_cli.py delete <fabric_name>      # 刪除特定 fabric (需確認)
python fabric_cli.py recalculate <fabric_name> # 重新計算 fabric 配置
python fabric_cli.py get-pending <fabric_name> # 獲取待部署配置 (儲存至 pending.txt)
python fabric_cli.py deploy <fabric_name>      # 部署 fabric 配置
python fabric_cli.py workflow <fabric_name>    # 完整部署工作流程 (重新計算->查看待部署->部署)
python fabric_cli.py add-msd <parent> <child>  # 將子 fabric 加入 MSD
python fabric_cli.py remove-msd <parent> <child> # 從 MSD 移除子 fabric

# 顯示幫助資訊
python fabric_cli.py --help
```

## [VRF CLI](scripts/cisco/12.2.2/vrf_cli.py)

**使用方式 (Usage):**
```bash
# 在 scripts/cisco/12.2.2/ 目錄下執行
python vrf_cli.py create <fabric_name> <vrf_name>     # 建立特定 VRF
python vrf_cli.py update <fabric_name> <vrf_name>     # 更新特定 VRF
python vrf_cli.py delete <vrf_name>                   # 刪除特定 VRF
python vrf_cli.py attach <fabric_name> <switch_role> <switch_name>   # 附加 VRF 到交換器
python vrf_cli.py detach <fabric_name> <switch_role> <switch_name>   # 從交換器分離 VRF

# 範例
python vrf_cli.py attach Site1 leaf Site1-L1    # 附加 VRF 到指定 leaf 交換器
python vrf_cli.py detach Site1 leaf Site1-L1    # 從指定 leaf 交換器分離 VRF

# 顯示幫助資訊
python vrf_cli.py --help
```

## [Network CLI](scripts/cisco/12.2.2/network_cli.py)

**使用方式 (Usage):**
```bash
# 在 scripts/cisco/12.2.2/ 目錄下執行
python network_cli.py create <fabric_name> <network_name>     # 建立特定 Network
python network_cli.py update <fabric_name> <network_name>     # 更新特定 Network
python network_cli.py delete <fabric_name> <network_name>     # 刪除特定 Network
python network_cli.py attach <fabric_name> <switch_role> <switch_name>   # 附加 Network 到交換器
python network_cli.py detach <fabric_name> <switch_role> <switch_name>   # 從交換器分離 Network

# 範例
python network_cli.py create Site1 bluenet1        # 建立 bluenet1 Network
python network_cli.py attach Site1 leaf Site1-L1   # 附加 Network 到指定 leaf 交換器
python network_cli.py detach Site1 leaf Site1-L1   # 從指定 leaf 交換器分離 Network

# 顯示幫助資訊
python network_cli.py --help
```


## [Interface CLI](scripts/cisco/12.2.2/interface_cli.py)
**使用方式 (Usage):**
```bash
# 在 scripts/cisco/12.2.2/ 目錄下執行
python interface_cli.py <fabric_name> <role> <switch_name>   # 更新指定交換器的所有介面

# 範例
python interface_cli.py Site1 leaf Site1-L1            # 更新 Site1-L1 交換器的所有介面配置

# 顯示幫助資訊
python interface_cli.py --help
```

## [Switch CLI](scripts/cisco/12.2.2/switch_cli.py)

**使用方式 (Usage):**
```bash
# 在 scripts/cisco/12.2.2/ 目錄下執行
python switch_cli.py discover <fabric_name> <role> <switch_name> [--preserve]   # 發現交換器
python switch_cli.py delete <fabric_name> <role> <switch_name>                  # 刪除交換器
python switch_cli.py set-role <switch_name>                                     # 設定交換器角色
python switch_cli.py change-ip <fabric_name> <role> <switch_name> <original-ip>/<mask> <new-ip>/<mask>  # 變更管理 IP
python switch_cli.py set-freeform <fabric_name> <role> <switch_name>           # 執行 freeform 配置
python switch_cli.py hostname <fabric_name> <role> <switch_name> <new_hostname>  # 變更交換器主機名稱
python switch_cli.py create-vpc <fabric_name>                                  # 建立 VPC 配對並設定政策
python switch_cli.py delete-vpc <fabric_name> <switch_name>                    # 刪除指定交換器的 VPC 配對

# 範例
python switch_cli.py discover Site1 leaf Site1-L1 --preserve             # 發現交換器並保留配置
python switch_cli.py delete Site1 leaf Site1-L1                          # 從 fabric 移除交換器
python switch_cli.py set-role Site1-L1                                        # 設定 Site1-L1 的角色
python switch_cli.py change-ip Site1 leaf Site1-L1 10.192.195.73/24 10.192.195.74/24  # 變更管理 IP
python switch_cli.py set-freeform Site1 border_gateway Site1-BGW2  # 執行 freeform 配置
python switch_cli.py hostname Site1 leaf Site1-L1 Site1-L1-NEW           # 變更主機名稱
python switch_cli.py create-vpc Site1                                         # 建立 Site1 fabric 所有 VPC 配對
python switch_cli.py delete-vpc Site1 Site1-L1                               # 刪除 Site1-L1 交換器的 VPC 配對

# 顯示幫助資訊
python switch_cli.py --help
python switch_cli.py <command> --help
```

# Manager 可使用功能

## FabricManager
- `create_fabric(fabric_name: str)` - 建立指定的 fabric
- `update_fabric(fabric_name: str)` - 更新指定的 fabric
- `delete_fabric(fabric_name: str)` - 刪除指定的 fabric
- `recalculate_config(fabric_name: str)` - 重新計算 fabric 配置
- `get_pending_config(fabric_name: str)` - 獲取待部署配置
- `deploy_fabric(fabric_name: str)` - 部署 fabric 配置
- `add_to_msd(parent_fabric: str, child_fabric: str)` - 將子 fabric 添加到 Multi-Site Domain
- `remove_from_msd(parent_fabric: str, child_fabric: str, force: bool = False)` - 從 Multi-Site Domain 移除子 fabric

## VRFManager
- `create_vrf(fabric_name: str, vrf_name: str)` - 在指定 fabric 建立 VRF
- `update_vrf(fabric_name: str, vrf_name: str)` - 更新指定 VRF
- `delete_vrf(fabric_name: str, vrf_name: str)` - 刪除指定 VRF
- `attach_vrf(fabric_name: str, role: str, switch_name: str)` - 將 VRF 附加到指定交換器
- `detach_vrf(fabric_name: str, role: str, switch_name: str)` - 從指定交換器分離 VRF

## NetworkManager
- `create_network(fabric_name: str, network_name: str)` - 建立網路
- `update_network(fabric_name: str, network_name: str)` - 更新網路
- `delete_network(fabric_name: str, network_name: str)` - 刪除網路
- `attach_networks(fabric_name: str, role: str, switch_name: str)` - 將網路附加到交換器
- `detach_networks(fabric_name: str, role: str, switch_name: str)` - 從交換器分離網路

## InterfaceManager
- `update_switch_interfaces(fabric_name: str, role: str, switch_name: str)` - 更新指定交換器的所有介面配置 (支援 policy 介面或是單純 開 / 關 介面)

## SwitchManager
- `discover_switch(fabric_name: str, role: str, switch_name: str, preserve_config: bool = False)` - 發現交換器
- `delete_switch(fabric_name: str, role: str, switch_name: str)` - 刪除交換器
- `set_switch_role(fabric_name: str, role: str, switch_name: str)` - 設定交換器角色
- `set_switch_role_by_name(switch_name: str)` - 根據交換器名稱設定角色
- `change_switch_ip(fabric_name: str, role: str, switch_name: str, original_ip_with_mask: str, new_ip_with_mask: str)` - 變更交換器管理 IP
- `set_switch_freeform(fabric_name: str, role: str, switch_name: str)` - 執行 freeform 配置
    - 注意: 這個會將 Policy 的 JSON 檔案存下來，以便之後能夠透過 API 讀取並執行
    - 因為在設定的時候實際上是創造出一個 freeform policy，如果之後沒有這個 JSON 檔案就無法知道正確的 policy ID 並做修改
- `change_switch_hostname(fabric_name: str, role: str, switch_name: str, new_hostname: str)` - 變更交換器主機名稱

## VPCManager
- `create_vpc_pairs(fabric_name: str)` - 建立指定 fabric 的所有 VPC 配對
- `delete_vpc_pairs(fabric_name: str, switch_name: str)` - 刪除指定交換器的 VPC 配對
