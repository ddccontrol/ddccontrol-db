# DDC/CI control database

Project `ddccontrol-db` contains database of monitor descriptors, which are used by  `ddccontrol` and `gddccontrol` utilities to control monitor parameters using DDC/CI protocol.

* [Installation](#installation)
    * [Installation from official packages](#installation-from-official-packages)
    * [Installation from sources](#installation-from-sources)
* [Usage](#usage)
    * [From GUI - Monitor Settings (`gddccontrol`)](#from-gui---monitor-settings-gddccontrol)
    * [From command line - `ddccontrol`](#from-command-line---ddccontrol)
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
automake
./configure --prefix=/usr/
make
```

Finally, the build can be installed using:

```shell
sudo make install
```

## Usage

Monitor database is used indirectly with `ddccontrol` and `gddccontrol` utilities.

### From GUI - Monitor Settings (`gddccontrol`)

Currently, root privileges are required to control monitor parameters, therefore the menu entry called `Monitor Settings` automatically asks for password.

Utility can launched directly from commandline:

```shell
sudo gddccontrol
```

### From command line - `ddccontrol`

To be documented...

## License

The project is licensed under `GNU General Public License v2.0` license. See [COPYING](COPYING) for details.
