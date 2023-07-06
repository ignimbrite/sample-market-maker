woo-maker
A simple WooX Market Making Bot for handling and managing cryptocurrency orders. This bot helps place bid and ask orders on the basis of pre-defined offset and refresh intervals.

Requirements
Python 3.7 or newer
An account with WooX with API keys available
Installation
Clone this repository and navigate into the project directory, then install the necessary libraries:

bash
Copy code
git clone https://github.com/username/woo-maker.git
cd woo-maker
pip install -r requirements.txt
Replace username with your actual GitHub username.

Usage
To use the bot, you need to provide it with the offset and refresh time parameters as command line arguments when running the script. Offset is provided in basis points and refresh time in milliseconds.

Run the bot with the following command:

css
Copy code
python main.py --offset [offset_bps] --refresh [refresh_time_ms]
For example, to run the bot with an offset of 3 basis points and a refresh time of 5000 milliseconds (or 5 seconds), you would use:

css
Copy code
python main.py --offset 3 --refresh 5000
Configuration
You need to provide the bot with your API keys. Open the main.py file and replace the placeholders in the following lines with your actual API public key, API secret key, and application ID:

python
Copy code
api_public_key='',
api_secret_key='',
application_id='',
Be sure to keep your API keys secure and don't share them with anyone.

