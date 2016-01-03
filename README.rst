===============================
yowsup celery
===============================


CI:

.. image:: https://img.shields.io/travis/jlmadurga/yowsup-celery.svg
        :target: https://travis-ci.org/jlmadurga/yowsup-celery

.. image:: http://codecov.io/github/jlmadurga/yowsup-celery/coverage.svg?branch=master 
    :alt: Coverage
    :target: http://codecov.io/github/jlmadurga/yowsup-celery?branch=master
  
.. image:: https://requires.io/github/jlmadurga/yowsup-celery/requirements.svg?branch=master
     :target: https://requires.io/github/jlmadurga/yowsup-celery/requirements/?branch=master
     :alt: Requirements Status
     
PyPI:


.. image:: https://img.shields.io/pypi/v/yowsup-celery.svg
        :target: https://pypi.python.org/pypi/yowsup-celery

Docs:

.. image:: https://readthedocs.org/projects/yowsup-celery/badge/?version=latest
        :target: https://readthedocs.org/projects/yowsup-celery/?badge=latest
        :alt: Documentation Status
        

Yowsup integrated in a celery architecture

* Free software: ISC license
* Documentation: https://yowsup-celery.readthedocs.org.

Features
--------

* Celery app adapted to Yowsup
 	* Bootstep added to worker to initialize Yowsup and stopping when TERM (sometimes kill -9 is necessary)
 	* Options added to execute workers with different Whatsapp accounts
 	* Only works with gevent and threads as yowsup socket is shared between tasks

 
* Yowsup features included:
 	* Connect/Disconnect
 	* Send Text, Image and Audio Messages
 	* Receive Messages, Acks and Receipts

