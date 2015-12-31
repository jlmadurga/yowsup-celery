#!/usr/bin/env python
# -*- coding: utf-8 -*-

from yowsup.layers import YowProtocolLayerTest
from yowsup_celery.layer import CeleryLayer
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities import IncomingReceiptProtocolEntity
import time
from yowsup_celery.exceptions import ConnectionError
from tests.utils import success_protocol_entity, failure_protocol_entity
from yowsup.layers import YowLayerEvent
from yowsup.layers.network import YowNetworkLayer
import unittest
try:
    from unittest import mock
except ImportError:
    import mock  # noqa
    

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
        
if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
