import asyncio, websockets, json; asyncio.run((lambda: websockets.connect("ws://150.136.94.139:8765/collaborate/test/cursor").__aenter__()).__await__().__next__().send(json.dumps({"type": "ping"})))
