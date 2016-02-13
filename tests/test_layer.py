#!/usr/bin/env python
# -*- coding: utf-8 -*-

from yowsup.layers import YowProtocolLayerTest
from yowsup_celery.layer import CeleryLayer
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities import IncomingReceiptProtocolEntity
import time
from yowsup_celery.exceptions import ConnectionError
from tests.utils import success_protocol_entity, failure_protocol_entity, \
    image_downloadable_media_message_protocol_entity, audio_downloadable_media_message_protocol_entity
from yowsup.layers import YowLayerEvent
from yowsup.layers.network import YowNetworkLayer
import unittest
from yowsup.layers.protocol_media.protocolentities.message_media_downloadable import \
    DownloadableMediaMessageProtocolEntity
try:
    from unittest import mock
except ImportError:
    import mock  # noqa
    
def init_request_upload(self, mediaType, filePath):
    self.tag = "iq"
    self._id = "id_iq"
    self._from = None
    self._type = "set"
    self.xmlns = "w:m"
    self.to = "s.whatsapp.net"
    self.mediaType = mediaType
    self.b64Hash = "hash"
    self.size = int("1234")
    self.origHash = "orighash"

class CeleryLayerTest(YowProtocolLayerTest, CeleryLayer):
    
    def setUp(self):
        CeleryLayer.__init__(self)
        self.connected = True
        self.number = "341234567"
        self.content = "content"
        
    def receive_message(self):
        content = "Received message"
        jid = "bbb@s.whatsapp.net"
        msg = TextMessageProtocolEntity(content, _from=jid)
        self.receive(msg)
        return msg
    
    def receive_receipt(self):
        receipt = IncomingReceiptProtocolEntity("123", "sender", int(time.time()))
        self.receive(receipt)
        return receipt    
    
    def test_already_connected(self):
        self.connected = True
        self.assertFalse(self.connect())
              
    def test_connection_successful(self):
        self.connected = False
        self.on_success(success_protocol_entity())
        self.assertTrue(self.connected)

    def test_connection_failure(self):
        self.connected = True
        self.on_failure(failure_protocol_entity())
        self.assertFalse(self.connected)
        
    def test_ack_for_received_message(self):
        msg = self.receive_message()
        ack = self.lowerSink.pop()
        self.assertEqual(ack.getId(), msg.getId())
        
    def test_ack_for_received_receipt(self):
        receipt = self.receive_receipt()
        ack = self.lowerSink.pop()
        self.assertEqual(ack.getId(), receipt.getId())
        
    def test_connection_required(self):
        self.connected = False
        self.assertRaises(ConnectionError, self.send_message, self.number, self.content)
        
    def test_send_message(self):
        msg = self.send_message(self.number, self.content)
        out_msg = self.lowerSink.pop()
        self.assertEqual(msg.getId(), out_msg.getId())
        self.assertEqual(self.number + '@s.whatsapp.net', out_msg.getTo())
        self.assertEqual(self.content, out_msg.getBody().decode('utf-8'))
        
    def test_disconnect(self):
        self.connected = True
        self.disconnect()
        evt = self.lowerEventSink.pop()
        self.assertEqual(evt.name, YowLayerEvent(YowNetworkLayer.EVENT_STATE_DISCONNECT).name)
        
    def test_connect(self):
        self.connected = False
        self.getLayerInterface = mock.MagicMock()
        self.getLayerInterface.return_value.connect = mock.MagicMock()
        self.connect()
        self.getLayerInterface.return_value.connect.assert_called_once_with()
         
    def test_on_disconnected(self):
        self.connected = True
        self.onEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_DISCONNECTED))
        self.assertFalse(self.connected)

    def _test_send_media_to_upload(self, fn, *args, **kwargs):
        with mock.patch('yowsup.layers.protocol_media.protocolentities.iq_requestupload.RequestUploadIqProtocolEntity.__init__',  # noqa
                        init_request_upload):  
            fn(*args, **kwargs)
            entity_iq = self.lowerSink.pop()
            iq_entity_registered, iq_on_success, iq_on_error = self.iqRegistry[entity_iq.getId()]
            self.assertEqual(entity_iq.getId(), iq_entity_registered.getId())
            self.assertEqual(entity_iq.getType(), iq_entity_registered.getType())            
    
    def test_send_image_to_upload(self):
        self._test_send_media_to_upload(self.send_image, "341234567", "path/image.jpg", "image caption")
                                       
    def test_send_audio_to_upload(self):
        self._test_send_media_to_upload(self.send_audio, "341234567", "path/audio.mp3")

    def test_send_image_to_do(self):
        path = "file_path/image.jpg"
        url = "image_url"
        to = "3412345670"
        ip = "192.12.1.1"
        caption = "caption"
        with mock.patch('yowsup.layers.protocol_media.protocolentities.message_media_downloadable_image.ImageDownloadableMediaMessageProtocolEntity.fromFilePath') as mock_image:  # noqa
            mock_image.return_value = image_downloadable_media_message_protocol_entity(url, to, ip, caption)
            self.do_send_image(path, url, to, ip, caption)
            entity = self.lowerSink.pop()
            self.assertEqual(entity.caption, caption)
            self.assertEqual(entity.to, to)
            self.assertEqual(entity.url, url)
            self.assertEqual(entity.getMediaType(), DownloadableMediaMessageProtocolEntity.MEDIA_TYPE_IMAGE)
            
    def test_send_audio_to_do(self):
        path = "file_path/audio.mp3"
        url = "audio_url"
        to = "3412345670"
        ip = "192.12.1.1"     
        with mock.patch('yowsup.layers.protocol_media.protocolentities.message_media_downloadable_audio.AudioDownloadableMediaMessageProtocolEntity.fromFilePath') as mock_audio:  # noqa
            mock_audio.return_value = audio_downloadable_media_message_protocol_entity(url, to, ip)
            self.do_send_audio(path, url, to, ip)
            entity = self.lowerSink.pop()
            self.assertEqual(entity.to, to)
            self.assertEqual(entity.url, url)
            self.assertEqual(entity.getMediaType(), DownloadableMediaMessageProtocolEntity.MEDIA_TYPE_AUDIO)
            
    def test_send_location(self):
        params = {
            "number": "341234567",
            "name": "Cerro espino",
            "url": "https://foursquare.com/v/4ca5ffa797c8a1cd9edc6ba5",
            "latitude": "40.458197101060826",
            "longitude": "-3.8601064682006836"
        }
        location_message = self.send_location(**params)
        out_msg = self.lowerSink.pop()
        self.assertEqual(location_message.getId(), out_msg.getId())
        self.assertEqual(params["number"] + '@s.whatsapp.net', out_msg.getTo())
        self.assertEqual(params["name"], out_msg.getLocationName())
        self.assertEqual(params["url"], out_msg.getLocationURL())
        self.assertEqual(params["latitude"], out_msg.getLatitude())
        self.assertEqual(params["longitude"], out_msg.getLongitude())
        
    def test_send_vcard(self):
        params = {
            "number": "341234567", 
            "name": "Grandma",
            "data": """BEGIN:VCARD\nVERSION:3.0\nN:;Grandma;;;N:;Grandma;;;\nFN:Grandma\n
                item1.TEL:+34 1234567\nitem1.X-ABLabel:Home\nEND:VCARD\n"""
        }
        vcard_message = self.send_vcard(**params)
        out_msg = self.lowerSink.pop()
        self.assertEqual(vcard_message.getId(), out_msg.getId())
        self.assertEqual(params["number"] + '@s.whatsapp.net', out_msg.getTo())
        self.assertEqual(params["name"], out_msg.getName())
        self.assertEqual(params["data"], out_msg.getCardData())
        
        
if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
