router bgp $BGP_ASN
  vrf vpc11
    neighbor Ethernet1/9-22
      inherit peer ebgp-peer-template-node