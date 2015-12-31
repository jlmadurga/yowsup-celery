#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from yowsup_celery import tasks
from celery import current_app
try:
    from unittest import mock
except ImportError:
    import mock  # noqa

class TestTasks(unittest.TestCase):
    
    def setUp(self):
        current_app.conf.CELERY_ALWAYS_EAGER = True

    def tearDown(self):
        pass
    
    def test_only_one_listen(self):
        with mock.patch('yowsup_celery.tasks.YowsupTask.stack', new_callable=mock.PropertyMock) as mock_stack:
            mock_stack.return_value = mock.MagicMock(listening=True)
            mock_stack.return_value.stack = mock.MagicMock()
            tasks.listen()
            self.assertEqual(0, mock_stack.asynloop.call_count)
            
    def test_listen(self):
        with mock.patch('yowsup_celery.tasks.YowsupTask.stack', new_callable=mock.PropertyMock) as mock_stack:
            mock_stack.return_value = mock.MagicMock(listening=False)
            mock_stack.return_value.stack = mock.MagicMock()
            tasks.listen()
            mock_stack.return_value.asynloop.assert_called_once_with()
                        
    def test_listen_required(self):
        with mock.patch('yowsup_celery.tasks.YowsupTask.stack', new_callable=mock.PropertyMock) as mock_stack, \
                mock.patch('yowsup_celery.tasks.YowsupTask.facade', new_callable=mock.PropertyMock) as mock_facade, \
                mock.patch('celery.app.task.Context', new_callable=mock.MagicMock) as mock_request, \
                mock.patch('yowsup_celery.tasks.connect.apply_async', new_callable=tasks.listen), \
                mock.patch('yowsup_celery.tasks.connect.retry', new_callable=tasks.connect):
            mock_request.return_value = mock.MagicMock(delivery_info={'routing_key': 'any_queue'})
            mock_stack.return_value = mock.MagicMock(listening=False)
            mock_stack.return_value.stack = mock.MagicMock()
            tasks.connect()
            mock_stack.return_value.asynloop.assert_called_once_with()
            mock_facade.return_value.connect.assert_called_once_with()
            
    def test_listen_required_not_needed(self):
        with mock.patch('yowsup_celery.tasks.YowsupTask.stack', new_callable=mock.PropertyMock) as mock_stack, \
                mock.patch('yowsup_celery.tasks.YowsupTask.facade', new_callable=mock.PropertyMock) as mock_facade:
            mock_stack.return_value = mock.MagicMock(listening=True)
            mock_stack.return_value.stack = mock.MagicMock()
            tasks.connect()
            self.assertEqual(0, mock_stack.asynloop.call_count)
            mock_facade.return_value.connect.assert_called_once_with()
            
if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
