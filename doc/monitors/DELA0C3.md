# Dell P2416D: DELA0C2 (VGA), DELA0C3 (HDMI)

EDID readings:
	Plug and Play ID: DELA0C2 [VESA standard monitor]
	Input type: Digital

EDID readings:
	Plug and Play ID: DELA0C3 [VESA standard monitor]
	Input type: Digital

## Capabilities
Note `type(LCD)` in upper case that is not recognized by the ddccontrol parser.

`mccs_ver(2.1)` may define a more specific control set than just "VESA standard monitor"

DELA0C2 (VGA):
```
Raw output: (prot(monitor)type(LCD)model(P2416D)cmds(01 02 03 07 0C E3 F3)vcp(02 04 05 06 08 0E 10 12 14(05 08 0B 0C) 16 18 1A 1E 20 30 3E 52 60(01 11 0F) AA(01 02) AC AE B2 B6 C6 C8 C9 D6(01 04 05) DC(00 02 03 05) DF E0 E1 E2(00 01 02 04 0E 12 14 19) F0(00 08) F1(01 02) F2 FD)mswhql(1)asset_eep(40)mccs_ver(2.1))
Parsed output: 
	VCP: 02 04 05 06 08 0e 10 12 14 16 18 1a 1e 20 30 3e 52 60 aa ac ae b2 b6 c6 c8 c9 d6 dc df e0 e1 e2 f0 f1 f2 fd 
	Type: Unknown
```

DELA0C3 (HDMI):
```
Raw output: (prot(monitor)type(LCD)model(P2416D)cmds(01 02 03 07 0C E3 F3)vcp(02 04 05 08 10 12 14(05 08 0B 0C) 16 18 1A 52 60(01 11 0F) AA(01 02) AC AE B2 B6 C6 C8 C9 D6(01 04 05) DC(00 02 03 05) DF E0 E1 E2(00 01 02 04 0E 12 14 19) F0(00 08) F1(01 02) F2 FD)mswhql(1)asset_eep(40)mccs_ver(2.1))
Parsed output: 
	VCP: 02 04 05 08 10 12 14 16 18 1a 52 60 aa ac ae b2 b6 c6 c8 c9 d6 dc df e0 e1 e2 f0 f1 f2 fd 
	Type: Unknown
```

Wrapped and aligned variant:
```
DELA0C2 (VGA):
(prot(monitor)type(LCD)model(P2416D)
cmds(01 02 03 07 0C E3 F3)
vcp(02 04 05 06 08 0E 10 12 14(05 08 0B 0C) 16 18 1A 1E 20 30 3E 52 60(01    11 0F   )
    AA(01 02) AC AE B2 B6 C6 C8 C9 D6(01 04 05) DC(00 02 03 05) DF
    E0 E1 E2(00 01 02 04    0E 12 14 19)    F0(00    08) F1(01 02) F2 FD)
mswhql(1)asset_eep(40)mccs_ver(2.1))

DELA0C3 (HDMI):
(prot(monitor)type(LCD)model(P2416D)
cmds(01 02 03 07 0C E3 F3)
vcp(02 04 05    08    10 12 14(05 08 0B 0C) 16 18 1A             52 60(01    11 0F   )
    AA(01 02) AC AE B2 B6 C6 C8 C9 D6(01 04 05) DC(00 02 03 05) DF
    E0 E1 E2(00 01 02 04    0E 12 14 19)    F0(00    08) F1(01 02) F2 FD)
mswhql(1)asset_eep(40)mccs_ver(2.1))
```

So VGA interface has a bit more controls.

## Controls
### Legend
* RW value may be set and new value may be read
* W monitor executes the command in response to write of 1, following read
  reports 0
* R attempts to write another value do not change register value.
  The value may be changed using OSD menu.
* Empty - have not tried to write something due to unclear consequences,
  or due to the register is likely read-only such as VCP version.

