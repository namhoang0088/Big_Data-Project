import json
import websocket
from confluent_kafka import Producer
import time

# Danh sách các đồng coin
symbols = ['BTC', 'ETH', 'XRP', 'BCH', 'LTC', 'ADA', 'DOT', 'BNB', 'LINK', 'XLM']

# Định nghĩa các topic trong Kafka

# URL của WebSocket API để lấy dữ liệu giá của các đồng coin
websocket_url = "wss://stream.binance.com:9443/stream?streams=" + '/'.join([f"{symbol.lower()}usdt@trade" for symbol in symbols])

# Tạo producer cho Kafka
producer = Producer({'bootstrap.servers': 'localhost:9092'})

# Hàm gửi dữ liệu lên Kafka
def send_to_kafka(symbol, price):
    producer.produce(topic=symbol, value=json.dumps({"symbol": symbol, "price": price}))
    producer.flush()

# Hàm xử lý sự kiện khi nhận được dữ liệu từ WebSocket
def on_message(ws, message):
    data = json.loads(message)
    symbol = data['data']['s']
    symbol = symbol.replace("USDT", "")
    price = data['data']['p']
    print("symbol:", symbol, "price:", price)
    send_to_kafka(symbol, price)

# Hàm xử lý sự kiện khi mất kết nối đến WebSocket
def on_error(ws, error):
    print(error)

# Hàm xử lý sự kiện khi kết nối WebSocket thành công
def on_open(ws):
    print("Connected to WebSocket")

# Kết nối đến WebSocket API và xác định các hàm xử lý sự kiện
ws = websocket.WebSocketApp(websocket_url, on_message=on_message, on_error=on_error, on_open=on_open)

# Khởi chạy WebSocket mỗi 20 giây
while True:
    ws.run_forever()
    time.sleep(20)
