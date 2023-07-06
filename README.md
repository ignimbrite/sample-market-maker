# Woo-Maker
A simple A simple [WooX](https://referral.woo.org/K5kBYJR7aFcQSU2c7) Market Making Bot for handling and managing orders.

## Requirements
- Python 3.7 or newer
- An account with WooX with API keys available

## Installation
It's recommended to use a virtual environment (venv) for running this project to isolate the dependencies. 

Clone this repository and navigate into the project directory, then install the necessary libraries:

```bash
git clone https://github.com/username/woo-maker.git
cd woo-maker
pip install -r requirements.txt
```
Replace 'username' with your actual GitHub username.

## Usage
To use the bot, you need to provide it with the offset and refresh time parameters as command line arguments when running the script. Offset is provided in basis points and refresh time in milliseconds.

Run the bot with the following command:

```bash
python main.py --offset [offset_bps] --refresh [refresh_time_ms]

```
For example, to run the bot with an offset of 3 basis points and a refresh time of 5000 milliseconds (or 5 seconds), you would use:

```bash
python main.py --offset 3 --refresh 5000
```
## Configuration
You need to provide the bot with your API keys. Open the main.py file and replace the placeholders in the following lines with your actual API public key, API secret key, and application ID:

```python
api_public_key=''
api_secret_key=''
application_id=''
```
