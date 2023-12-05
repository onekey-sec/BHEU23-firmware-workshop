#!/bin/bash -x
#
# Bring down Ethernet and CAN interfaces for qemu emulated system.
#
###############################################################################
. config.ini

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit -1
fi

ip link set dev ${ETH_0} down
ip link set dev ${ETH_1} down
brctl delif ${BR_0} ${ETH_0} ${OUT_IF} 
ip link set dev ${BR_0} down

brctl delbr ${BR_0}

ip link del ${ETH_0}
ip link del ${ETH_1}

echo "[+] bringing down virtual CAN interfaces."
ip link set ${CAN_0} down
ip link del ${CAN_0}
