import asyncio
import logging
from woo_x import Client

class MarketMaker:
    def __init__(self, client, offset):
        self.client = client
        self.best_bid = None
        self.best_ask = None
        self.offset = offset
        self.price_updated = asyncio.Event()

    async def update_best_prices(self, symbols):
        async for slam in self.client.slams(symbols):
            if 'orders' in slam and 'bid' in slam['orders'] and 'price' in slam['orders']['bid']:
                self.best_bid = slam['orders']['bid']['price']
            if 'orders' in slam and 'ask' in slam['orders'] and 'price' in slam['orders']['ask']:
                self.best_ask = slam['orders']['ask']['price']
            self.price_updated.set()

    async def place_order(self, symbol, side, size):
        await self.price_updated.wait()
        if self.best_bid is not None and self.best_ask is not None:
            mid_price = (self.best_bid + self.best_ask) / 2
            price = mid_price - self.offset if side == 'bids' else mid_price + self.offset
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
            await asyncio.sleep(3)

    async def run(self):
        symbols = ['PERP_BTC_USDT']
        update_task = asyncio.create_task(self.update_best_prices(symbols))
        handle_orders_task = asyncio.create_task(self.handle_orders())
        await asyncio.gather(update_task, handle_orders_task)

async def main():
    logging.basicConfig(
        level=logging.ERROR
    )

    async with Client(
        api_public_key='j8Y+6YCHDUwYYePMvq1eOg==',
        api_secret_key='ORSVONLEMB6IHCRKAG4N4HRWYXBU',
        application_id='194c85b6-8114-465c-829c-9fca81e40bf4',
        network='testnet',
    ) as client:
        offset = 300
        executor = MarketMaker(client, offset)
        await executor.run()

if __name__ == '__main__':
    asyncio.run(main())