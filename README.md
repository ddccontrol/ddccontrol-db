[![Build Status][travis-badge]][travis]

[travis-badge]: https://travis-ci.org/ddccontrol/ddccontrol-db.svg?branch=master
[travis]: https://travis-ci.org/ddccontrol/ddccontrol-db

# DDC/CI control database

Project `ddccontrol-db` contains database of monitor descriptors, which are used by  `ddccontrol` and `gddccontrol` utilities to control monitor parameters using DDC/CI protocol. [MONITORS.md](MONITORS.md) contains a list of displays currently in the database.

* [Installation](#installation)
    * [Installation from official packages](#installation-from-official-packages)
    * [Installation from sources](#installation-from-sources)
* [Usage](#usage)
    * [From GUI using gddccontrol](#from-gui-using-gddccontrol)
    * [From command line using ddccontrol](#from-command-line-using-ddccontrol)
* [License](#license)

## Installation

The most convenient way to install `ddccontrol-db` is to use packages from official distribution repositories.

Manual installation is more complicated, but contains latest monitor profiles.

### Installation from official packages

On Ubuntu based distrubtions `ddccontrol-db`, along with utilities, can be installed using `apt`:

```shell
sudo apt install ddccontrol ddccontrol-db gddccontrol
```

Instructions for other distributions will be prepared later.

### Installation from sources

Install build depedencies (on Ubuntu):

```shell
sudo apt install intltool
```

Instructions for dependecies installation will be prepared later.

Latest repository can be cloned and built by:

```shell
git clone https://github.com/ddccontrol/ddccontrol-db.git
cd ddccontrol-db
./autogen.sh 
./configure --prefix=/usr/
make
```

Finally, the build can be installed using:

```shell
sudo make install
```

## Usage

Monitor database is used indirectly with `ddccontrol` and `gddccontrol` utilities.

### From GUI using gddccontrol

`gddccontrol` is a graphical utility for monitor configuration. It is called **Monitor Settings** in list of applications.

Currently, root privileges are required to control monitor parameters, therefore the launcher automatically asks for a password.

Utility can launched directly from commandline:

```shell
sudo gddccontrol
```

### From command line using ddccontrol

`ddccontrol` allows monitor configuration directly from commandline. To probe I2C devices to find monitor buses use:

```shell
sudo ddccontrol -p
```

To read value of control `0x10` (brightness on VESA compliant monitors) for device `dev:/dev/i2c-4`:

```shell
sudo ddccontrol -r 0x10 dev:/dev/i2c-4
```

To set value of control `0x10` (brightness on VESA compliant monitors) to `75` for device `dev:/dev/i2c-4`:

```shell
sudo ddccontrol -r 0x10 -w 75 dev:/dev/i2c-4
```

See `ddccontrol -h` for more information.

## License

The project is licensed under `GNU General Public License v2.0` license. See [COPYING](COPYING) for details.
