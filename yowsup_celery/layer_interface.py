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

    def connected(self):
        return self._layer.connected
