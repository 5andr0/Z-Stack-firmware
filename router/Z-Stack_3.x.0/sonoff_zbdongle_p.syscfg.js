/*
 * Sonoff ZBDongle-P (CC2652P) hardware settings applied after the SDK's
 * CC1352P-2 LaunchPad GenericApp configuration.
 */

// Preserve the serial ROM bootloader path used by Sonoff's web flasher.
device.enableBootloader = true;
device.enableBootloaderBackdoor = true;
device.dioBootloaderBackdoor = 15;
device.levelBootloaderBackdoor = "Active low";

// Match Koenkk's launchpad build power/clock configuration.
device.forceVddr = true;
device.enableDCDC = false;

// Three 8 KiB NV pages, matching preinclude.h and the linker command file.
NVS1.internalFlash.regionBase = 0x50000;
NVS1.internalFlash.regionSize = 0x6000;

// Search every Zigbee channel and use the CC2652P high-power RF design.
zstack.rf.primaryChannels = [11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26];
zstack.rf.txPower = "20";
