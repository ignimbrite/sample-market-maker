# Woo X Market Maker Sample
A simple [Woo X](https://referral.woo.org/K5kBYJR7aFcQSU2c7) Market Making Bot for handling and managing orders.

## Requirements
- Python 3.7 or newer
- An account with Woo X with API keys available

## Installation
It's recommended to use a virtual environment (venv) for running this project to isolate the dependencies.

Clone this repository and navigate into the project directory, then install the necessary libraries:

```bash
git clone https://github.com/mattmgls/woo-maker.git
cd woo-maker
pip install -r requirements.txt
```

## Usage
To use the bot, simply run the main script:

```bash
python main.py
```

Parameters like offset, refresh time, base size, size step, grid size, grid step, API keys, and network are configured in the settings.py file.
## Configuration
Configuration parameters are found in settings.py.

Modify the parameters as per your requirements:
```python
symbol = "PERP_BTC_USDT"
offset_bps = 100
refresh_time = 30000
step_bps = 100
grid_size = 5
base_size = 0.01
size_step = 0.01

api_public_key = 'your_api_public_key'
api_secret_key = 'your_api_secret_key'
application_id = 'your_application_id'
network = 'testnet'
```

Remember to replace 'your_api_public_key', 'your_api_secret_key', and 'your_application_id' with your actual API public key, API secret key, and application ID from Woo X. For the network setting, choose 'testnet' for testing or 'mainnet' for real trading.