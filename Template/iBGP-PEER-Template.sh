template peer iBGP-PEER-Template
  remote-as ${my_var:-default_value}
  log-neighbor-changes
  update-source loopback1
  address-family l2vpn evpn
    send-community
    send-community extended
    route-reflector-client
