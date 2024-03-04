# Jump Plotter

A user application which displays data

## Table of Contents

- [Just Plotter](#just-plotter)
  - [Table of Contents](#table-of-contents)
  - [About the Project](#about-the-project)
    - [Built With](#built-with)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
  - [Usage](#usage)
  - [Contributing](#contributing)
  - [License](#license)
  - [Contact](#contact)

## About the Project

A user-application to view project data

### Built With

- [Python](https://www.python.org/)
- [Matplotlib](https://matplotlib.org/)

## Getting Started

To get started with this project, follow these steps:

### Prerequisites

- Install python-3.11

### Installation

#### Install Python 3.11 as required. Two options:

1. (Recommended) Install with pyenv.
If you don't have this version available, it may be installed with pyenv.
pyenv is a tool for managing multiple versions of Python on the same system.

```sh
cd $HOME
curl https://pyenv.run | bash
pyenv install 3.11.0
```

2. Install from Python.org. Python 3.11.0+ is required and can be downloaded from [https://www.python.org/downloads/](https://www.python.org/downloads/)

#### Clone the repository
   ```sh
   git clone git@github.com:4d30/just_plotter.git
   ```

#### Install dependencies
   ```sh
   cd just_plotter
   pyenv local 3.11.0
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage

Edit the config file `config.ini`. Set *rto* to the path of RTO/ on your system 
```sh
gedit config.ini
```
Run
```sh
python main.py
```

## Notes

Some things to think about:

1. Do you see visual indications of synchronization? 

2. Are all of the sensors recording during the event window?

3. Are any of the sensor signals doing something interesting or out of the
   ordinary?

4. Are events happening at the same time?

5. Is the gap between events occuring on a human time scale?

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the project
2. Create your feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a pull request

