feature tacacs+
tacacs-server deadtime 60
tacacs-server host 10.67.172.39 key 7 "qseieii"
tacacs-server host 10.67.172.40 key 7 "qseieii"
tacacs-server host 10.67.172.39 test username healthcheck idle-time 5
tacacs-server host 10.67.172.40 test username healthcheck idle-time 5
aaa group server tacacs+ nwadmin
    server 10.67.172.39
    server 10.67.172.40
    source-interface mgmt0
aaa authentication login default group nwadmin
aaa authorization config-commands default group nwadmin local
aaa authorization commands default group nwadmin local