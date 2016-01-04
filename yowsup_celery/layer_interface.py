from yowsup.layers import YowLayerInterface


class CeleryLayerInterface(YowLayerInterface):
    
    def connect(self):
        return self._layer.connect()
    
    def disconnect(self):
        return self._layer.disconnect()
    
    def send_message(self, number, content):
        return self._layer.send_message(number, content)
    
    def send_image(self, number, path):
        return self._layer.send_image(number, path)
    
    def send_audio(self, number, path):
        return self._layer.send_audio(number, path)
    
    def send_location(self, number, name, url, latitude, longitude):
        return self._layer.send_location(number, name, url, latitude, longitude)
    
    def send_vcard(self, number, name, data):
        return self._layer.send_vcard(number, name, data)

    def connected(self):
        return self._layer.connected
