#!/usr/bin/env python
# -*- coding: utf-8 -*-

from yowsup.layers.auth.protocolentities import SuccessProtocolEntity, FailureProtocolEntity
from yowsup.layers.protocol_acks.protocolentities.test_ack_incoming import entity as ack_incoming_entity
from yowsup.layers.protocol_acks.protocolentities import IncomingAckProtocolEntity
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities import IncomingReceiptProtocolEntity
from yowsup.layers.protocol_media.protocolentities.message_media_downloadable_image \
    import DownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities.message_media_downloadable_image \
    import ImageDownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities.message_media_downloadable_audio import \
    AudioDownloadableMediaMessageProtocolEntity
import time


def success_protocol_entity():
    attributes = {
        "status": "active",
        "kind": "free",
        "creation": "1234",
        "expiration": "1446578937",
        "props": "2",
        "t": "1415470561"
    }
    return SuccessProtocolEntity(**attributes)

def failure_protocol_entity():
    attributes = {
        "reason": "Auth incorrect"
    }
    return FailureProtocolEntity(**attributes)


def ack_incoming_protocol_entity(message=None):
    if not message:
        return ack_incoming_entity
    attributes = {
        "_id": message.getId(),
        "_class": message.getType(),
        "_from": message.getTo(),
        "timestamp": int(time.time())                  
    }
    return IncomingAckProtocolEntity(**attributes)

def text_message_protocol_entity():
    attributes = {
        "body": "received message",
        "_from": "bbb@s.whatsapp.net"
    }
    return TextMessageProtocolEntity(**attributes)

def receipt_incoming_protocol_entity():
    attributes = {
        "_id": "123",
        "_from": "sender",
        "timestamp": int(time.time())
    }
    return IncomingReceiptProtocolEntity(**attributes)

def image_downloadable_media_message_protocol_entity(url="url", to="341234567", ip="ip", caption="image caption"):
    attributes = {
        "mimeType": DownloadableMediaMessageProtocolEntity.MEDIA_TYPE_IMAGE,
        "fileHash": "filehash",
        "url": url,
        "ip": ip,
        "size": "1234",
        "fileName": "image.jpg",
        "encoding": "encoding",
        "width": "123",
        "height": "123",
        "caption": caption,
        "to": to
    }
    return ImageDownloadableMediaMessageProtocolEntity(**attributes)

def audio_downloadable_media_message_protocol_entity(url="url", to="341234567", ip="ip", caption="image caption"):
    attributes = {
        "mimeType": DownloadableMediaMessageProtocolEntity.MEDIA_TYPE_AUDIO,
        "fileHash": "filehash",
        "url": url,
        "ip": ip,
        "size": "1234",
        "fileName": "audio.mp3",
        "abitrate": "arbitrate",
        "acodec": "acodec",
        "asampfreq": "asampfreq",
        "duration": "10",
        "origin": "origin",
        "seconds": "100",        
        "encoding": "encoding",
        "to": to
    }
    return AudioDownloadableMediaMessageProtocolEntity(**attributes)
