# Sonoff ZBDongle-P Hue-compatible On/Off Light router

This target keeps TI GenericApp's Zigbee Router (`zr`) network role and changes
its application endpoint to a virtual ZHA On/Off Light. The On/Off value is
stored in RAM and reported over Zigbee; it does not drive a GPIO.

The endpoint exposes the Basic, Identify, Groups, Scenes, and On/Off server
clusters. Groups, scenes, On, Off, and Toggle commands are handled so that the
device has the standard shape expected by a Hue Bridge while continuing to
route Zigbee traffic at the network layer. It was successfully commissioned
and interviewed by an official Philips Hue Bridge v2 on 2026-09-04.

## What had to change

The normal Koenkk router remains TI GenericApp device `0x00FF`. Changing only
its Basic attributes does not make it a light, and Hue cannot interview it as
one. `hue_on_off_light.patch` makes the following application changes:

- HA profile `0x0104`, On/Off Light device ID `0x0100`, device version `1`;
- endpoint 1 servers for Basic `0x0000`, Identify `0x0003`, Groups `0x0004`,
  Scenes `0x0005`, and On/Off `0x0006`;
- a RAM-backed OnOff attribute plus Off, On, Toggle, Groups, and Scenes
  handling;
- attribute reporting while preserving the `zr_genericapp` router build.

There is also a security difference. Association with Hue succeeds using the
normal Zigbee MAC procedure, but Hue encrypts its initial APS Transport Key
with the ZLL pre-installed trust-center link key. With only TI's default
`ZigBeeAlliance09`, Z-Stack alternates between `NWK_JOINING` and
`UNAUTHENTICATED` before reporting `NO_NETWORK`.

The workflow reads the Hue key from the `HUE_TCLK_HEX` repository secret,
verifies its published SHA-256 fingerprint, and supplies it through TI's
`zstack_UseAPSKeyWithFallback` commissioning mode. The standard
`ZigBeeAlliance09` trust-center key remains available as the fallback. The Hue
key itself is deliberately not stored in the public repository.

The successful transition is:

```text
NWK_DISC -> NWK_JOINING -> DEV_ROUTER -> BDB SUCCESS
```

After `DEV_ROUTER`, Hue sends its cluster interview and the device forwards
Zigbee traffic as a normal mains-powered router.

## Downloads

The [GitHub Releases page](https://github.com/5andr0/Z-Stack-firmware/releases)
contains two Intel HEX images:

- `sonoff_zbdongle_p_hue_on_off_light_router_production.hex` — normal firmware
  with no application USB serial logging;
- `sonoff_zbdongle_p_hue_on_off_light_router_debug.hex` — identical Zigbee
  functionality plus readable USB commissioning and ZCL diagnostics.

Both are for the Sonoff ZBDongle-P/CC2652P, preserve the Sonoff serial
bootloader backdoor on DIO15, and can be flashed with the
[Sonoff Dongle Flasher](https://dongle.sonoff.tech/sonoff-dongle-flasher/).

## Build

Run the **Build Sonoff Hue router firmware** GitHub Actions workflow. Its build
matrix produces separate `production` and `debug` artifacts.

The workflow uses SimpleLink SDK 8.30.01.01, CCS 12.8.1, TI Arm Clang 4.0.2
LTS, and the `CC1352P_2_LAUNCHXL` router project. It validates every Intel HEX
checksum and the Sonoff bootloader-backdoor configuration word before upload.

Forks must configure a repository secret named `HUE_TCLK_HEX` containing the
16-byte ZLL commissioning trust-center key. The build verifies the canonical
colon-separated, uppercase representation (with a trailing newline) against
this SHA-256 fingerprint before compiling:

```text
ce574642a3a8959b344796591321a155ae3bd25e4f5668602f6a33c06adbdf33
```

Local builds select a variant with `HUE_ROUTER_VARIANT=production` or
`HUE_ROUTER_VARIANT=debug`.

## Pair and reset

Flash either Intel HEX image with the Sonoff Dongle Flasher. Release BOOT and
power-cycle the dongle normally. Start a light search on the Hue Bridge and
then reset the dongle. GenericApp starts network steering automatically. The
debug variant additionally retries a failed scan every ten seconds, making it
easier to observe commissioning without precise timing.

If the dongle belonged to another Zigbee network, use its button-driven factory
reset or erase it before retrying. The serial bootloader remains enabled with
the active-low backdoor on DIO 15, matching the Sonoff ZBDongle-P.

## Live diagnostics

In the debug image, the CP2102 USB serial connection carries plain-text
diagnostics at 115200 baud, 8 data bits, no parity, and one stop bit. On Linux,
close the flasher and any service holding the serial port, then run:

```sh
ls -l /dev/serial/by-id/
picocom -b 115200 /dev/ttyUSB0
```

Start a Hue light search, then reset the dongle. The log reports every network
scan, BDB commissioning result, Trust Center exchange, device-state change,
joined PAN/channel, incoming application frame, and On/Off command. `NO_NETWORK`
means no joinable network was found; `TCLK_EX_FAILURE` means joining reached the
security exchange but failed; `JOINED` followed by `AF RX` means the bridge is
communicating with the light endpoint.

The visible red LED on this dongle is a fixed power LED. The only GPIO LED in
the published pin map is DIO7 and is not populated, so it cannot provide useful
blink diagnostics without a hardware modification.

## Compatibility with non-Hue coordinators

This is not locked to a Hue PAN, channel, bridge address, or network key. For a
fresh centralized join it tries the Hue/ZLL commissioning TCLK and uses TI's
fallback to the normal global `ZigBeeAlliance09` key. Distributed-network
support from GenericApp is unchanged. It should therefore still join standard
ZHA, Zigbee2MQTT, and other Zigbee 3 coordinators, where it will appear as an
On/Off Light rather than `ti.router`.

The Hue join has been hardware-tested. The fallback path is provided by TI
Z-Stack and compiled into both images, but it has not been tested against every
coordinator implementation. Factory-reset the dongle before moving it between
Zigbee networks.

## References

- [TI Z-Stack network-steering procedure](https://software-dl.ti.com/simplelink/esd/simplelink_cc13xx_cc26xx_sdk/7.10.01.24/exports/docs/zigbee/html/zigbee/z-stack-overview.html#network-steering-procedure-for-a-node-not-on-a-network)
- [Hue classical commissioning and the ZLL trust-center key](https://peeveeone.com/2016/11/breakout-breakthrough/)
- [Independent Hue light implementation: TCLK and device-version findings](https://wejn.org/2025/01/zigbee-hue-llo-world/)
- [Official Hue Zigbee 3.0 interoperability statement](https://developers.meethue.com/zigbee-3-0-support-in-hue-ecosystem/)
