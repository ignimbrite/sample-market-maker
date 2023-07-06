import argparse
import asyncio
import logging
import time
import settings
from woo_x import Client


class MarketMaker:
    def __init__(self, client):
        self.client = client
        self.symbol = settings.symbol
        self.mid_price = None
        self.offset_bps = settings.offset_bps
        self.refresh_time_ms = settings.refresh_time_ms
        self.step_bps = settings.step_bps
        self.grid_size = settings.grid_size
        self.base_size = settings.base_size
        self.size_step = settings.size_step
        self.price_updated = asyncio.Event()
        self.logger = logging.getLogger('MarketMaker')

    async def update_best_prices(self):
        async for slam in self.client.slams([self.symbol]):
            if 'mid_price' in slam:
                self.mid_price = slam['mid_price']
            self.price_updated.set()

    async def handle_single_order(self, side, i):
        size = self.base_size + (i * self.size_step)
        step_bps_size = (self.mid_price * self.step_bps) / 1e4
        offset = (self.offset_bps / 1e4) * self.mid_price
        price = self.mid_price - offset if side == 'bids' else self.mid_price + offset
        price = price + (i * step_bps_size) if side == 'asks' else price - (
                i * step_bps_size)
        price = round(price, 2)
        size = round(size, 8)
        if price:
            response = await self.client.place_order(self.symbol, side, price, size)
            symbol_parts = self.symbol.split('_')
            formatted_response = "Placed order for {:.2f} {} @ {:.2f}".format(size, symbol_parts[1], price)
            self.logger.info(formatted_response)
            time.sleep(0.3)  # Delay to avoid rate limit

    async def place_order(self, side):
        await self.price_updated.wait()
        if self.mid_price is not None:
            for i in range(self.grid_size):
                await self.handle_single_order(side, i)
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
            await self.place_order('bids')
            await self.place_order('asks')
            self.logger.info(f"Orders placed, sleeping for {self.refresh_time_ms / 1e3} seconds.")
            position = await self.client.position(self.symbol)
            self.logger.info(f"Current position for {self.symbol}: {position}")
            await asyncio.sleep(self.refresh_time_ms / 1e3)

    async def run(self):
        update_task = asyncio.create_task(self.update_best_prices())
        handle_orders_task = asyncio.create_task(self.handle_orders())
        await asyncio.gather(update_task, handle_orders_task)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    async with Client(
            api_public_key=settings.api_public_key,
            api_secret_key=settings.api_secret_key,
            application_id=settings.application_id,
            network=settings.network,
    ) as client:
        executor = MarketMaker(client)
        await executor.run()



if __name__ == '__main__':
    asyncio.run(main())
