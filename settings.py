# The market symbol you want the bot to trade, e.g., "PERP_BTC_USDT", "SPOT_BTC_USDT", etc.
symbol = "PERP_BTC_USDT"

# The offset or spread for order placement from the mid-price in basis points (1 basis point = 0.01%)
offset_bps = 3

# The bot's refresh time in seconds, i.e., how often the bot should cancel and replace orders
refresh_time = 1

# The step size in basis points for order grid (the price difference between two consecutive orders in the grid)
step_bps = 10

# The number of bid and ask orders the bot should place on either side of the mid-price
grid_size = 3

# The size of the first order in the grid
base_size = 0.01

# The increment in size for each subsequent order in the grid
size_step = 0.02

# The interval for order placement in seconds. A shorter interval might result in rate limiting when using grid_size > 1
timeout = 0.3

# Your API public key from Woo X
api_public_key = 'your_api_public_key'

# Your API secret key from Woo X
api_secret_key = 'your_api_secret_key'

# Your application ID from Woo X
application_id = 'your_app_id'

# The network you want to connect to. Choose 'testnet' for testing or 'mainnet' for real trading
network = 'testnet'