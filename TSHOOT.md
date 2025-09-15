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
而當 Switch Add 和 Switch Delete 的時候 , 也應該要有相對應的連線增加或減少

## 2025/9/15 Jay 針對 Repo 上述問題進行修正 , 刪除不存在的連線

  









