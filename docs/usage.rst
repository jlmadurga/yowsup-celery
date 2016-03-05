========
Usage
========

Create a Yowcelery app::

	import yowsup_celery
	
	app = YowCelery('example',
             broker='amqp://',
             #backend='amqp://',
             include=['yowsup_celery.tasks'])
             
You can add other layer between core layers and celery top layer::

	app.conf.update(
	   TOP_LAYERS=('yowsup_ext.layers.store.layer.YowStorageLayer',)          
     )

Then to launch worker::

	$ celery -A proj worker -P gevent -c 2 -l info --yowconfig conf_wasap
	
Yowsup celery worker only works with gevent and threads pools. Yowsup asyncore socket need to be shared between tasks.

You can see the new worker options: celery -A proj worker --help::
  
  --yowconfig=CONFIG    Path to config file containing authentication info.
  --yowlogin=phone:b64password
                        WhatsApp login credentials, in the format
                        phonenumber:password,                      where
                        password is base64 encoded.
  --yowunmoxie          Disable E2E Encryption

Just call tasks as other celery app::

	from yowsup_celery import tasks

	tasks.connect.delay()
	tasks.send_message.delay("341234567", "New message sent")
	taks.disconnect.delay()
	
You can have a multiple workers for different phone numbers routing each worker to its queue::

	$ celery -A proj worker -P gevent -c 2 -l info --yowconfig conf_wasap_number1 -Q number1
	
When calling tasks queue to the queue desired::

	taks.connect.apply_async(queue="number1")	
	
If you want to use celery as daemon just add yowconfig path in configuration::

	app.conf.update(
	   YOWSUPCONFIG='path/to/yowsupconfig/file'          
     )

