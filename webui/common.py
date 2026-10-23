from webui.serializers import NetworkSerializer
import httpx

def send_json(o, url):
    i = NetworkSerializer(o)

    httpx.post(url, data=i.data)