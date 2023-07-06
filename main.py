import argparse
import asyncio
import logging
from woo_x import Client

class MarketMaker:
    def __init__(self, client, offset_bps, refresh_time_ms):
        self.client = client
        self.mid_price = None
        self.offset_bps = offset_bps
        self.refresh_time_ms = refresh_time_ms
        self.price_updated = asyncio.Event()

    async def update_best_prices(self, symbols):
        async for slam in self.client.slams(symbols):
            if 'mid_price' in slam:
                self.mid_price = slam['mid_price']
            self.price_updated.set()

    async def place_order(self, symbol, side, size):
        await self.price_updated.wait()
        if self.mid_price is not None:
            offset = self.mid_price * (self.offset_bps / 1e4)
            price = round(self.mid_price - offset if side == 'bids' else self.mid_price + offset, 2)
            if price:
                response = await self.client.place_order(symbol, side, price, size)
                print(response)

                position = await self.client.position(symbol)
                print(f"Current position for {symbol}: {position}")

    async def cancel_all_orders(self):
        response = await self.client.cancel_all_orders()
        print(response)

    async def handle_orders(self):
        while True:
            await self.cancel_all_orders()
            await self.place_order('PERP_BTC_USDT', 'bids', 0.01)
            await self.place_order('PERP_BTC_USDT', 'asks', 0.01)
            await asyncio.sleep(self.refresh_time_ms / 1e3)

    async def run(self):
        symbols = ['PERP_BTC_USDT']
        update_task = asyncio.create_task(self.update_best_prices(symbols))
        handle_orders_task = asyncio.create_task(self.handle_orders())
        await asyncio.gather(update_task, handle_orders_task)

async def main(offset_bps, refresh_time_ms):
    logging.basicConfig(
        level=logging.ERROR
    )

    async with Client(
        api_public_key='j8Y+6YCHDUwYYePMvq1eOg==',
        api_secret_key='ORSVONLEMB6IHCRKAG4N4HRWYXBU',
        application_id='194c85b6-8114-465c-829c-9fca81e40bf4',
        network='testnet',
    ) as client:
        executor = MarketMaker(client, offset_bps, refresh_time_ms)
        await executor.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Market Maker bot")
    parser.add_argument('--offset', type=float, help='Offset in basis points', required=True)
    parser.add_argument('--refresh_time', type=int, help='Refresh time in milliseconds', required=True)
    args = parser.parse_args()
    asyncio.run(main(args.offset, args.refresh_time))
