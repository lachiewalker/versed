# versed

[![PyPI - Version](https://img.shields.io/pypi/v/versed.svg)](https://pypi.org/project/versed)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/versed.svg)](https://pypi.org/project/versed)

-----

Versed is a document chat app with Google Drive integration.

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [License](#license)

## Quick Start

Install using **pipx**:

```console
pipx install versed
```

Run `versed` in your terminal:

```console
versed
```

From the API key selection screen choose `"Add a New Key"` and add fill in the required fields to add a valid OpenAI API key.

- **Optional** - Select the `"Google Drive"` tab in the left pane and complete the log in flow to enable indexing files from your Google Drive.

Choose a file from the file view pane and index it by clicking `"Add to Index"`... and ask away!

## Installation

Versed requires Python3.9 or newer to run.
Versed is best run using `pipx`, which will manage a virtual environment for all dependencies for you, to avoid collisions with other software.

### Requirements

- **Python** - A version of python3 should come pre-installed on Linux and Mac. If you are on Windows and only need Python for Versed, installing from the Microsoft Store is the easiest way to go.
- **pipx** - Pipx manages virtual enviroments for each installed app, helping to avoid dependency collisions. Follow the instructions below or visit [pipx's installation guide](https://pipx.pypa.io/stable/installation/) for instructions.
- **OpenAI API key** - A desktop account for ChatGPT is not the same as an API key. To create an API key for OpenAI you will need to [create an account](https://platform.openai.com) and then [create an API key](https://platform.openai.com/api-keys) once logged in.

### Linux (Debian / Ubuntu)

Install `pipx`:

```console
sudo apt update
sudo apt install pipx
```

After installation **pipx** will prompt you to run `pipx ensurepath`. Doing so will add **pipx** to your system's path, enabling **pipx** to be run from anywhere

Now `versed` can be installed using `pipx` as follows:

```console
pipx install versed
```

### Windows

To install **pipx** using pip, run the following command.

```console
# If you installed python using Microsoft Store, replace `py` with `python3` in the next line.
py -m pip install --user pipx
```

Now `versed` can be installed using **pipx** as follows:

```console
pipx install versed
```

## Getting Started

## License

`versed` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
