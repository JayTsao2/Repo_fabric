router bgp $BGP_ASN
  template peer ebgp-peer-template-node
    bfd
    remote-as $BGP_ASN
    address-family ipv4 unicast
      as-override
      disable-peer-as-check
      soft-reconfiguration inbound always
  vrf Z01
    neighbor Ethernet1/9-22
      inherit peer ebgp-peer-template-node

