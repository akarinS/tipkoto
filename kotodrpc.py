import json
import requests

class KotodRpc(object):

    def __init__(self, rpc_user, rpc_password, rpc_port = "8432"):
        self.auth = (rpc_user, rpc_password)
        self.url = "http://127.0.0.1:" + rpc_port

    def call(self, method, *params):
        data = json.dumps({"jsonrpc": "1.0",
                           "id"     : "",
                           "method" : method,
                           "params" : params})

        response = requests.post(self.url,
                                 auth    = self.auth,
                                 headers = {"content-type": "text/plain;"},
                                 data    = data)

        return response.json()["result"]

