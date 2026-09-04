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
`sonoff-zbdongle-p-hue-router` artifact contains:

`sonoff_zbdongle_p_hue_on_off_light_router.hex`

The workflow uses SimpleLink SDK 8.30.01.01, CCS 12.8.1, TI Arm Clang 4.0.2
LTS, and the `CC1352P_2_LAUNCHXL` router project. It validates every Intel HEX
checksum and the Sonoff bootloader-backdoor configuration word before upload.

## Pair and reset

Flash the Intel HEX image with the Sonoff Dongle Flasher. Start a light search
on the Hue Bridge, then power-cycle or reset the dongle. GenericApp starts
network steering automatically when it is not already commissioned.

If the dongle belonged to another Zigbee network, use its button-driven factory
reset or erase it before retrying. The serial bootloader remains enabled with
the active-low backdoor on DIO 15, matching the Sonoff ZBDongle-P.
