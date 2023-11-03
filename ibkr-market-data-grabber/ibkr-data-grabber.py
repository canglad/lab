# Copyright 2023 canglad.com

# This code is released for demo purpose, under MIT license https://opensource.org/license/mit/

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from ibapi.client import EClient
from ibapi.common import TickerId, TickAttrib
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.ticktype import *

import threading
import time

from datetime import datetime, timezone

DEBUG = False
DATA_DIR = "/home/dev/data"


class Stock:
    def __init__(self, name, exchange, currency):
        self.tick = name
        self.exchange = exchange
        self.currency = currency
        self.current_bid = 0.0
        self.current_ask = 0.0
        self.current_last = 0.0
        self.times = []
        self.bids = []
        self.asks = []
        self.lasts = []
        my_time = datetime.fromtimestamp(int(time.time()))
        self.data_file = open(f"{DATA_DIR}/{self.currency}-{self.tick}/{self.tick}-{my_time.year}-{my_time.month:02d}-{my_time.day:02d}.csv", "a")


class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    def currentTime(self, server_time: int):
        super().currentTime(server_time)
        local_time = int(time.time())
        if abs(local_time - server_time > 1):
            print(f"ERROR: gap between TWS/IBKR Server's current time and the local computer current time is bigger \
than 1 second. TWS/IBKR time: {server_time}    local computer time: {local_time}")
            quit()

    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float,
                  attrib: TickAttrib):
        super().tickPrice(reqId, tickType, price, attrib)
        my_stock = stocks[reqId]

        if DEBUG:
            print("DEBUG: TickPrice. TickerId:", reqId, "Tick:", my_stock.tick, "tickType:", tickType,
                  "tickTypeString:", TickTypeEnum.to_str(tickType),
                  "Price:", price, "CanAutoExecute:", attrib.canAutoExecute,
                  "PastLimit:", attrib.pastLimit, end=' ')
        if DEBUG:
            if tickType == TickTypeEnum.BID or tickType == TickTypeEnum.ASK:
                print("PreOpen:", attrib.preOpen)
            else:
                print()

        local_time = int(time.time())
        my_time = datetime.fromtimestamp(local_time)

        # avoid recording stock data before market open hours
        if (my_time.hour <= 8) or (my_time.hour == 9 and my_time.minute < 30):
            return

        # avoid recording stock data after market hours
        if (my_time.hour >= 16):
            print("market closed. quit")
            quit()

        my_stock.data_file.write(f"{local_time},{tickType},{price}\n")
        my_stock.data_file.flush()


stocks = [
    Stock("QQQ", "SMART", "USD"),
    Stock("SPY", "SMART", "USD"),
    Stock("NVDA", "SMART", "USD"),
    Stock("AAPL", "SMART", "USD"),
    Stock("MSFT", "SMART", "USD"),
]


def run_loop():
    app.run()


def check_off_hours():
  local_time = int(time.time())
  my_time = datetime.fromtimestamp(local_time)
  if my_time.hour <= 8 or my_time.hour >= 16:
    quit() 
  

# check local timezone. this program is designed for US Eastern Timezone only. you must set the local machine to
# that timezone
def assure_local_timezone():
    local_tz = datetime.now(timezone.utc).astimezone().tzinfo
    tz = local_tz.tzname(datetime.now())
    if tz != "EST" and tz != "EDT" and tz != "Eastern Standard Time" and tz != "Eastern Daylight Time":
        print(f"ERROR: local timezone must be defined to US Eastern Time, EST or EDT. Current tz is {tz}")
        quit()


assure_local_timezone()

app = IBapi()
app.connect('127.0.0.1', 4002, 1)

# Start the socket in a thread
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()

time.sleep(1)  # Sleep interval to allow time for connection to server

app.reqCurrentTime()

for i in range(0, len(stocks)):
    contract = Contract()
    contract.symbol = stocks[i].tick
    contract.secType = 'STK'
    contract.exchange = stocks[i].exchange
    contract.currency = stocks[i].currency
    app.reqMktData(i, contract, "", False, False, [])
