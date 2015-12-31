# -*- coding: utf-8 -*-
from yowsup.layers.interface import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers import EventCallback
from yowsup.layers.protocol_messages.protocolentities import \
    TextMessageProtocolEntity
import logging
from yowsup.layers.network import YowNetworkLayer
from yowsup.layers import YowLayerEvent
from functools import wraps
import sys
from yowsup_celery.layer_interface import CeleryLayerInterface
from yowsup_celery.exceptions import ConnectionError

logger = logging.getLogger(__name__)

def connection_required(f):
    @wraps(f)
    def decorated_function(self, *args, **kwargs):
        if not self.connected:
            raise ConnectionError("%s needs to be connected" % f.__name__)
        return f(self, *args, **kwargs)
    return decorated_function

class CeleryLayer(YowInterfaceLayer):    
    """
    Layer to be on the top of the Yowsup Stack. 
    :ivar bool connected: connected or not connected to whatsapp
    :ivar YowLayerInterface interface: layer interface
    """

    def __init__(self):
        super(CeleryLayer, self).__init__()
        self.connected = False
        self.interface = CeleryLayerInterface(self)

    def normalize_jid(self, number):
        if '@' in number:
            return number
        elif "-" in number:
            return "%s@g.us" % number

        return "%s@s.whatsapp.net" % number
        
    @ProtocolEntityCallback("success")
    def on_success(self, success_protocol_entity):
        """
        Callback when there is a successful connection to whatsapp server
        """
        logger.info("Logged in")
        self.connected = True
            
    @ProtocolEntityCallback("failure")
    def on_failure(self, entity):
        """
        Callback function when there is a failure in a connection to whatsapp 
        server
        """
        logger.error("Login failed, reason: %s" % entity.getReason())
        self.connected = False
        
    @ProtocolEntityCallback("ack")
    @connection_required
    def on_ack(self, entity):
        """
        Callback function when receiving an ack for a sent message from 
        whatsapp
        """
        logger.info("Ack id %s received" % entity.getId())
   
    @ProtocolEntityCallback("message")
    @connection_required
    def on_message(self, message_protocol_entity):
        """
        Callback function when receiving message from whatsapp server
        """
        logger.info("Message id %s received" % message_protocol_entity.getId())
        # answer with receipt
        self.toLower(message_protocol_entity.ack())
            
    @ProtocolEntityCallback("receipt")
    @connection_required
    def on_receipt(self, receipt_protocol_entity):
        """
        Callback function when receiving receipt message from whatsapp
        """
        self.toLower(receipt_protocol_entity.ack())
        
    @EventCallback(YowNetworkLayer.EVENT_STATE_DISCONNECTED)
    @connection_required
    def on_disconnected(self, yowLayerEvent):
        """
        Callback function when receiving a disconnection event
        """
        logger.info("On disconnected")
        self.connected = False
    
    @connection_required
    def send_message(self, number, content):
        """
        Send message
        :param str number: phone number with cc (country code)
        :param str content: body text of the message
        """
        outgoing_message = TextMessageProtocolEntity(content.encode("utf-8") if sys.version_info >= (3, 0)
                                                     else content, to=self.normalize_jid(number))
        self.toLower(outgoing_message)
        return outgoing_message
        
    def connect(self):
        if self.connected:
            logger.warning("Already connected, disconnect first")
            return False
        self.getLayerInterface(YowNetworkLayer).connect()
        return True

    @connection_required
    def disconnect(self):
        self.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_DISCONNECT))
        return True
