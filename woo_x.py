import asyncio

import aiostream.stream
import orjson
import websockets
import wootrade
import time
import logging
import aiohttp
from dataclasses import dataclass


@dataclass
class Client():
    ENDPOINTS = {
        'mainnet': {
            'HTTP': 'https://api.woo.org',
            'WS_PUBLIC': 'wss://wss.woo.org/ws/stream/{application_id}',
            'WS_PRIVATE': 'wss://wss.woo.org/v2/ws/private/stream/{application_id}',
        },
        'testnet': {
            'HTTP': 'https://api.staging.woo.org',
            'WS_PUBLIC': 'wss://wss.staging.woo.org/ws/stream/{application_id}',
            'WS_PRIVATE': 'wss://wss.staging.woo.org/v2/ws/private/stream/{application_id}',
        },
    }

    api_public_key: str
    api_secret_key: str
    application_id: str
    network: str

    def __post_init__(self):
        self.http_endpoint = self.ENDPOINTS[self.network]['HTTP']
        self.ws_public_endpoint = self.ENDPOINTS[self.network]['WS_PUBLIC'].format(application_id=self.application_id)
        self.ws_private_endpoint = self.ENDPOINTS[self.network]['WS_PRIVATE'].format(application_id=self.application_id)

        self._session = aiohttp.ClientSession(self.http_endpoint)

        self._subclient = wootrade.Client(
            self.api_public_key,
            self.api_secret_key,
            self.application_id,
            self.network == 'testnet'
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.close()

    async def symbols(self, normalized: bool = True):
        response = await self._session.get('/v1/public/info')

        content = await response.json()

        if not normalized:
            return content

        return [{
            'exchange': 'woo-x',
            'raw_name': entry['symbol'],
            'name': '/'.join(entry['symbol'].split('_')[1:]),
            'category': {'SPOT': 'spot', 'PERP': 'perpetuals'}[entry['symbol'].split('_')[0]]
        } for entry in content['rows']]

    async def place_order(self, symbol: str, side: str, price: float, size: float):
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: (
                self._subclient.send_order(
                    symbol=symbol,
                    order_type='LIMIT',
                    side={'bids': 'BUY', 'asks': 'SELL'}[side],
                    order_price=price,
                    order_quantity=size
                )
            )
        )

        return response

    async def cancel_all_orders(self):
        timestamp = str(int(time.time() * 1000))

        signature = wootrade.signature(timestamp, self.api_secret_key)

        response = await self._session.delete(
            "/v3/orders/pending",
            headers={
                'x-api-key': self.api_public_key,
                'x-api-signature': signature,
                'x-api-timestamp': timestamp
            }
        )

        content = await response.json()
        return content

    async def slams(self, symbols: [str], normalize: bool = True):
        async def stream(symbols):
            async for connection in websockets.connect(self.ws_public_endpoint):
                await asyncio.gather(*[
                    connection.send(orjson.dumps({
                        'event': 'subscribe',
                        'topic': f"{symbol}@bbo"
                    }).decode('utf-8'))
                    for symbol in symbols
                ])

                async def ping():
                    await connection.send(orjson.dumps({'event': 'ping'}).decode('utf-8'))

                async for raw_message in connection:
                    message = orjson.loads(raw_message)

                    if message.get('event') == 'ping': asyncio.ensure_future(ping())

                    yield message

        if normalize:
            async for message in stream(symbols):
                if 'data' not in message:
                    continue

                best_bid = float(message['data']['bid'])
                best_ask = float(message['data']['ask'])
                mid_price = (best_bid + best_ask) / 2

                yield {
                    'exchange': 'woo-x',
                    'symbol': message['data']['symbol'],
                    'channel': 'slams',
                    'orders': {
                        'bid': {
                            'price': best_bid,
                            'size': message['data']['bidSize']
                        },
                        'ask': {
                            'price': best_ask,
                            'size': message['data']['askSize']
                        }
                    },
                    'mid_price': mid_price
                }
        else:
            async for message in stream(symbols):
                yield message

    async def mark_price(self, symbol: str, normalize: bool = True):
        async def stream(symbol):
            async for connection in websockets.connect(self.ws_public_endpoint):
                await connection.send(orjson.dumps({
                    'id': 'foo',
                    'event': 'subscribe',
                    'topic': f"{symbol}@markprice"
                }).decode('utf-8'))

                async def ping(): await connection.send(orjson.dumps({'event': 'ping'}).decode('utf-8'))

                async for raw_message in connection:
                    message = orjson.loads(raw_message)

                    if message.get('event') == 'ping': asyncio.ensure_future(ping())

                    yield message

        if normalize:
            async for message in stream(symbol):
                if 'data' not in message:
                    continue

                yield {
                    'exchange': 'woo-x',
                    'symbol': f"{symbol}",
                    'channel': 'mark_price',
                    'price': message['data']['price']
                }
        else:
            async for message in stream(symbol):
                yield message

    async def position(self, symbol: str, normalized: bool = True):
        timestamp = str(int(time.time() * 1000))

        signature = wootrade.signature(timestamp, self.api_secret_key)

        response = await self._session.get(
            f"/v1/position/{symbol}",
            headers={
                'x-api-key': self.api_public_key,
                'x-api-signature': signature,
                'x-api-timestamp': timestamp
            }
        )

        content = await response.json()

        if normalized:
            if content == {'success': True}:
                return 0

            return float(content['holding'])
        else:
            return content

    async def fills(self):
        async for connection in websockets.connect(self.ws_private_endpoint):
            try:
                timestamp = str(int(time.time() * 1000))

                await connection.send(orjson.dumps({
                    'id': 'test',
                    'event': 'auth',
                    'params': {
                        'apikey': self.api_public_key,
                        'sign': wootrade.signature(timestamp, self.api_secret_key),
                        'timestamp': timestamp
                    }
                }).decode('utf-8'))

                await connection.send(orjson.dumps({
                    "id": "test",
                    "topic": "executionreport",
                    "event": "subscribe"
                }).decode('utf-8'))

                async def ping(): await connection.send(orjson.dumps({'event': 'ping'}).decode('utf-8'))

                async for raw_message in connection:
                    message = orjson.loads(raw_message)

                    if message.get('event') == 'ping': asyncio.ensure_future(ping())

                    yield message
            except Exception as exception:
                print(exception)

    async def balances(self, normalized: bool = True):
        timestamp = str(int(time.time() * 1000))

        signature = wootrade.signature(timestamp, self.api_secret_key)

        response = await self._session.get(
            f"/v1/client/holding",
            headers={
                'x-api-key': self.api_public_key,
                'x-api-signature': signature,
                'x-api-timestamp': timestamp
            }
        )

        content = await response.json()

        if normalized:
            return content['holding']
        else:
            return content



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
        response = await client.place_order('PERP_BTC_USDT', 'bids', 25000.0, 0.01)
        print(response)

        async for message in client.slams([symbol['raw_name'] for symbol in await client.symbols() if symbol['category'] == 'perpetuals']):
            print(message)



if __name__ == '__main__':
    asyncio.run(main())

