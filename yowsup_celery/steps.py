from __future__ import absolute_import
from celery import bootsteps
from yowsup_celery.stack import YowsupStack
from yowsup_celery.utils import import_string
import logging
from yowsup_celery.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

class YowsupStep(bootsteps.StartStopStep):    
    
    def _get_top_layers(self, worker):
        top_layers_string = worker.app.conf.table().get('TOP_LAYERS', None)
        top_layers = []
        if top_layers_string:
            for top_layer_string in top_layers_string:
                top_layer = import_string(top_layer_string)
                top_layers.append(top_layer)
        return tuple(top_layers)    
    
    def _get_config(self, config):
        try:
            with open(config, 'r') as f:
                out = {}
                for l in f:
                    line = l.strip()
                    if len(line) and line[0] not in ('#', ';'):
                        prep = line.split('#', 1)[0].split(';', 1)[0].split('=', 1)
                        varname = prep[0].strip()
                        val = prep[1].strip()
                        out[varname.replace('-', '_')] = val
                return out
        except IOError:
            logger.error("Invalid config path: %s" % config)
            raise ConfigurationError("Invalid config path: %s" % config)
    
    def _get_credentials(self, login, config, worker):
        if login:
            return tuple(login.split(":"))
        else:
            if not config:
                config = worker.app.conf.table().get('YOWSUPCONFIG', None)
            if config:
                config_credentials = self._get_config(config)
                if "password" not in config_credentials or "phone" not in config_credentials:
                    raise ConfigurationError("Must specify at least phone number and password in config file")
                return config_credentials["phone"], config_credentials["password"]
            else:
                return None
        
    def __init__(self, worker, login, config, unmoxie, **kwargs):
        """
        :param worker: celery worker
        :param login: optional login:password parameter
        :param config: optional path to configuration file
        :param unmoxie: boolean to disable encryption
        """
        credentials = self._get_credentials(login, config, worker)
        if not credentials:
            raise ConfigurationError("Error: You must specify a configuration method")
        worker.app.stack = YowsupStack(credentials, not unmoxie, self._get_top_layers(worker))
        logger.info("Yowsup for %s intialized" % credentials[0])

    def stop(self, worker):     
        logger.info("Stopping yowsup")
        if worker.app.stack.facade.connected():
            worker.app.stack.facade.disconnect()
            logger.info("Disconnect yowsup")
