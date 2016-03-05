#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from yowsup_celery.steps import YowsupStep
from yowsup_celery.stack import YowsupStack
from yowsup_celery.layer_interface import CeleryLayerInterface
from yowsup_celery.exceptions import ConfigurationError
try:
    from unittest import mock
except ImportError:
    import mock  # noqa

class TestYowsupStep(unittest.TestCase):

    def setUp(self):
        self.worker = mock.Mock()
        self.worker.app.conf.table = mock.MagicMock(return_value={})

    def tearDown(self):
        pass
    
    def assertStackIntiliazed(self, stack):
        self.assertIsInstance(stack, YowsupStack)
        self.assertFalse(stack.listening)
        self.assertIsInstance(stack.facade, CeleryLayerInterface)
        
    def _correct_login_step(self):
        return YowsupStep(self.worker, "341234567:password", None, True)

    def test_init_login_ok(self):
        YowsupStep(self.worker, "341234567:password", None, True)
        self.assertStackIntiliazed(self.worker.app.stack)
        
    def test_init_conf_ok(self):
        with mock.patch('six.moves.builtins.open', mock.mock_open(read_data='adasdasd')) as m:
            handle = m.return_value.__enter__.return_value
            handle.__iter__.return_value = iter(["####confifle\n", "phone=341111111\n", "password=asdasdasdasd\n"])
            YowsupStep(self.worker, None, "file_path", True)
            self.assertStackIntiliazed(self.worker.app.stack)
    
    def test_init_conf_file_not_complete(self):
        with mock.patch('six.moves.builtins.open', mock.mock_open(read_data='adasdasd')) as m:
            handle = m.return_value.__enter__.return_value
            handle.__iter__.return_value = iter(["####confifle\n", "password=asdasdasdasd\n"])
            self.assertRaises(ConfigurationError, YowsupStep, self.worker, None, "file_path", True)
    
    def test_init_conf_file_not_exists(self):
        self.assertRaises(ConfigurationError, YowsupStep, self.worker, None, "file_path", True)        
        
    def test_init_no_configuration_method(self):
        self.assertRaises(ConfigurationError, YowsupStep, self.worker, None, None, True)
    
    def test_init_conf_file_only_in_configuration(self):
        with mock.patch('six.moves.builtins.open', mock.mock_open(read_data='adasdasd')) as m:
            handle = m.return_value.__enter__.return_value
            handle.__iter__.return_value = iter(["####confifle\n", "phone=341111111\n", "password=asdasdasdasd\n"])
            self.worker.app.conf.table = mock.MagicMock(return_value={'YOWSUPCONFIG': 'file_path'})
            YowsupStep(self.worker, None, None, True)
            self.assertStackIntiliazed(self.worker.app.stack)
        
    def test_init_top_layer_not_interface_layer(self):
        self.worker.app.conf.table = mock.MagicMock(return_value={'TOP_LAYERS': ('yowsup.stacks.yowstack.YowStack',)})
        self.assertRaises(ConfigurationError, YowsupStep, self.worker, "341234567:password", None, True)
        
    def test_init_top_layer_not_module(self):
        self.worker.app.conf.table = mock.MagicMock(return_value={'TOP_LAYERS': ('not_module',)})
        self.assertRaises(ImportError, YowsupStep, self.worker, "341234567:password", None, True)
        
    def test_init_top_layer_not_class(self):
        self.worker.app.conf.table = mock.MagicMock(return_value={'TOP_LAYERS': ('yowsup.stacks.yowstack.NoDefined',)})
        self.assertRaises(ImportError, YowsupStep, self.worker, "341234567:password", None, True)
        
    def test_stop_when_connected(self):
        step = self._correct_login_step()
        self.worker.app.stack.facade.connected = mock.MagicMock(return_value=True)
        self.worker.app.stack.facade.disconnect = mock.MagicMock()
        step.stop(self.worker)
        self.worker.app.stack.facade.disconnect.assert_called_once_with()
        
    def test_stop_not_connected(self):
        step = self._correct_login_step()
        self.worker.app.stack.facade.connected = mock.MagicMock(return_value=False)
        self.worker.app.stack.facade.disconnect = mock.MagicMock()
        step.stop(self.worker)
        self.assertEqual(0, self.worker.app.stack.facade.disconnect.call_count)

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
