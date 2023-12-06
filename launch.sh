#!/bin/bash -x
#
# QEMU emulator launcher script.
#
###############################################################################

. config.ini

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit -1
fi

qemu-system-arm -M virt,highmem=off \
  -m 2G -smp 2 -cpu cortex-a7 \
  -kernel zImage \
  -device virtio-scsi-device \
  -device scsi-hd,drive=SystemDisk \
  -drive file=${FIRMWARE_IMAGE},format=raw,if=none,id=SystemDisk \
  -append "${BOOT_PARAMS}" \
  -no-reboot \
  -nographic \
  -serial mon:stdio \
  -object rng-random,filename=/dev/random,id=rng0 \
  -netdev tap,id=tap0net,ifname=${ETH_1},script=no,downscript=no \
  -device virtio-net-device,netdev=tap0net,mac=${ETH_1_MAC} \
  -netdev tap,id=tap1net,ifname=${ETH_0},script=no,downscript=no \
  -device virtio-net-device,netdev=tap1net,mac=${ETH_0_MAC} \
  -object can-bus,id=canbus0 \
  -object can-host-socketcan,id=canhost0,if=can0,canbus=canbus0 \
  -device kvaser_pci,canbus=canbus0 \