Last column contains description found in DB entries for other monitors or
in [ddcutil](http://www.ddcutil.com/) docs and [sources](https://github.com/rockowitz/ddcutil/).
Degree of uncertainty is expressed by question marks.

| Addr | DELA0C3 (HDMI)                            | DELA0C2 (VGA)                             |    | Description or Comment              |
| ---- | ----------------------------------------- | ----------------------------------------- | -- | ----------------------------------- |
| 0x02 | +/1/2 C [???]                             | +/2/2 C [???]                             | RW | New Control Value                   |
| 0x04 | +/0/1 C [Restore Factory Defaults]        | +/0/1 C [Restore Factory Defaults]        | W  |                                     |
| 0x05 | +/0/1 C [Restore Brightness and Contrast] | +/0/1 C [Restore Brightness and Contrast] | W  |                                     |
| 0x06 | +/0/1   [???]                             | +/0/1 C [Restore Factory Default Geometry]| W  |                                     |
| 0x08 | +/0/1 C [Restore Factory Default Color]   | +/0/1 C [Restore Factory Default Color]   | W  |                                     |
| 0x0b | +/100/0   [???]                           | +/100/0   [???]                           |    | Color Temperature Increment ???     |
| 0x0e | +/62865/100   [???]                       | +/52/100 C [Image Lock Coarse (Clock)]    |    |                                     |
| 0x10 | +/25/100 C [Brightness]                   | +/75/100 C [Brightness]                   | RW |                                     |
| 0x12 | +/60/100 C [Contrast]                     | +/75/100 C [Contrast]                     | RW |                                     |
| 0x14 | +/5/12 C [???]                            | +/5/12 C [???]                            | RW | Color Preset                        |
| 0x16 | +/100/100 C [Red maximum level]           | +/100/100 C [Red maximum level]           | RW |                                     |
| 0x18 | +/100/100 C [Green maximum level]         | +/100/100 C [Green maximum level]         | RW |                                     |
| 0x1a | +/100/100 C [Blue maximum level]          | +/100/100 C [Blue maximum level]          | RW |                                     |
| 0x1e | +/0/1   [???]                             | +/0/1 C [Automatically adjust]            | W  |                                     |
| 0x1f | +/1/1   [???]                             | +/1/1   [???]                             |    | Auto Color (always 1) ???           |
| 0x20 | +/221/100   [???]                         | +/49/100 C [Horizontal Position]          | RW |                                     |
| 0x30 | +/21/100   [???]                          | +/51/100 C [Vertical Position]            | RW |                                     |
| 0x3e | +/68/100   [???]                          | +/92/100 C [Image Lock Fine (Clock Phase)]| RW |                                     |
| 0x52 | +/0/255 C [???]                           | +/14/255 C [???]                          | R  | Active Control                      |
| 0x60 | +/17/18 C [Input Source Select]           | +/1/18 C [Input Source Select - Analog]   | RW |                                     |
| 0x6c | +/17/18   [???]                           | +/1/18   [???]                            |    | ???                                 |
| 0x6e | +/17/18   [???]                           | +/1/18   [???]                            |    | ???                                 |
| 0x70 | +/17/18   [???]                           | +/1/18   [???]                            |    | ???                                 |
| 0xaa | +/1/255 C [OSD Orientation - Landscape]   | +/1/255 C [OSD Orientation - Landscape]   | R  |                                     |
| 0xac | +/23564/1 C [???]                         | +/5464/1 C [???]                          |    | Horizontal Sync Frequency ?         |
| 0xae | +/6010/65535 C [???]                      | +/5990/65535 C [???]                      |    | Vertical Sync Frequency (x100 Hz) ? |
| 0xb2 | +/1/1 C [???]                             | +/1/1 C [???]                             |    | Subpixel Layout - RGB ?             |
| 0xb6 | +/3/5 C [???]                             | +/3/5 C [???]                             |    | Display Technology Type - LCD Active Matrix ? |
| 0xc0 | +/958/65535   [???]                       | +/1005/65535   [???]                      |    | Power-on Hours                      |
| 0xc6 | +/17868/65535 C [???]                     | +/17868/65535 C [???]                     |    | Application Enable Key ?            |
| 0xc8 | +/4361/17 C [???]                         | +/4361/17 C [???]                         |    | Display Controller Type ?           |
| 0xc9 | +/257/65535 C [???]                       | +/257/65535 C [???]                       |    | Display Firmware Level ?            |
| 0xca | +/1/2   [???]                             | +/1/2   [???]                             | R  | OSD                                 |
| 0xcc | +/2/11   [???]                            | +/2/11   [???]                            | R  | Language - English                  |
| 0xd6 | +/1/5 C [DPMS Control - On]               | +/1/5 C [DPMS Control - On]               | RW |                                     |
| 0xdc | +/0/5 C [???]                             | +/0/5 C [???]                             | RW | Magic Bright                        |
| 0xdf | +/513/65535 C [???]                       | +/513/65535 C [???]                       |    | VCP Version - 02.01                 |
| 0xe0 | +/0/1 C [???]                             | +/0/1 C [???]                             |    | constant value     ???              |
| 0xe1 | +/0/1 C [Power control - Off]             | +/0/1 C [Power control - Off]             | RW |                                     |
| 0xe2 | +/0/25 C [???]                            | +/0/25 C [???]                            | R  | Something related to Preset Mode ?  |
| 0xf0 | +/0/255 C [???]                           | +/0/255 C [???]                           | RW | Paper preset mode if 0x08           |
| 0xf1 | +/3/255 C [???]                           | +/3/255 C [???]                           |    | constant value     ???              |
| 0xf2 | +/0/255 C [???]                           | +/0/255 C [???]                           | R  | Dynamic Contrast - Off              |
| 0xfd | +/98/255 C [???]                          | +/98/255 C [???]                          |    | constant value     ???              |

## Preset modes
Similar to [DELA0BE](DELA0BE.md) except absence of 0x0c

### Read-write registers 0x14, 0xdc, 0xf0
"Address: value" pairs to set the mode

* Standard `0x14: 0x05` or `0xdc: 0x00`
* Multimedia `0xdc: 0x02`
* Movie `0xdc: 0x03`
* Game `0xdc: 0x05`
* Paper `0xf0: 0x08` (opposite `0xf0: 0x00` has no effect)
* Cool `0x14: 0x08`
* Warm `0x14: 0x0b`
* User `0x14: 0x0c`

0x14 register may have other values: 0, 1, 2, 4, or even 29. E.g. if movie or game preset mode is selected
then hue is changed using OSD or dynamic contrast is turned off. No reaction on attempts to set similar values.

### 0xe2 Read-only register
* 0 Standard
* 1 Multimedia
* 2 Movie
* 4 Game
* 14 Warm
* 18 Cool
* 20 Custom
* 25 Paper

### 0xf2 Dynamic contrast read-only register
Through OSD available for movie and game presets. Can not be changed using DDC controls.

## Input source 0x60
Monitor has autoselect menu item, have no idea how it can be selected.
Read results in currently active input chosen explicitly or implicitly.

* 1 VGA
* 15 Display Port
* 17 HDMI

Through VGA cable read attempts fails just after switching.

## OSD Language (0xcc, read-only)
* 0x02 English
* 0x03 French
* 0x04 German

May be vendor or model specific

* 0x06 Portuguese (Brazil)
* 0x0a Spanish

Above reported range of 11

* 0x0c Japanese
* 0x90 Russian
* 0xe0 Chinese

## DPMS 0xd6
State 0x05 "Power Off" can not be changed directly to 0x04 "Standby"

## OSD only controls
Similar to [DELA0BE](DELA0BE.md) except "MST" is absent but there are some other options.

## Misc
Read error are reported quite often, most of the times retries succeed.

0x6c 0x6e 0x70 that might mean Red, Green, Blue Black Level.
While probing reading gives the same value as input source.
Single reads results in strange values
```
Reading 0x70...
Control 0x70: +/30309/10613   [???]
```
or
```
Control 0x70: +/10588/12585   [???]
```

Read after the following commands gives error: restore factory defaults, geometry, auto adjust, standby.
Maybe auto adjust takes more time than default delay.

