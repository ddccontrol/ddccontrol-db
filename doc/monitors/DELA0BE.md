# DELA0BE

EDID readings:
Plug and Play ID: DELA0BE [Dell P2415Q]
Input type: Digital

Tested on displays:

* Dell P2415Q (through mDP connection)

## Capabilities

```
Raw output: (prot(monitor)type(lcd)model(P2415Q)cmds(01 02 03 07 0C E3 F3)vcp(02 04 05 08 10 12 14(05 08 0B 0C) 16 18 1A 52 60( 11 0F 10) AA(01  02) AC AE B2 B6 C6 C8 C9 D6(01 04 05) DC(00 02 03 05 ) DF F0(00 08) FD E0 E1 E2(00 01 02 04 0E 12 14 19) E4 F1 F2)mccs_ver(2.1)mswhql(1))
Parsed output:
  VCP: 02 04 05 08 10 12 14 16 18 1a 52 60 aa ac ae b2 b6 c6 c8 c9 d6 dc df e0 e1 e2 e4 f0 f1 f2 fd
  Type: LCD
```

## Controls

* OK: Writing works
* Read Only: Writing doesn't change value
* Error: Monitor reacts, but value is not applied/persisted

| Control | valid/current/max | Write test | Description                                      |
| ------- | ----------------- | ---------- | ------------------------------------------------ |
| 0x02    | +/2/2             |            | Secondary Degauss                                |
| 0x04    | +/0/255           |            | Restore Factory Defaults                         |
| 0x05    | +/0/1             | OK         | Restore Brightness and Contrast                  |
| 0x06    | +/0/255           |            | ???                                              |
| 0x08    | +/0/255           |            | Restore Factory Default Color                    |
| 0x0b    | +/0/24028         |            | ???                                              |
| 0x0c    | +/1/255           | Error      | ??? (through color presets)                      |
| 0x0e    | +/50/100          |            | ???                                              |
| 0x10    | +/43/100          | OK         | Brightness                                       |
| 0x12    | +/75/100          | OK         | Contrast                                         |
| 0x14    | +/5/12            | OK         | Color Preset (through color presets)             |
| 0x16    | +/100/100         | OK         | Red maximum level                                |
| 0x18    | +/100/100         | OK         | Green maximum level                              |
| 0x1a    | +/100/100         | OK         | Blue maximum level                               |
| 0x1e    | +/0/2             |            | ???                                              |
| 0x20    | +/0/100           |            | ???                                              |
| 0x30    | +/0/100           |            | ???                                              |
| 0x3e    | +/50/100          |            | ???                                              |
| 0x52    | +/20/255          |            | ???                                              |
| 0x60    | +/16/14           | OK         | Input Source Select                              |
| 0x6c    | +/50/255          |            | ???                                              |
| 0x6e    | +/50/255          |            | ???                                              |
| 0x70    | +/50/255          |            | ???                                              |
| 0xa8    | +/0/3             |            | ???                                              |
| 0xaa    | +/1/255           | Read Only  | OSD Orientation                                  |
| 0xac    | +/2228/2          |            | ???                                              |
| 0xae    | +/5999/0          |            | ???                                              |
| 0xb2    | +/1/8             |            | ???                                              |
| 0xb4    | +/1/2             |            | ???                                              |
| 0xb6    | +/3/5             |            | ???                                              |
| 0xc0    | +/6/65535         |            | ???                                              |
| 0xc6    | +/17868/65535     |            | ???                                              |
| 0xc8    | +/22021/0         |            | ???                                              |
| 0xc9    | +/259/65535       |            | ???                                              |
| 0xca    | +/2/2             |            | ???                                              |
| 0xd6    | +/1/255           | OK         | DPMS Control - On (1 = on, 4 = standby, 5 = off) |
| 0xdc    | +/0/255           | OK         | Magic Bright Mode (through color presets)        |
| 0xdf    | +/513/255         |            | ???                                              |
| 0xe0    | +/0/1             |            | ???                                              |
| 0xe1    | +/0/1             |            | Power control                                    |
| 0xe2    | +/0/255           | Read Only  | ??? (through color presets)                      |
| 0xe3    | +/0/1             |            | ???                                              |
| 0xe4    | +/0/1             | OK         | Color Uniformity                                 |
| 0xf0    | +/0/255           | OK + Error | ??? (through color presets) (writing 8 works, 0 doesn't) |
| 0xf1    | +/3/1             |            | ???                                              |
| 0xf2    | +/0/1             | Read Only  | Dynamic Contrast (certain color presets only)    |
| 0xfa    | +/0/65535         |            | ???                                              |
| 0xfd    | +/98/65535        |            | ???                                              |
| 0xff    | +/0/65535         |            | ???                                              |

## Regarding Color Presets

The monitor allows to select a couple of color presets through the OSD which change multiple settings at once:

| Control | Description         | Standard | Movie | Multimedia | Game | Paper | Warm | Cool | Custom |
| ------- | ------------------- | -------- | ----- | ---------- | ---- | ----- | ---- | ---- | ------ |
| 0x0c    | ???                 | 1        | 2     | 2          | 2    | 2     | 2    | 2    | 2      |
| 0x14    | Color Preset        | 5        | 5     | 5          | 5    | 5     | 11   | 8    | 12     |
| 0xdc    | "Magic Bright Mode" | 0        | 0     | 2          | 5    | 0     | 0    | 0    | 0      |
| 0xe2    | ???                 | 0        | 2     | 1          | 4    | 25    | 14   | 18   | 20     |
| 0xf0    | ???                 | 0        | 0     | 0          | 0    | 8     | 0    | 0    | 0      |
| 0xf2    | Dynamic Contrast    | 0        | 1     | 0          | 1    | 0     | 0    | 0    | 0      |

## OSD only controls

The following settings can be controlled through the OSD, but do not change any readable parameter:

* Personalize
    * Shortcut Key 1 (map functions to physical buttons)
    * Shortcut Key 2 (map functions to physical buttons)
* Color
    * Input color format (RGB / YPbPr)
    * Hue (0 - 100) (only visible when e.g. in movie preset mode)
    * Saturation (0 - 100) (only visible when e.g. in movie preset mode)
* Display
    * Aspect Ratio (Wide 16:9 / 4:3 / 1:1 / Auto Resize)
    * Sharpness (0 - 100)
    * Response Time (fast / normal)
    * MST (Off / Primary / Secondary)
* Energy
    * Power Button LED (off during active / on during active)
* Menu
    * Language

