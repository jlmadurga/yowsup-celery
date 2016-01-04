# -*- coding: utf-8 -*-
from yowsup.layers.interface import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers import EventCallback
from yowsup.layers.protocol_messages.protocolentities import \
    TextMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities import RequestUploadIqProtocolEntity
from yowsup.layers.protocol_media.protocolentities.message_media_downloadable_image import \
    ImageDownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities.message_media_downloadable_audio import \
    AudioDownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities.message_media_location import LocationMediaMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities.message_media_vcard import VCardMediaMessageProtocolEntity
import logging
from yowsup.layers.network import YowNetworkLayer
from yowsup.layers import YowLayerEvent
from functools import wraps
import sys
import os
from yowsup_celery.layer_interface import CeleryLayerInterface
from yowsup_celery.exceptions import ConnectionError
from yowsup.layers.protocol_media.mediauploader import MediaUploader

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
    
    def do_send_image(self, file_path, url, to, ip=None, caption=None):
        entity = ImageDownloadableMediaMessageProtocolEntity.fromFilePath(file_path, url, ip, to, caption=caption)
        self.toLower(entity)

    def do_send_audio(self, file_path, url, to, ip=None, caption=None):
        entity = AudioDownloadableMediaMessageProtocolEntity.fromFilePath(file_path, url, ip, to)
        self.toLower(entity)
        
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
        
    def on_request_upload_result(self, jid, path, result_request_upload_iq_protocol_entity, 
                                 request_upload_iq_protocol_entity, caption=None):

        if request_upload_iq_protocol_entity.mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_AUDIO:
            do_send_fn = self.do_send_audio
        else:
            do_send_fn = self.do_send_image

        if result_request_upload_iq_protocol_entity.isDuplicate():
            do_send_fn(path, result_request_upload_iq_protocol_entity.getUrl(), jid,
                       result_request_upload_iq_protocol_entity.getIp(), caption)
        else:
            success_fn = lambda filePath, jid, url: do_send_fn(filePath, url, jid, 
                                                               result_request_upload_iq_protocol_entity.getIp(), 
                                                               caption)
            mediaUploader = MediaUploader(jid, self.getOwnJid(), path,
                                          result_request_upload_iq_protocol_entity.getUrl(),
                                          result_request_upload_iq_protocol_entity.getResumeOffset(),
                                          success_fn, self.on_upload_error, self.on_upload_progress, async=True)
            mediaUploader.start()
            
    def on_upload_error(self, file_path, jid, url):
        logger.error("Upload file %s to %s for %s failed!" % (file_path, url, jid))

    def on_upload_progress(self, file_path, jid, url, progress):
        logger.info("%s => %s, %d%% \r" % (os.path.basename(file_path), jid, progress))
    
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
    
    def _send_media_path(self, number, path, type, caption=None):
        jid = self.normalize_jid(number)
        entity = RequestUploadIqProtocolEntity(type, filePath=path)
        success_fn = lambda success_entity, original_entity: self.on_request_upload_result(jid, path, success_entity, 
                                                                                           original_entity, caption)
        error_fn = lambda error_entity, original_entity: self.on_request_upload_error(jid, path, error_entity, 
                                                                                      original_entity)
        self._sendIq(entity, success_fn, error_fn)

    @connection_required
    def send_image(self, number, path, caption=None):
        """
        Send image message
        :param str number: phone number with cc (country code)
        :param str path: image file path
        """
        return self._send_media_path(number, path, RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE, caption)
        
    @connection_required
    def send_audio(self, number, path):
        """
        Send audio message
        :param str number: phone number with cc (country code)
        :param str path: audio file path
        """
        return self._send_media_path(number, path, RequestUploadIqProtocolEntity.MEDIA_TYPE_AUDIO)
    
    @connection_required
    def send_location(self, number, name, url, latitude, longitude):
        """
        Send location message
        :param str number: phone number with cc (country code)
        :param str name: indentifier for the location
        :param str url: location url
        :param str longitude: location longitude
        :param str latitude: location latitude 
        """
        location_message = LocationMediaMessageProtocolEntity(latitude, longitude, name, url, encoding="raw", 
                                                              to=self.normalize_jid(number))
        self.toLower(location_message)
        return location_message
    
    @connection_required
    def send_vcard(self, number, name, data):
        """
        Send location message
        :param str number: phone number with cc (country code)
        :param str name: indentifier for the location
        :param str data: vcard format i.e.
        BEGIN:VCARD
        VERSION:3.0
        N:;Home;;;
        FN:Home
        item1.TEL:+34 911234567
        item1.X-ABLabel:Home
        END:VCARD
        """
        vcard_message = VCardMediaMessageProtocolEntity(name, data, to=self.normalize_jid(number))
        self.toLower(vcard_message)
        return vcard_message