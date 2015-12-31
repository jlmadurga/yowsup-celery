from __future__ import absolute_import

from yowsup_celery.celery import YowCelery

"""    
    Example of worker execution using gevent pool and two concurrent worker threads. With whatsapp configuration file
    in example/conf_wasa
    
  $ celery -A example worker -P gevent -c 2 -l info --yowconfig example/conf_wasap
  
  You can see the new worker options: celery -A example worker --help
  
  --yowconfig=CONFIG    Path to config file containing authentication info.
  --yowlogin=phone:b64password
                        WhatsApp login credentials, in the format
                        phonenumber:password,                      where
                        password is base64 encoded.
  --yowunmoxie          Disable E2E Encryption

"""

app = YowCelery('example',
             broker='amqp://',
             #backend='amqp://',
             include=['yowsup_celery.tasks'])

# Feel free to add other layers 
# app.conf.update(
#     TOP_LAYERS=('yowsup_ext.layers.store.layer.YowStorageLayer',)          
#     )
