# Sonoff ZBDongle-P Hue On/Off Light router

This target keeps TI GenericApp's Zigbee Router (`zr`) network role and changes
its application endpoint to a virtual ZHA On/Off Light. The On/Off value is
stored in RAM and reported over Zigbee; it does not drive a GPIO.

The endpoint exposes the Basic, Identify, Groups, Scenes, and On/Off server
clusters. Groups, scenes, On, Off, and Toggle commands are handled so that the
device has the standard shape expected by a Hue Bridge while continuing to
route Zigbee traffic at the network layer.

## Build

Run the **Build Sonoff Hue router firmware** GitHub Actions workflow. Its
`sonoff-zbdongle-p-hue-router-debug` artifact contains:

`sonoff_zbdongle_p_hue_on_off_light_router_debug.hex`

The workflow uses SimpleLink SDK 8.30.01.01, CCS 12.8.1, TI Arm Clang 4.0.2
LTS, and the `CC1352P_2_LAUNCHXL` router project. It validates every Intel HEX
checksum and the Sonoff bootloader-backdoor configuration word before upload.

## Pair and reset

Flash the Intel HEX image with the Sonoff Dongle Flasher. Start a light search
on the Hue Bridge, then power-cycle or reset the dongle. GenericApp starts
network steering automatically, and this diagnostic build retries a failed scan
every ten seconds.

If the dongle belonged to another Zigbee network, use its button-driven factory
reset or erase it before retrying. The serial bootloader remains enabled with
the active-low backdoor on DIO 15, matching the Sonoff ZBDongle-P.

## Live diagnostics

The CP2102 USB serial connection carries plain-text diagnostics at 115200 baud,
8 data bits, no parity, and one stop bit. On Linux, close the flasher and any
service holding the serial port, then run:

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
