EDID readings:
Plug and Play ID: PHL08DC [VESA standard monitor]
Input type: Digital

Capabilities:
```
Raw output: (prot(monitor)type(LCD)model(221P6QPYE)cmds(01 02 03 07 0C E3 F3)vcp(02 04 05 08 0B 0C 10 12 14(01 04 05 06 07 08 0A 0B) 16 18 1A 52 54(00 01) 60(01 03 0F) 62 6C 6E 70 72(05 78 FB 50 64 78 8C A0) 86(02 08) 8D(01 02) AA(01 02) AC AE B2 B6 C0 C6 C8 C8 CA(01 02) CC(01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 12 14 16 17 1A 1E 24) D6(01 04 05) DC(00 01 02 03 05 08) DF E9(00 02) EB(00 01 02 03) F0(00 01) F2(00 01 02 03 04) FA(00 01 02) FB FC FD FE(00 01 02 04))mswhql(1)asset_eep(40)mccs_ver(2.2))
Parsed output:
VCP: 02 04 05 08 0b 0c 10 12 14 16 18 1a 52 54 60 62 6c 6e 70 72 86 8d aa ac ae b2 b6 c0 c6 c8 ca cc d6 dc df e9 eb f0 f2 fa fb fc fd fe
Type: Unknown
```

Write test results:

* OK: write using ddccontrol works flawlessly
* OK, IRC: write using ddccontrol works, but receives **I**nvalid **R**esponse on **C**hange
* OK, RIR: write using ddccontrol works, but receives **R**andomly **I**nvalid **R**esponse
* BAD, R: works bad, **R**andomly sets value

GUI test:

* OK: works fine
* N/P: not present

| Control | valid/current/max | CAPS | Write test | GUI test | Description - Value name]                |
| ------- | ----------------- | ---- | ---------- | -------- | ---------------------------------------- |
| 0x02    | +/1/2 C           |      | TODO       |          | ???                                      |
| 0x04    | +/0/1 C           |      | OK         | OK       | Restore Factory Defaults                 |
| 0x05    | +/0/1 C           |      | OK         | OK       | Restore Brightness and Contrast          |
| 0x06    | +/0/1             |      | TODO       |          | ???                                      |
| 0x08    | +/0/1 C           |      | OK         | OK       | Restore Factory Default Color            |
| 0x0b    | +/50/50 C         |      | TODO       |          | ???                                      |
| 0x0c    | +/70/255 C        |      | TODO       |          | ???                                      |
| 0x0e    | +/8606/100        |      | TODO       |          | ???                                      |
| 0x10    | +/59/100 C        | VCP  | OK         | OK       | Brightness (0 - 100)                     |
| 0x12    | +/47/100 C        | VCP  | OK         | OK       | Contrast (0 - 100)                       |
| 0x14    | +/11/11 C         | VCP  | OK         | OK       | Color preset (01-sRGB, 04-5000K, 05-6500K, 06-7500K, 07-8200K, 08-N/A, 0A-11500K, 0B-User Defined) |
| 0x16    | +/100/100 C       | VCP  | OK         | OK       | Red maximum level (0 - 100)              |
| 0x18    | +/93/100 C        | VCP  | OK         | OK       | Green maximum level (0 - 100)            |
| 0x1a    | +/98/100 C        | VCP  | OK         | OK       | Blue maximum level (0 - 100)             |
| 0x1e    | +/0/1             |      | TODO       |          | ???                                      |
| 0x1f    | +/1/1             |      | TODO       |          | ???                                      |
| 0x20    | +/50/100          | N/A  | OK         | OK       | Shifts screen horizontally (0 - 100; 50 = center, probably in pixels) |
| 0x30    | +/50/100          | N/A  | OK         | OK       | Shifts screen vertically (0 - 100;50 = center, probably in pixels) |
| 0x3e    | +/24/100          |      | TODO       |          | ???                                      |
| 0x52    | +/0/255 C         |      | TODO       |          | ???                                      |
| 0x54    | +/1/1 C           | VCP  | OK         |          | X - Pixel Orbiting (00 01)               |
| 0x60    | +/15/3 C          | VCP  | OK, IRC    | OK       | Input Source Select (01 - D-SUB, 03 - DVI, 0F - DisplayPort) |
| 0x62    | +/80/100 C        | VCP  | OK, RIR    | OK       | Audio Speaker Volume Adjust (0 - 100)    |
| 0x6c    | +/50/100 C        | VCP  | OK         | OK       | Red minimum level (0 - 100)              |
| 0x6e    | +/50/100 C        | VCP  | OK         | OK       | Green minimum level (0 - 100)            |
| 0x70    | +/50/100 C        | VCP  | OK         | OK       | Blue minimum level (0 - 100)             |
| 0x72    | +/120/160 C       |      | TODO       |          | ???                                      |
| 0x86    | +/8/8 C           | VCP  | BAD, R     |          | Picture Format (08 = Wide Screen, 02 = 4:3) |
| 0x87    | +/3/4             |      | TODO       |          | ???                                      |
| 0x8d    | +/2/2 C           |      | TODO       |          | ???                                      |
| 0xaa    | +/1/4 C           | VCP  | N/A        |          | OSD Orientation - Landscape - ??? (01 02) |
| 0xac    | +/2880/1 C        |      | TODO       |          | ???                                      |
| 0xae    | +/5990/65535 C    |      | TODO       |          | ???                                      |
| 0xb2    | +/1/1 C           |      | TODO       |          | ???                                      |
| 0xb6    | +/3/5 C           |      | TODO       |          | ???                                      |
| 0xc0    | +/173/65535 C     |      | TODO       |          | ???                                      |
| 0xc6    | +/111/255 C       |      | TODO       |          | ???                                      |
| 0xc8    | +/9/0 C           |      | TODO       |          | ???                                      |
| 0xc9    | +/514/65535       |      | TODO       |          | ???                                      |
| 0xca    | +/2/2 C           | VCP  | N/A        |          | ??? - (01 02)                            |
| 0xcc    | +/2/36 C          | VCP  | TODO       |          | ???                                      |
| 0xd6    | +/1/5 C           | VCP  | TODO       |          | DPMS Control - On - ??? (01 04 05)       |
| 0xdc    | +/0/8 C           |      | TODO       |          | ???                                      |
| 0xdf    | +/514/65535 C     |      | TODO       |          | ???                                      |
| 0xe9    | +/2/2 C           |      | TODO       |          | ???                                      |
| 0xeb    | +/0/1 C           | VCP  | TODO       |          | ??? - (00 01 02 03)                      |
| 0xf0    | +/0/1 C           | VCP  | OK         |          | SmartContrast (0 = off, 1 = on)          |
| 0xf2    | +/1/4 C           | VCP  | OK         | OK       | Power LED (0 = off; 1,2,3,4 = levels)    |
| 0xf9    | +/0/4             | N/A  | OK         |          | PowerSensor                              |
| 0xfa    | +/0/255 C         | VCP  | N/A        |          | ??? - (00 01 02)                         |
| 0xfb    | +/5/60 C          |      | TODO       |          | ???                                      |
| 0xfc    | +/0/65535 C       |      | TODO       |          | ???                                      |
| 0xfd    | +/0/65535 C       |      | TODO       |          | ???                                      |
| 0xfe    | +/0/255 C         | VCP  | N/A        |          | ??? - (00 01 02 04)                      |
