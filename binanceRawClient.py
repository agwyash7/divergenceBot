import hmac
import json
import logging
import hashlib
import time
import requests
from pprint import pprint
from urllib.parse import urlencode


def cleanNoneValue(d) -> dict:
    out = {}
    for k in d.keys():
        if d[k] is not None:
            out[k] = d[k]
    return out


def get_timestamp():
    return int(time.time() * 1000)


def encoded_string(query):
    return urlencode(query, True).replace("%40", "@")


class BinanceRawClient(object):
    def __init__(self, key=None, secret=None, timeout=None, proxies=None, show_limit_usage=False, show_header=False):
        self.key = key
        self.secret = secret
        self.timeout = timeout
        self.base_url = "https://api.binance.com"
        self.show_limit_usage = False
        self.show_header = False
        self.proxies = None

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json;charset=utf-8",
                "X-MBX-APIKEY": key,
            }
        )

        if show_limit_usage is True:
            self.show_limit_usage = True

        if show_header is True:
            self.show_header = True

        if type(proxies) is dict:
            self.proxies = proxies

    def limit_request(self, http_method, url_path, payload=None):
        return self.send_request(http_method, url_path, payload=payload)

    def sign_request(self, http_method, url_path, payload=None):
        if payload is None:
            payload = {}
        payload["timestamp"] = get_timestamp()
        query_string = self._prepare_params(payload)
        signature = self._get_sign(query_string)
        payload["signature"] = signature
        return self.send_request(http_method, url_path, payload)

    def limited_encoded_sign_request(self, http_method, url_path, payload=None):
        if payload is None:
            payload = {}
        payload["timestamp"] = get_timestamp()
        query_string = self._prepare_params(payload)
        signature = self._get_sign(query_string)
        url_path = url_path + "?" + query_string + "&signature=" + signature
        return self.send_request(http_method, url_path)

    def send_request(self, http_method, url_path, payload=None):
        if payload is None:
            payload = {}
        url = self.base_url + url_path
        logging.debug("url: " + url)
        params = cleanNoneValue(
            {
                "url": url,
                "params": self._prepare_params(payload),
                "timeout": self.timeout,
                "proxies": self.proxies,
            }
        )
        response = self._dispatch_request(http_method)(**params)
        logging.debug("raw response from server:" + response.text)
        self._handle_exception(response)

        try:
            data = response.json()
        except ValueError:
            data = response.text
        result = {}

        if self.show_limit_usage:
            limit_usage = {}
            for key in response.headers.keys():
                key = key.lower()
                if (
                        key.startswith("x-mbx-used-weight")
                        or key.startswith("x-mbx-order-count")
                        or key.startswith("x-sapi-used")
                ):
                    limit_usage[key] = response.headers[key]
            result["limit_usage"] = limit_usage

        if self.show_header:
            result["header"] = response.headers

        if len(result) != 0:
            result["data"] = data
            return result

        return data

    @staticmethod
    def _prepare_params(params):
        return encoded_string(cleanNoneValue(params))

    def _get_sign(self, data):
        m = hmac.new(self.secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha256)
        return m.hexdigest()

    def _dispatch_request(self, http_method):
        return {
            "GET": self.session.get,
            "DELETE": self.session.delete,
            "PUT": self.session.put,
            "POST": self.session.post,
        }.get(http_method, "GET")

    @staticmethod
    def _handle_exception(response):
        status_code = response.status_code
        if status_code < 400:
            return
        if 400 <= status_code < 500:
            err = json.loads(response.text)
            print(f"Error-: ({err['code']}) {err['msg']}")

    def isolatedAccountInfo(self):
        url_path = "/sapi/v1/margin/isolated/account"
        return self.sign_request("GET", url_path)

    def activeIsolatedWalletInfo(self):
        info = (self.isolatedAccountInfo())["assets"]
        results = []
        for asset in info:
            if asset['enabled']:
                results.append(asset)

        return results


    def enableIsolatedWallet(self, symbol):
        url_path = "/sapi/v1/margin/isolated/account"
        payload = {"symbol": symbol}
        return self.sign_request("POST", url_path, payload)

    def disableIsolatedWallet(self, symbol):
        url_path = "/sapi/v1/margin/isolated/account"
        payload = {"symbol": symbol}
        return self.sign_request("DELETE", url_path, payload)


apiKey = "rN58tKBfaXISf8wXzScVxHe2wSu7jxIw45kjLX7bSSiEFlf0DYk0yPa3puqL4LOF"
apiSecret = "rmJwaoxzMQY7naQfAUQSDV4sKgb3uXTdIjZBvAjVEUxafhwuTQgsEJBh8PNCxNuz"
rawClient = BinanceRawClient(key=apiKey, secret=apiSecret)

rawClient.sign_request("GET", "/api/v3/exchangeInfo")
# activeCoins = rawClient.activeIsolatedWalletInfo()
#
# for activeCoin in activeCoins:
#     print(rawClient.disableIsolatedWallet(symbol=activeCoin['symbol']))
#     time.sleep(5)
# print(rawClient.enableIsolatedWallet(symbol="AAVEBTC"))