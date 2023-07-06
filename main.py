import argparse
import asyncio
import logging
import time
from woo_x import Client


class MarketMaker:
    def __init__(self, client, symbol, offset_bps, refresh_time_ms, step, grid_size):
        self.client = client
        self.symbol = symbol
        self.mid_price = None
        self.offset_bps = offset_bps
        self.refresh_time_ms = refresh_time_ms
        self.step = step
        self.grid_size = grid_size
        self.price_updated = asyncio.Event()
        self.logger = logging.getLogger('MarketMaker')

    async def update_best_prices(self):
        async for slam in self.client.slams([self.symbol]):
            if 'mid_price' in slam:
                self.mid_price = slam['mid_price']
            self.price_updated.set()

    async def handle_single_order(self, side, size, i):
        offset = (self.mid_price + i * self.step) * (self.offset_bps / 1e4)
        price = round(self.mid_price - offset if side == 'bids' else self.mid_price + offset, 2)
        if price:
            response = await self.client.place_order(self.symbol, side, price, size)
            symbol_parts = self.symbol.split('_')
            formatted_response = "Placed order for {:.2f} {} @ {:.2f}".format(size, symbol_parts[1], price)
            self.logger.info(formatted_response)
            time.sleep(0.3)  # Delay to avoid rate limit

    async def place_order(self, side, size):
        await self.price_updated.wait()
        if self.mid_price is not None:
            for i in range(self.grid_size):
                await self.handle_single_order(side, size, i)
            self.price_updated.set()

    async def cancel_all_orders(self):
        response = await self.client.cancel_all_orders()
        if response.get('success') and response.get('status') == 'CANCEL_ALL_SENT':
            self.logger.info("Cancelling all existing orders.")
        else:
            self.logger.info(response)

    async def handle_orders(self):
        while True:
            await self.cancel_all_orders()
            await self.place_order('bids', 0.01)
            await self.place_order('asks', 0.01)
            self.logger.info(f"Orders placed, sleeping for {self.refresh_time_ms / 1e3} seconds.")
            position = await self.client.position(self.symbol)
            self.logger.info(f"Current position for {self.symbol}: {position}")
            await asyncio.sleep(self.refresh_time_ms / 1e3)

    async def run(self):
        update_task = asyncio.create_task(self.update_best_prices())
        handle_orders_task = asyncio.create_task(self.handle_orders())
        await asyncio.gather(update_task, handle_orders_task)


async def main(symbol, offset_bps, refresh_time_ms, step, grid_size):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    async with Client(
            api_public_key='j8Y+6YCHDUwYYePMvq1eOg==',
            api_secret_key='ORSVONLEMB6IHCRKAG4N4HRWYXBU',
            application_id='194c85b6-8114-465c-829c-9fca81e40bf4',
            network='testnet',
    ) as client:
        executor = MarketMaker(client, symbol, offset_bps, refresh_time_ms, step, grid_size)
        await executor.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Market Maker bot")
    parser.add_argument('--symbol', type=str, help='Symbol to operate on', required=True)
    parser.add_argument('--offset', type=float, help='Offset in basis points', required=True)
    parser.add_argument('--refresh_time', type=int, help='Refresh time in milliseconds', required=True)
    parser.add_argument('--step', type=float, help='Step size for grid orders', required=True)
    parser.add_argument('--grid_size', type=int, help='Number of grid orders', required=True)
    args = parser.parse_args()
    asyncio.run(main(args.symbol, args.offset, args.refresh_time, args.step, args.grid_size))
