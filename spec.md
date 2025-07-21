# Fabric Builder
## 專案資料夾結構 (Project Directory Structure)

```
.
├── scripts/
│   ├── api/
│   │   └── cisco/
│   │       ├── 12.1.2e/
│   │       ├── 12.2.2/
│   │       └── 12.3/
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
    
    * 📂 **`/scripts/api`**
        * 用途: 放置所有 API 請求相關的邏輯與模組。
        
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
#### [Fabric](scripts/api/cisco/12.2.2/fabric.py)
- Fabric create / read / update / delete
- Fabric recalculate
- Fabric deploy
##### Note
- AAA Freeform config = AAA_SERVER_CONF
- Spine Freeform config = EXTRA_CONF_SPINE
- Leaf Freeform config = EXTRA_CONF_LEAF
#### [Switch](scripts/api/cisco/12.2.2/switch.py)
- Switch read / delete
- Switch discover (add)
- Read switch pending config
- Read switch diff config 
- Change discovery IP / rediscover IP 尚未測試
#### Interface
- 尚未測試
#### [Policy](scripts/api/cisco/12.2.2/policy.py)
- Policy read / update / delete
#### [Network](scripts/api/cisco/12.2.2/network.py)
- Network create / read / update / delete
- Network attachment read / update
    - deployment = true 是接, deployment = false 是拔掉
    - Issue: 如果同時放 switchPorts, detachSwitchPorts, deployment = true 還是會拔掉放在 detachSwitchPorts 的 ports
    - 接的時候要將 deployment 設定成 true 並確定沒有 detachSwitchPorts 出現
    - 拔的時候要將 deployment 設定成 false 並確定有放 detachSwitchPorts
- Preview network (generate pending config)
- Deploy network
#### [VRF](scripts/api/cisco/12.2.2/vrf.py)
- VRF create / read / update / delete
- VRF attachment read / update

## Scripts
TODO
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
- 透過 jinjia2 產生網頁直接讓他填 config