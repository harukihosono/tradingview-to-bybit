# app.py
import time
import hashlib
import hmac
import json
from flask import Flask, request, jsonify
from typing import Dict, Any
import requests

app = Flask(__name__)

class BybitAPI:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api-testnet.bybit.com"
        # 固定の注文数量を設定
        self.fixed_qty = "0.001"  # BTCUSDTの最小注文数量

    def _get_signature(self, params: dict) -> tuple:
        timestamp = int(time.time() * 1000)
        param_str = str(timestamp) + self.api_key + "5000" + json.dumps(params)
        signature = hmac.new(
            bytes(self.api_secret, "utf-8"),
            bytes(param_str, "utf-8"),
            hashlib.sha256
        ).hexdigest()
        return timestamp, signature

    def _get_headers(self, timestamp: int, signature: str) -> Dict:
        return {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-SIGN-TYPE": "2",
            "X-BAPI-TIMESTAMP": str(timestamp),
            "X-BAPI-RECV-WINDOW": "5000",
            "Content-Type": "application/json"
        }

    def place_order(self, symbol: str, side: str, is_close: bool = False) -> Dict[str, Any]:
        endpoint = "/v5/order/create"
        
        params = {
            "category": "linear",
            "symbol": symbol,
            "side": side.capitalize(),
            "orderType": "Market",
            "qty": self.fixed_qty,
            "reduceOnly": is_close
        }

        timestamp, signature = self._get_signature(params)
        headers = self._get_headers(timestamp, signature)
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.post(url, headers=headers, json=params)
            return response.json()
        except Exception as e:
            print(f"Error in place_order: {e}")
            return {"error": str(e)}

# APIクライアントの初期化
bybit = BybitAPI(
    api_key="w5WJRy0x4w6b12yggY",
    api_secret="fTIUk3fh4dxSjBO9CWDThwJoTT5DYHwxo04K"
)

DOTEN = "false"

@app.route('/trade', methods=['POST'])
def trade():
    try:
        request_json = request.get_json()
        symbol = request_json.get('symbol', 'BTCUSDT')
        side = request_json.get('side', '')
        comment = request_json.get('comment', '')
        
        if DOTEN != "true":
            if "Close" in comment:
                # ポジションのクローズ
                result = bybit.place_order(symbol, side, is_close=True)
            else:
                # 新規ポジション
                result = bybit.place_order(symbol, side)
        else:
            # 両建て（DOTENモード）
            close_result = bybit.place_order(symbol, side, is_close=True)
            time.sleep(0.1)
            entry_result = bybit.place_order(symbol, side)
            result = {"close": close_result, "entry": entry_result}
            
        return jsonify({"status": "success", "result": result})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)