from __future__ import absolute_import

from celery import Celery
from yowsup_celery.steps import YowsupStep
from celery.bin import Option

class YowCelery(Celery):
    
    def __init__(self, *args, **kwargs):
        super(YowCelery, self).__init__(*args, **kwargs)
        self.steps['worker'].add(YowsupStep)
        self.user_options['worker'].update(
            [Option('--yowlogin', dest='login', metavar="phone:b64password", default=None, 
                    help='''WhatsApp login credentials, in the format phonenumber:password, 
                    where password is base64 encoded.'''),
             Option('--yowconfig', dest='config', default=None, 
                    help='Path to config file containing authentication info.'),
             Option('--yowunmoxie', dest='unmoxie', action="store_true", default=False, 
                    help="Disable E2E Encryption")])
