from __future__ import absolute_import

from celery import Task, shared_task
from functools import wraps

def listening_required(f):
    @wraps(f)
    def decorated_function(self, *args, **kwargs):
        if not self.stack.listening:
            listen.apply_async(queue=self.request.delivery_info['routing_key'])
            return self.retry()
        else:
            return f(self, *args, **kwargs)
    return decorated_function

   
class YowsupTask(Task):
    abstract = True
    default_retry_delay = 0.5
    
    @property
    def stack(self):
        return self.app.stack
    
    @property
    def facade(self):
        return self.app.stack.facade
    
    
@shared_task(base=YowsupTask, bind=True, ignore_result=True)
def listen(self):
    if not self.stack.listening:
        return self.stack.asynloop()
    else:
        return "Already listening"

@shared_task(base=YowsupTask, bind=True)
@listening_required
def connect(self):
    return self.facade.connect()
        

@shared_task(base=YowsupTask, bind=True)
@listening_required
def disconnect(self):
    return self.facade.disconnect()

@shared_task(base=YowsupTask, bind=True)
@listening_required
def send_message(self, number, content):
    self.facade.send_message(number, content)
    return True

@shared_task(base=YowsupTask, bind=True)
@listening_required
def send_image(self, number, path):
    self.facade.send_image(number, path)
    return True

@shared_task(base=YowsupTask, bind=True)
@listening_required
def send_audio(self, number, path):
    self.facade.send_audio(number, path)
    return True

@shared_task(base=YowsupTask, bind=True)
@listening_required
def send_location(self, number, name, url, latitude, longitude):
    self.facade.send_location(number, name, url, latitude, longitude)
    return True

@shared_task(base=YowsupTask, bind=True)
@listening_required
def send_vcard(self, number, name, data):
    self.facade.send_vcard(number, name, data)
    return True
