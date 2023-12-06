from uagents import Context, Agent, Model
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import json

alice = Agent(name="Rishi", seed="alice recovery phrase")

app = FastAPI()


class EmptyMessage(Model):
    message: str


class ConnectionManager:
    def __init__(self):
        self.active_connection = None
        self.active_connection: WebSocket

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connection = websocket

    def disconnect(self, websocket: WebSocket):
        self.active_connection = None

    async def send_agent_message(self, message):
        global should_ask_for_exchange_rates
        if self.active_connection is not None:
            await self.active_connection.send_json(message)
            should_ask_for_exchange_rates = False


manager = ConnectionManager()

should_ask_for_exchange_rates = False
should_update_monitors = False


# To monitor the exchange rates
@alice.on_interval(period=1.0)
async def monitor_exchange_rates(ctx: Context):
    if not should_ask_for_exchange_rates:
        return await manager.send_agent_message({
            # "data" : some_data_variable
            "event": "check_exchange"
        })
    else:
        # TODO: call the api function to get the data and then send it out.
        # TODO: Sending alerts for comparisons will also be a part of this.
        pass


# To monitor update the monitors
@alice.on_interval(period=1.0)
async def update_monitors(ctx: Context):
    if not should_update_monitors:
        return
    else:
        # TODO: call the api function to set the data and then send it out.
        pass


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global should_ask_for_exchange_rates
    global should_update_monitors
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive()
            if data['type'] == "websocket.disconnect":
                raise WebSocketDisconnect
            event = json.loads(data['text'])['event']
            if event == "check_exchange":
                should_ask_for_exchange_rates = True
                print(f"before sending: {should_ask_for_exchange_rates}")
                await manager.send_agent_message({
                    # TODO: Change the response to the actual data.
                    "should_check": should_ask_for_exchange_rates
                })
                print(f"after sending: {should_ask_for_exchange_rates}")
            elif event == "update_monitors":
                should_update_monitors = True
                await manager.send_agent_message({
                    # TODO: Change the response to the actual data.
                    "should_update": should_update_monitors
                })
            else:
                pass

    except WebSocketDisconnect:
        print("client diconnected.")


if __name__ == "__main__":
    uvicorn.run(port=8000, app=app)
