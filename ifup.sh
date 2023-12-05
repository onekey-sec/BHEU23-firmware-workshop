#!/bin/bash -x
#
# Set up Ethernet and CAN interfaces for qemu emulated system.
#
###############################################################################

. config.ini

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit -1
fi

PID=$(pidof NetworkManager)
if [[ ! -z "${PID}" || ${PID} -gt 0 ]]; then
    echo "[!] We recommend disabling NetworkManager. It may interfere with qemu networking."
fi

ip tuntap add ${ETH_O} mode tap
ip tuntap add ${ETH_1} mode tap

echo "[+] setting up transparent bridge betwen host eth0 (${ETH_0}) and uplink"
brctl addbr ${BR_0}
brctl addif ${BR_0} ${ETH_0} ${OUT_IF}

echo "[+] setting up fixed ip on ${ETH_1}"
ip addr add 192.168.4.2/24 dev ${ETH_1}

echo "[+] bringing up interfaces and bridges"
ip link set dev ${ETH_0} up
ip link set dev ${ETH_1} up
ip link set dev ${BR_0} up

echo "[+] requesting dhcp lease on ${BR_0}"
dhclient ${BR_0} -v

echo "[+] setting up virtual CAN interfaces."
ip link add dev ${CAN_0} type vcan
#ip link set ${CAN_0} type can bitrate 1000000
ip link set ${CAN_0} up txqueuelen 1000
