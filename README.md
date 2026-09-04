# Z-Stack-firmware
This repository contains compilation instructions and compiled Z-Stack firmwares for the Texas Instruments [CC2530](https://www.ti.com/product/CC2530), [CC2531](https://www.ti.com/product/CC2531), [CC2538](https://www.ti.com/product/CC2538), [CC1352P](https://www.ti.com/product/CC1352P), [CC2652P](https://www.ti.com/product/CC2652P), [CC2652R](https://www.ti.com/product/CC2652R) and [CC2652RB](https://www.ti.com/product/CC2652RB).

## Philips Hue-compatible Sonoff ZBDongle-P router

This fork adds a hardware-tested router target for the **Sonoff Zigbee 3.0 USB
Dongle Plus (ZBDongle-P, 2021-07-29 V1.3, CC2652P)**. It joins an official
Philips Hue Bridge v2 as a mains-powered On/Off Light while retaining the
Z-Stack Zigbee Router role, so it participates in mesh routing.

Download the ready-to-flash production and USB-debug images from the
[latest release](https://github.com/5andr0/Z-Stack-firmware/releases/latest).
Detailed build, pairing, diagnostic, security, and compatibility information
is in the [Hue router documentation](router/Z-Stack_3.x.0/HUE_ROUTER.md).

The upstream GenericApp router does not join and appear as a Hue light without
three application/security changes:

1. Its endpoint must identify as HA On/Off Light `0x0100`, application device
   version `1`, with Basic, Identify, Groups, Scenes, and On/Off server clusters.
2. Hue classical commissioning transports the network key under the ZLL
   pre-installed trust-center link key instead of only `ZigBeeAlliance09`.
3. The virtual On/Off attribute and Off, On, Toggle, Groups, and Scenes command
   handlers must be implemented so Hue can interview and control the endpoint.

This fork installs the Hue key using TI's `zstack_UseAPSKeyWithFallback` mode.
The standard `ZigBeeAlliance09` key remains the fallback, so the firmware is
not restricted to Hue networks. The commissioning key is injected from a
GitHub Actions secret and is not stored in the repository.
