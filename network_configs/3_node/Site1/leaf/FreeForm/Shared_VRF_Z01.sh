router bgp $BGP_ASN
  vrf Z01
    neighbor Ethernet1/9-22
      inherit peer ebgp-peer-template-node

