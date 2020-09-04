# How to add a monitor

This document is intended as a hands-on introduction on how to add a monitor to the database.

1. [Install DDC Control](#install-ddc-control)
1. [Clone and install `ddccontrol-db`](#clone-and-install-ddccontrol-db)
1. [Make a change](#make-a-change)
    1. [Verify the change using `ddccontrol`](#verify-the-change-using-ddccontrol)
    1. [Verify the change using the GUI](#verify-the-change-using-the-gui)
1. [Identify your monitor's I2C bus](#identify-your-monitors-i2c-bus)
1. [Identify your monitor](#identify-your-monitor)
1. [Add your monitor to the database](#add-your-monitor-to-the-database)
1. [Add a capabilities string](#add-a-capabilities-string)
1. [Add controls](#add-controls)
    1. [Query monitor capabilities](#query-monitor-capabilities)
    1. [Add a control](#add-a-control)
    1. [Try out the change](#try-out-the-change)
1. [Debugging](#debugging)
    1. [Troubleshooting checklist](#troubleshooting-checklist)
    1. [Capabilities string syntax](#capabilities-string-syntax)

## Install DDC Control

Install DDC Control according to [its installation instructions](https://github.com/ddccontrol/ddccontrol#installation).
You don't need to compile it, so using a pre-built package is fine.
Example:

```console
sudo apt install ddccontrol gddccontrol ddccontrol-db i2c-tools
```

## Clone and install `ddccontrol-db`

Clone, build and install `ddccontrol-db` according to the [_Installation from sources_](../README.md#installation-from-sources) section in the readme.

## Make a change

This section describes how to make changes and have them take effect.
**You need to perform these steps every time you've made a change to the database.**

If your monitor is not yet in the database, DDC Control uses the _VESA standard monitor_ profile (described in `db/monitor/VESA.xml`).
Modifying its name is probably the easiest way to verify that changes are applied correctly:

```diff
--- a/db/monitor/VESA.xml
+++ b/db/monitor/VESA.xml
@@ -1,16 +1,16 @@
 <?xml version="1.0"?>
 <!--- "Standard" controls -->
-<monitor name="VESA standard monitor" init="standard">
+<monitor name="Cool unknown monitor" init="standard">
        <controls>
                <control id="degauss" address="0x00"/>
                <control id="secdegauss" address="0x02"/>
```

Once you've made the change, install the database:

```console
sudo make install
```

### Verify the change using `ddccontrol`

When you've installed the modified database, do a probe for monitors:

```console
$ sudo ddccontrol -p
[...]
Detected monitors :
 - Device: dev:/dev/i2c-5
   DDC/CI supported: Yes
   Monitor Name: Cool unknown monitor
   Input type: Digital
  (Automatically selected)
[...]
```

You should see _Cool unknown monitor_ somewhere in the output.

### Verify the change using the GUI

Launch the DDC Control GUI from your application launcher or from the command line:

```console
sudo gddccontrol
```

Click the **blue arrow button at the top** to probe for monitors.
You should now be able to select _Cool unknown monitor_ in the _Current monitor_ dropdown.

## Identify your monitor's I2C bus

Knowing which **I2C bus** your monitor is using will simplify development.
The output of `sudo ddccontrol -p` (shown above) reveals that, in this case, the monitor is on the `i2c-5` bus.

## Identify your monitor

To add a monitor to the database, you need to know its [**Plug and Play ID**](https://uefi.org/PNP_ACPI_Registry).
It consists of a 3- or 4-character vendor ID and a 4-character hexadecimal product ID, e.g. `ACR06B1`.
To find it, query the capabilities of your monitor and look for these lines:

```console
$ sudo ddccontrol -c dev:/dev/i2c-5
[...]
EDID readings:
	Plug and Play ID: ACR06B1 [VESA standard monitor]
	Input type: Digital
[...]
```

In this case, the ID is indeed `ACR06B1`.

## Add your monitor to the database

Add your monitor by creating the file `db/monitor/<PLUG_AND_PLAY_ID>.xml`, for example:

```console
touch db/monitor/ACR06B1.xml
```

The file content below is a good starting point:

```xml
<?xml version="1.0"?>
<monitor name="Acer Nitro XV273K" init="standard">
	<include file="VESA"/>
</monitor>
```

Apply the changes:

```console
sudo make install
```

DDC Control should now recognize your monitor:

```console
$ sudo ddccontrol -p
[...]
Detected monitors :
 - Device: dev:/dev/i2c-5
   DDC/CI supported: Yes
   Monitor Name: Acer Nitro XV273K
   Input type: Digital
  (Automatically selected)
[...]
```

## Add a capabilities string

The **capabilities string** helps DDC Control understand what the monitor supports.
Acquire it like this:

```console
$ sudo ddccontrol -c dev:/dev/i2c-5
[...]
Capabilities:
Raw output: (prot(monitor)type(lcd)model(XV273K)cmds(01 02 03 07 0C E3 F3)vcp(02 04 05 08 0B 0C 10 12 14(05 06 08 0B 0C) 16 18 1A 52 54(00 01) 59 5A 5B 5C 5D 5E 60(03 11 0F 10) 62 9B 9C 9D 9E 9F A0 AC AE B6 C0 C6 C8 C9 CC(01 02 03 04 05 06 08 09 0A 0C 0D 0E 14 16 1E)D6(01 04 05) DF E3 E5 E6 E7(00 01 02) E8(00 01 02) )mswhql(1)asset_eep(32)mccs_ver(2.1))
Parsed output:
        VCP: 02 04 05 08 0b 0c 10 12 14 16 18 1a 52 54 59 5a 5b 5c 5d 5e 60 62 9b 9c 9d 9e 9f a0 ac ae b6 c0 c6 c8 c9 cc d6 df e3 e5 e6 e7 e8
        Type: LCD
```

The _Raw output_ value is the capabilities string.
Add it to your database entry:

```diff
--- a/db/monitor/ACR06B1.xml
+++ b/db/monitor/ACR06B1.xml
@@ -1,4 +1,5 @@
 <?xml version="1.0"?>
 <monitor name="Acer Nitro XV273K" init="standard">
+       <caps add="(prot(monitor)type(lcd)model(XV273K)cmds(01 02 03 07 0C E3 F3)vcp(02 04 05 08 0B 0C 10 12 14(05 06 08 0B 0C) 16 18 1A 52 54(00 01) 59 5A 5B 5C 5D 5E 60(03 11 0F 10) 62 9B 9C 9D 9E 9F A0 AC AE B6 C0 C6 C8 C9 CC(01 02 03 04 05 06 08 09 0A 0C 0D 0E 14 16 1E)D6(01 04 05) DF E3 E5 E6 E7(00 01 02) E8(00 01 02) )mswhql(1)asset_eep(32)mccs_ver(2.1))" />
        <include file="VESA"/>
 </monitor>
```

## Add controls

This is the tricky part.
Identifying which controls a monitor supports via DDC/CI and _how_ it supports them is a process of trial and error.
It's often helpful to take inspiration from other database entries, especially from the same vendor (`ACR` = Acer, `SAM` = Samsung, etc).

### Query monitor capabilities

DDC Control can help you figure out what controls you can add and how they should be defined:

```console
$ sudo ddccontrol -d dev:/dev/i2c-5
[...]
EDID readings:
        Plug and Play ID: ACR06B1 [Acer Nitro NV273K]
        Input type: Digital

Controls (valid/current/max) [Description - Value name]:
[...]
Control 0x10: +/91/100 C [Brightness]
Control 0x12: +/50/100 C [Contrast]
Control 0x14: +/5/11 C [???]
Control 0x16: +/50/100 C [Red maximum level]
Control 0x18: +/50/100 C [Green maximum level]
Control 0x1a: +/50/100 C [Blue maximum level]
[...]
```

### Add a control

The `<include file="VESA"/>` line includes a set of standard control definitions that may or may not work on your monitor.
You can override its definitions by adding your own ones before it, or remove it altogether.

The change below will remove the standard VESA definitions and add a single [MCCS](https://en.wikipedia.org/wiki/Monitor_Control_Command_Set)-compliant brightness control using address `0x10` (which the monitor does indeed support, according to the `ddccontrol -d` output above):

```diff
--- a/db/monitor/ACR06B1.xml
+++ b/db/monitor/ACR06B1.xml
@@ -1,5 +1,7 @@
 <?xml version="1.0"?>
 <monitor name="Acer Nitro XV273K" init="standard">
        <caps add="(prot(monitor)type(lcd)model(XV273K)cmds(01 02 03 07 0C E3 F3)vcp(02 04 05 08 0B 0C 10 12 14(05 06 08 0B 0C) 16 18 1A 52 54(00 01) 59 5A 5B 5C 5D 5E 60(03 11 0F 10) 62 9B 9C 9D 9E 9F A0 AC AE B6 C0 C6 C8 C9 CC(01 02 03 04 05 06 08 09 0A 0C 0D 0E 14 16 1E)D6(01 04 05) DF E3 E5 E6 E7(00 01 02) E8(00 01 02) )mswhql(1)asset_eep(32)mccs_ver(2.1))" />
-       <include file="VESA"/>
+       <controls>
+               <control id="brightness" address="0x10"/>
+       </controls>
 </monitor>
```

You should generally try to reuse code from `db/options.xml.in` (accomplished by `id="brightness"` in the example above).
You can add controls and/or values in `db/options.xml.in` if necessary.

### Try out the change

Apply the change as described in the [_Make a change_](#make-a-change) section.
The DDC Control GUI should now contain a single brightness control that you can use to control monitor brightness.
You can also use the command line:

```console
sudo ddccontrol dev:/dev/i2c-5 -r 0x10 -w 42
```

Note that even if a definition shows up in DDC Control, it may not be interpreted correctly by your monitor.
For example, _6-axis Hue_ colors may be ordered differently for different monitors.

## Debugging

Mistakes can be made in a database entry, for example XML syntax errors and non-parsable integer values.
Many of these are pointed out by `ddccontrol`, but the error messages can be somewhat hard to spot amidst other output, so make sure to look closely.
The verbosity flags (`-v`, `-vv`, ...) can be helpful.

### Troubleshooting checklist

* Run `sudo make install`.
* Re-probe for monitors in the DDC Control GUI.
* Check if controls are being discarded by the capabilities string:
  ```console
  $ ddccontrol -v -p dev:/dev/i2c-5
  [...]
  Control foobar has been discarded by the caps string.
  [...]
  ```
* Run `ddccontrol -vvv -p` and look for error messages.
* Try restarting the GUI.
* Make sure you haven't mixed up hexadecimal and decimal notation.
  Both are used in database entries.

### Capabilities string syntax

The raw capabilities string doesn't say a lot by itself, but it can sometimes aid in debugging.

The `vcp` part of the capabilities string contains the control addresses supported by the monitor, and sometimes the allowed values for a specific control.
Consider for example the following made-up capabilities string:

```text
[...]vcp(02 12 14(05 08 0B) 16 )[...]
```

This fictional monitor would support controls at addresses `0x02`, `0x12`, `0x14` and `0x16`, with the control at address `0x14` accepting values `0x05`, `0x08` and `0x0B`.
