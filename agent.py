from uagents import Context, Agent, Model
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import json
import freecurrencyapi

alice = Agent(name="Rishi", seed="alice recovery phrase")

app = FastAPI()

API_KEY='fca_live_X2sxe8aAg55RJgBo1yvUG5jGKEf0rQbrdXWjzsWZ'
client = freecurrencyapi.Client(api_key=API_KEY)

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
should_update_threshold = False

# To monitor the exchange rates
@alice.on_interval(period=10.0)
async def monitor_exchange_rates(ctx: Context):

    # code to send the monitor data
    monitor_base = ctx.storage.get('monitor_base') 
    monitor_target = ctx.storage.get('monitor_target')

    if monitor_base and monitor_target:
        result = client.latest(base_currency=monitor_base, currencies=monitor_target)
        data = result['data']
        await manager.send_agent_message({
            "data" : data,
            "event": "check_exchange"
        })
    else:
        # TODO: call the api function to get the data and then send it out.
        # TODO: Sending alerts for comparisons will also be a part of this.
        pass

    # code to send alerts incase of threshold breach
    try: # nested in try block to prevent typecasting errors
        threshold_base = ctx.storage.get('threshold_base')
        base_value = float(ctx.storage.get('threshold_base_value'))
        threshold_target = ctx.storage.get('threshold_target')
        target_value = float(ctx.storage.get('threshold_target_value'))
        operation = ctx.storage.get('operation')

        if threshold_base and base_value and threshold_target and target_value and operation:

            result = client.latest(base_currency=threshold_base, currencies=[threshold_target])
            current_value = float(result['data'][threshold_target])
            send_alert = False
            alert_data = {
                    "operation":operation,
                    "current_value":current_value,
                    "threshold_value":target_value
                }
            if operation=='-1' and (base_value*current_value)<target_value:
                # minimum threshold reached
                send_alert = True
            elif operation=='0' and (base_value*current_value)==target_value:
                #equal threshold reached
                send_alert = True
            elif operation=='1' and (base_value*current_value)>target_value:
                #maximum threshold reached
                send_alert = True

            if send_alert:
                await manager.send_agent_message({
                    "data":alert_data,
                    "event":"threshold_alert"
                })
        else:
            pass
    except:
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
