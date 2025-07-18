# Fabric Builder
## Network Config
- 需求: 讓網路工程師可以簡單的設定
- Need to check types
## API Interfaces
### Cisco NDFC 12.2.2
#### [Fabric](API/cisco/12.2.2/fabric.py)
- Fabric create / read / update / delete
- Fabric recalculate
- Fabric deploy
##### Note
- AAA Freeform config = AAA_SERVER_CONF
- Spine Freeform config = EXTRA_CONF_SPINE
- Leaf Freeform config = EXTRA_CONF_LEAF
#### [Switch](API/cisco/12.2.2/switch.py)
- Switch read / delete
- Switch discover (add)
- Read switch pending config
- Read switch diff config 
- Change discovery IP / rediscover IP 尚未測試
#### Interface
- 尚未測試
#### [Policy](API/cisco/12.2.2/policy.py)
- Policy read / update / delete
#### [Network](API/cisco/12.2.2/network.py)
- Network create / read / update / delete
- Network attachment read / update
    - deployment = true 是接, deployment = false 是拔掉
    - Issue: 如果同時放 switchPorts, detachSwitchPorts, deployment = true 還是會拔掉放在 detachSwitchPorts 的 ports
    - 接的時候要將 deployment 設定成 true 並確定沒有 detachSwitchPorts 出現
    - 拔的時候要將 deployment 設定成 false 並確定有放 detachSwitchPorts
- Preview network (generate pending config)
- Deploy network
#### [VRF](API/cisco/12.2.2/vrf.py)
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
1. NDFC 無法透過外網訪問
2. Network / VRF Preview and Deploy 無法使用(Timeout)