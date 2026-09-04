# 20260904 (Hue-compatible Sonoff ZBDongle-P target)

- Present GenericApp as an HA On/Off Light while retaining the router role
- Add Basic, Identify, Groups, Scenes, and On/Off server support
- Use the Hue/ZLL commissioning trust-center key with the standard global key
  as fallback
- Set the Simple Descriptor application device version to 1
- Add separate production and USB-debug GitHub Actions builds

# 20250403

- Updated SimpleLink SDK to 8.30.01.01

# 20221102

- Allow to set transmit power
- Fix directly connected Xiaomi devices disconnecting
- SimpleLink SDK 6.30.00.84 ([changelog](https://software-dl.ti.com/simplelink/esd/simplelink_cc13xx_cc26xx_sdk/6.30.00.84/exports/changelog.html))

# 20220125

- SimpleLink SDK 5.30.01.01 ([changelog](https://software-dl.ti.com/simplelink/esd/simplelink_cc13xx_cc26xx_sdk/5.30.01.01/exports/changelog.html))
- Increase memory heap
- Increase transmit power of CC1352P/CC2652P from 5dBm to 9dBm
- Support routing table command

# 20210128

- Initial router firmwares
