## 問題處理

## 2025/09/13

- 設備會出現 Interface Admin Status up / 但實際是 down 的狀態
  - 需要到 CML 中將該設備 Interface 先 shutdown 再 no shutdown

- 如果實際上沒開機的設備, 例如 Site1-BGW3, 就必須取消對該設備的連線描述
  - 舉例 : Site1-DCI-1.yaml 中, 不應該有 :
  
```
  - Ethernet1/3:
      Interface Description: Site1-BGW3
      Enable Interface: True

  - Ethernet1/6:
      Interface Description: Site2-BGW3
      Enable Interface: True

```
- 當 Switch Add 和 Switch Delete 的時候 , 也應該要有相對應的連線增加或減少
  - 同理 , 當增加 Site1-L3 Switch 的時候 , 同時也要增加 Site1-S1,Site2-S2 的以下

```
  - Ethernet1/3:
      Interface Description: Site1-L3
      Enable Interface: True
```

## 2025/9/15 Jay 針對 Repo 上述問題進行修正 , 刪除不存在的連線

## 2025/09/21 
- add switch 的時候報錯 403
  - Site1-L2 的 serial number 錯誤，造成加入失敗, 修正後即正常

## 未來須考慮增加檢查機制，有任何 add Switch 動作之前即檢查，檢查如果不一致就不用往下執行

- 確認所有YAML 中，無 policy 的 interface 為 admin ip / operation status up , 才開始動作
- 確認 YAML 中每一台 switch 的以下狀況正常 (Get)
  - hostname
  - IP 確認可達
  - S/N 回傳值與 YAML 相同
  - Platform
  - version

  









