import asyncore
import time
import logging
import sys
import traceback
from yowsup import stacks
from yowsup_celery.layer import CeleryLayer
from yowsup_celery import exceptions
from yowsup.layers import YowLayerEvent
from yowsup.layers.auth import AuthError
from yowsup.layers.network import YowNetworkLayer
try:
    import Queue
except ImportError:
    import queue as Queue
    
logger = logging.getLogger(__name__)

class YowsupStack(stacks.YowStack):
    """
    Gateway for Yowsup in a client API way
    
    :ivar bool listening: asyncore loop task in execution
    :ivar Queue detached_queue: Queue with callbacks to execute after
    :ivar YowLayerInterface facade:layer interface on top of stack
    disconnection
    """
    
    def __init__(self, credentials, encryption=False, top_layers=None):
        """
        :param credentials: number and registed password
        :param bool encryptionEnabled:  E2E encryption enabled/ disabled
        :params top_layers: tuple of layer between :class:`yowsup_gateway.layer.CeleryLayer` 
        and Yowsup Core Layers  
        """
        top_layers = top_layers + (CeleryLayer,) if top_layers else (CeleryLayer,)
        layers = stacks.YowStackBuilder.getDefaultLayers(axolotl=encryption) + top_layers
        try:
            super(YowsupStack, self).__init__(layers, reversed=False)
        except ValueError as e:
            raise exceptions.ConfigurationError(e.args[0])
        self.setCredentials(credentials)
        self.detached_queue = Queue.Queue()
        self.facade = self.getLayerInterface(CeleryLayer)
        self.listening = False
        
    def execDetached(self, fn):
        return self.detached_queue.put(fn)
            
    def cleanup(self):
        self.listening = False
        self.detached_queue = Queue.Queue()

    def asynloop(self, auto_connect=False, timeout=10, detached_delay=0.2):
        """
        Non-blocking event loop consuming messages until connection is lost,
           or shutdown is requested.
        :param int timeout: number of secs for asyncore timeout
        :param float detached_delay: float secs to sleep when exiting asyncore loop and execution detached queue
            callbacks
        """
        if auto_connect:
            self.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))
        try:
            self.listening = True
            start = int(time.time())
            while True:
                asyncore.loop(timeout)
                time.sleep(detached_delay)
                try:
                    # Execute from detached queue callback
                    callback = self.detached_queue.get(False)
                    callback()
                except Queue.Empty:
                    pass
                if int(time.time()) - start > timeout:
                    logger.info("Asynloop : Timeout")
                    #  defensive code should be already disconneted
                    if self.facade.connected():
                        self.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_DISCONNECT))
                    break
            self.cleanup()
        except AuthError as e:
            self.cleanup()
            raise exceptions.AuthenticationError("Authentication Error: {0}".format(e))
        except:
            self.cleanup()
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            raise exceptions.UnexpectedError(str(exc_info[0]))
