#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import inspect
import threading
from yowsup.layers.interface import YowInterfaceLayer
from yowsup.layers.network import YowNetworkLayer
from yowsup.layers import YowLayerEvent, EventCallback
from tests.utils import success_protocol_entity, failure_protocol_entity, ack_incoming_protocol_entity, \
    text_message_protocol_entity, receipt_incoming_protocol_entity
from yowsup.layers.auth.autherror import AuthError
from yowsup_celery.stack import YowsupStack
from yowsup_celery.layer import CeleryLayer


try:
    from unittest import mock
except ImportError:
    import mock  # noqa
    

class SendProtocolEntityCallback(object):
    """
    Decorate callback for handling send protoocol entities
    """
    def __init__(self, entityType):
        self.entityType = entityType

    def __call__(self, fn):
        fn.send_entity_callback = self.entityType
        return fn

class CoreLayerMock(YowInterfaceLayer):
    """
    Mock layer to simulate core layers
    """
    
    def __init__(self, error_auth=False, error_ack=False):
        super(CoreLayerMock, self).__init__()
        self.send_entity_callbacks = {}
        self.error_auth = error_auth
        self.error_ack = error_ack
        self.connected = False
        self.lowerSink = []
        self.toLower = self.sendOverrider
        members = inspect.getmembers(self, predicate=inspect.ismethod)
        for m in members:
            if hasattr(m[1], "send_entity_callback"):
                fname = m[0]
                fn = m[1]
                self.send_entity_callbacks[fn.send_entity_callback] = getattr(self, fname)
                
    def sendOverrider(self, data):
        self.lowerSink.append(data)
                
    def send(self, entity):
        if not self.processIqRegistry(entity):
            entityType = entity.getTag()
            if entityType in self.send_entity_callbacks:
                self.send_entity_callbacks[entityType](entity)
            else:
                self.toLower(entity)

    @EventCallback(YowNetworkLayer.EVENT_STATE_CONNECT)
    def on_connect(self, event):
        if self.error_auth:
            self.connected = False
            protocol_entity = failure_protocol_entity()
        else:
            self.connected = True
            protocol_entity = success_protocol_entity()
        self.toUpper(protocol_entity)
        if not self.connected:
            raise AuthError()

    @EventCallback(YowNetworkLayer.EVENT_STATE_DISCONNECT)
    def on_disconnect(self, event):
        self.connected = False
        self.emitEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_DISCONNECTED, 
                                     reason="Connection closed", 
                                     detached=True))
        return True
    
    @SendProtocolEntityCallback("message")
    def on_message(self, message_protocol_entity):
        if not self.error_ack:
            self.toUpper(ack_incoming_protocol_entity(message_protocol_entity))
        self.toLower(message_protocol_entity)
        
    @SendProtocolEntityCallback("ack")
    def on_ack(self, ack_protocol_entity):
        self.toLower(ack_protocol_entity)
    
    @SendProtocolEntityCallback("entity")
    def on_receipt(self, receipt_protocol_entity):
        self.toLower(receipt_protocol_entity)
    
    def connect(self):
        if self.error_auth:
            self.connected = False
            protocol_entity = failure_protocol_entity()
        else:
            self.connected = True
            protocol_entity = success_protocol_entity()
        self.toUpper(protocol_entity)
        if not self.connected:
            raise AuthError()
        
    def receive_message(self):
        msg = text_message_protocol_entity()
        self.toUpper(msg)
        return msg
        
    def receive_ack(self):
        ack = ack_incoming_protocol_entity()
        self.toUpper(ack)
        return ack
        
    def receive_receipt(self):
        receipt = receipt_incoming_protocol_entity()
        self.toUpper(receipt)
        return receipt
        
    
class StackTest(unittest.TestCase):
    
    def setUp(self):
        self.stack = YowsupStack(("341111111", "password"))
        stackClassesArr = (CeleryLayer, CoreLayerMock)   
        self.stack._YowStack__stack = stackClassesArr[::-1]
        self.stack._YowStack__stackInstances = []
        self.stack._YowStack__props = {}
        self.stack._construct()
        self.stack.facade = self.stack.getLayerInterface(CeleryLayer)
        self.mock_layer = self.stack._YowStack__stackInstances[0]
        self.celery_layer = self.stack._YowStack__stackInstances[1]
        self.number = "341234567"
        self.content = "message test"
        self.message = (self.number, self.content)
        
    def _queue_thread(self, fn, *args, **kwargs):
        while not self.stack.listening:
            pass
        if fn:
            fn(*args, **kwargs)
        
    def _asynloop(self, asyn_action, timeout=0.1, auto_connect=False):
        self.input_thread = threading.Thread(target=self._queue_thread, args=(asyn_action,))
        self.input_thread.daemon = True
        self.input_thread.start()
        self.stack.asynloop(timeout=timeout, auto_connect=auto_connect)
        self.assertFalse(self.stack.listening, False)
        self.assertTrue(self.stack.detached_queue.empty())
        
    def test_asynloop_timeout(self):
        self._asynloop(None, 0.1)     
        
    def test_asynloop_autoconnect(self):
        def check_connected():
            self.assertTrue(self.stack.facade.connected())
        self._asynloop(check_connected, auto_connect=True) 
        
    def _test_asynloop(self, action):
        def queue_to_loop():
            self.assertTrue(self.stack.listening)
            self.stack.facade.connect()
            self.assertTrue(self.stack.facade.connected())
            if action:
                action()
            self.stack.facade.disconnect()
            self.assertFalse(self.stack.facade.connected())
        
        with mock.patch.object(YowsupStack, 'getLayerInterface', return_value=self.mock_layer) as mock_interface:
            mock_interface.return_value = self.mock_layer
            self._asynloop(queue_to_loop)
            
    def test_asynloop_disconnect(self):
        self._test_asynloop(None)
        
    def test_asynloop_receive_message(self):
        def receive_message():
            msg = self.mock_layer.receive_message()
            ack = self.mock_layer.lowerSink.pop()
            self.assertEqual(msg.getId(), ack.getId())
        self._test_asynloop(receive_message)
        
    def test_asynloop_receive_ack(self):
        def receive_ack():
            self.mock_layer.receive_ack()
            self.assertEqual([], self.mock_layer.lowerSink)         
        self._test_asynloop(receive_ack)
        
    def test_asynloop_receive_receipt(self):
        def receive_receipt():
            receipt = self.mock_layer.receive_receipt()
            ack = self.mock_layer.lowerSink.pop()
            self.assertEqual(receipt.getId(), ack.getId())
        self._test_asynloop(receive_receipt)
        
    def test_asynloop_send_message(self):
        def send_message():
            msg_to_send = self.stack.facade.send_message("341234567", "content")
            msg_sent = self.mock_layer.lowerSink.pop()
            self.assertEqual(msg_to_send.getId(), msg_sent.getId())
            self.assertEqual(msg_to_send.getBody(), msg_sent.getBody())
        self._test_asynloop(send_message)
