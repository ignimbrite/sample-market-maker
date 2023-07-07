import argparse
import asyncio
import logging
import time
import random
import settings
import signal
from woo_x import Client

class MarketMaker:
    def __init__(self, client):
        self.client = client
        self.symbol = settings.symbol
        self.mid_price = None
        self.offset_bps = settings.offset_bps
        self.refresh_time = settings.refresh_time
        self.step_bps = settings.step_bps
        self.grid_size = settings.grid_size
        self.base_size = settings.base_size
        self.size_step = settings.size_step
        self.price_updated = asyncio.Event()
        self.timeout = settings.timeout
        self.logger = logging.getLogger('MarketMaker')
        self.cancelled = asyncio.Event()

    async def update_best_prices(self):
        async for slam in self.client.slams([self.symbol]):
            if 'mid_price' in slam:
                self.mid_price = slam['mid_price']
            self.price_updated.set()

    async def handle_single_order(self, side, price, size):
        if price:
            response = await self.client.place_order(self.symbol, side, price, size)
            symbol_parts = self.symbol.split('_')
            formatted_response = "Placed order for {:.4f} {} @ {:.2f}".format(size, symbol_parts[1], price)
            self.logger.info(formatted_response)
            time.sleep(self.timeout)  # Delay to avoid rate limit

    async def place_grid_order(self, side, i):
        size = self.base_size + (i * self.size_step)
        step_bps_size = (self.mid_price * self.step_bps) / 1e4
        offset = (self.offset_bps / 1e4) * self.mid_price
        price = self.mid_price - offset if side == 'bids' else self.mid_price + offset
        price = price + (i * step_bps_size) if side == 'asks' else price - (i * step_bps_size)
        price = round(price, 2)
        size = round(size, 8)
        await self.handle_single_order(side, price, size)

    async def place_fill_order(self, side, size):
        offset = (self.offset_bps / 1e4) * self.mid_price
        price = self.mid_price - offset if side == 'bids' else self.mid_price + offset
        price = round(price, 2)
        await self.handle_single_order(side, price, size)

    async def place_order(self, side):
        await self.price_updated.wait()
        if self.mid_price is not None:
            for i in range(self.grid_size):
                await self.place_grid_order(side, i)
            self.price_updated.set()

    async def cancel_all_orders(self):
        response = await self.client.cancel_all_orders()
        if response.get('success') and response.get('status') == 'CANCEL_ALL_SENT':
            self.logger.info("Canceling all existing orders.")
        else:
            self.logger.info(response)

    async def handle_orders(self):
        while not self.cancelled.is_set():
            await self.cancel_all_orders()
            await self.place_order('bids')
            await self.place_order('asks')
            self.logger.info(f"Orders placed, sleeping for {self.refresh_time} seconds.")
            position = await self.client.position(self.symbol)
            base_asset = self.symbol.split('_')[1]
            self.logger.info(f"Current position for {self.symbol}: {position} {base_asset}")
            await asyncio.sleep(self.refresh_time)

    async def monitor_fills(self):
        async for fill in self.client.fills():
            if 'data' in fill and fill['data']['status'] == 'FILLED':
                qty_filled = round(fill['data']['quantity'], 4)
                executed_price = round(fill['data']['executedPrice'], 2)
                symbol_parts = self.symbol.split('_')

                formatted_response = "Order filled for {:.4f} {} @ {:.2f}".format(qty_filled, symbol_parts[1],
                                                                                  executed_price)
                self.logger.info(formatted_response)

                position = await self.client.position(self.symbol)
                self.logger.info(f"Current position for {self.symbol}: {position}")

                side_filled = fill['data']['side']
                side = 'bids' if side_filled == 'BUY' else 'asks'
                await self.place_fill_order(side, qty_filled)

    async def cancel_and_exit(self):
        self.cancelled.set()
        self.logger.info('Cancelled all orders and exiting.')
        await self.cancel_all_orders()
        exit(0)

    def attach_exit_handler(self):
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, lambda: loop.create_task(self.cancel_and_exit()))
        loop.add_signal_handler(signal.SIGTERM, lambda: loop.create_task(self.cancel_and_exit()))

    async def run(self):
        self.attach_exit_handler()
        update_task = asyncio.create_task(self.update_best_prices())
        handle_orders_task = asyncio.create_task(self.handle_orders())
        monitor_fills_task = asyncio.create_task(self.monitor_fills())
        await asyncio.gather(update_task, handle_orders_task, monitor_fills_task)

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
