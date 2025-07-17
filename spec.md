
## Gitlab 三道關卡 (Gitlab Three Checkpoints)
| 關卡 (Stage) | 驗證項目 (Verification Item) |
| :--- | :--- |
| **Pre-test** | ❶ 格式驗證 (確認所需資料 / 項目數量 ) (Format Validation - Confirm required data / number of items) |
| | ❷ Get 所有有使用中的 API 並比對與現行 YAML 數據是否一致 (Get all in-use APIs and compare with current YAML data for consistency) |
| | ❸ 該 Change 是否已有相對應的完整 API 動作 (Whether the change has a corresponding complete API action) |
| **Reviewer / Approval** | ❶ Repo Diff |
| | ❷ Pending Config 提供簽核者 (Pending Config provided to the approver) |

-----

## Fabric Build

### New Fabric Build
- Fabric build

### All Freeform modification
- Recalculate and Deploy

### Create Freeform Policy API

### Revise Border to GigaCore BGP

### Route Leak Modification
---
## VRF

### Add VRF
### Attach Route Port to VRF
### Attach VLAN to VRF
### Remove VRF

- Pre-check:
    - Ensure no VLAN use this VRF
    - Ensure no Equipments use this VRF
-----

## Network

### Add Network
### Attach Port to VLAN
### Change VLAN of a Port
### Remove Network

- Pre-check:
    - Ensure no VRF use this network
    - Ensure no Equipments use this network
-----

## Switch / Rack

### Add Switch
- Add Switch
- Recalculate and Deploy
### Create Switch - Hostname Policy
- Get Policy ID (need to record)
- Revise Policy ID API
### Revise Hostname
### Remove Switch
- Delete Switch
- Recalculate and Deploy
### Change Management IP
- Console change IP
- Change Discovery IP
- Re-discovery
- What is the action of YAML?