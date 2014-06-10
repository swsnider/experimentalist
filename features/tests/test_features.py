import unittest

from features import config
from features import world

class MockRequest(object):
    def __init__(self, **kargs):
        self.user_id = 1
        self.features = []
        self.admin = False
        self.internal = False
        self.user_name = 'test_user'
        self.group_list = ['test_group']
        for k, v in kargs.items():
            setattr(self, k, v)

    def __str__(self):
        return ', '.join([str(i) for i in (self.user_id, self.features, self.admin, self.internal, self.user_name, self.group_list)])

class FeatureTest(unittest.TestCase):
    def setUp(self):
        self.world = world.World()
        self.world.get_bucket_from_request = lambda req: req.user_id
        self.world.features_from_request = lambda req: req.features
        self.world.is_admin = lambda req: req.admin
        self.world.is_internal = lambda req: req.internal
        self.world.user_name = lambda req: req.user_name
        self.world.group_list = lambda req: req.group_list
        self.world.hash = lambda h: float(h.split('-')[1])

    def test_default_disabled(self):
        conf = config.Feature('test', self.world, {})
        self.assertFalse(conf.is_enabled(MockRequest()))

    def test_fully_enabled(self):
        conf = config.Feature('test', self.world, {'enabled': 'on'})
        self.assertTrue(conf.is_enabled(MockRequest()))

    def test_simple_disabled(self):
        conf = config.Feature('test', self.world, {'enabled': 'off'})
        self.assertFalse(conf.is_enabled(MockRequest()))

    def test_variant_enabled(self):
        conf = config.Feature('test', self.world, {'enabled': 'winner'})
        self.assertEqual(conf.variant(MockRequest()), 'winner')
        self.assertEqual(conf.variant(MockRequest(user_id=2, user_name='other_test')), 'winner')

    def test_fully_enabled_string(self):
        conf = config.Feature('test', self.world, 'on')
        self.assertTrue(conf.is_enabled(MockRequest()))

    def test_simple_disabled_string(self):
        conf = config.Feature('test', self.world, 'off')
        self.assertFalse(conf.is_enabled(MockRequest()))

    def test_variant_enabled_string(self):
        conf = config.Feature('test', self.world, 'winner')
        self.assertEqual(conf.variant(MockRequest()), 'winner')
        self.assertEqual(conf.variant(MockRequest(user_id=2, user_name='other_test')), 'winner')

    def test_simple_rampup(self):
        conf = config.Feature('test', self.world, 50)
        self.assertTrue(conf.is_enabled(MockRequest(user_id=None), alternate_id=0))
        self.assertTrue(conf.is_enabled(MockRequest(user_id=None), alternate_id=0.1))
        self.assertTrue(conf.is_enabled(MockRequest(user_id=None), alternate_id=0.4999))
        self.assertFalse(conf.is_enabled(MockRequest(user_id=None), alternate_id=0.5))
        self.assertFalse(conf.is_enabled(MockRequest(user_id=None), alternate_id=0.6))
        self.assertFalse(conf.is_enabled(MockRequest(user_id=None), alternate_id=0.99))
        self.assertFalse(conf.is_enabled(MockRequest(user_id=None), alternate_id=1))

    def test_multivariant(self):
        conf = config.Feature('test', self.world, {'percentages': [(2, 'foo'), (3, 'bar')]})
        self.assertEqual(conf.variant(MockRequest(user_id=0)), 'foo')
        self.assertEqual(conf.variant(MockRequest(user_id=0.01)), 'foo')
        self.assertEqual(conf.variant(MockRequest(user_id=0.01999)), 'foo')
        self.assertEqual(conf.variant(MockRequest(user_id=0.02)), 'bar')
        self.assertEqual(conf.variant(MockRequest(user_id=0.04999)), 'bar')
        self.assertFalse(conf.is_enabled(MockRequest(user_id=0.05)))
        self.assertFalse(conf.is_enabled(MockRequest(user_id=1)))

    def test_complex_disabled(self):
        conf = config.Feature('test', self.world, dict(
            enabled='off',
            users={'test_user': 'on'},
            groups={'test_group': 'on'},
            admin='on',
            internal='on',
            public_url_override=True
        ))
        self.assertFalse(conf.is_enabled(MockRequest(admin=True, internal=True, features=['test'])))

    def test_admin_only(self):
        conf = config.Feature('test', self.world, {'admin': 'on'})
        self.assertFalse(conf.is_enabled(MockRequest()))
        self.assertTrue(conf.is_enabled(MockRequest(admin=True)))

    def test_admin_plus(self):
        conf = config.Feature('test', self.world, {'admin': 'on', 'enabled': 10})
        self.assertFalse(conf.is_enabled(MockRequest(user_id=0.5)))
        self.assertTrue(conf.is_enabled(MockRequest(admin=True, user_id=0.5)))
        self.assertTrue(conf.is_enabled(MockRequest(user_id=0.05)))

    def test_internal_only(self):
        conf = config.Feature('test', self.world, {'internal': 'on'})
        self.assertFalse(conf.is_enabled(MockRequest()))
        self.assertTrue(conf.is_enabled(MockRequest(internal=True)))

    def test_internal_plus(self):
        conf = config.Feature('test', self.world, {'internal': 'on', 'enabled': 10})
        self.assertFalse(conf.is_enabled(MockRequest(user_id=0.5)))
        self.assertTrue(conf.is_enabled(MockRequest(internal=True, user_id=0.5)))
        self.assertTrue(conf.is_enabled(MockRequest(user_id=0.05)))

    def test_one_user(self):
        conf = config.Feature('test', self.world, {'users': {'test_user': 'on'}})
        self.assertTrue(conf.is_enabled(MockRequest()))
        self.assertFalse(conf.is_enabled(MockRequest(user_name='test2')))

    def test_list_of_users(self):
        conf = config.Feature('test', self.world, {'users': {'test_user': 'winner2', 'test2': 'winner'}})
        self.assertEqual(conf.variant(MockRequest()), 'winner2')
        self.assertEqual(conf.variant(MockRequest(user_name='test2')), 'winner')
        self.assertFalse(conf.is_enabled(MockRequest(user_name='test3')))

    def test_one_group(self):
        conf = config.Feature('test', self.world, {'groups': {'test_group': 'on'}})
        self.assertTrue(conf.is_enabled(MockRequest()))
        self.assertFalse(conf.is_enabled(MockRequest(group_list=['test2'])))

    def test_list_of_groups(self):
        conf = config.Feature('test', self.world, {'groups': {'test_group': 'winner2', 'test2': 'winner'}})
        self.assertEqual(conf.variant(MockRequest()), 'winner2')
        self.assertEqual(conf.variant(MockRequest(group_list=['test2', 'test3'])), 'winner')
        self.assertFalse(conf.is_enabled(MockRequest(group_list=['test3'])))

    def test_url_override(self):
        conf = config.Feature('test', self.world, {})
        self.assertTrue(conf.is_enabled(MockRequest(features=['test'], admin=True)))
        self.assertTrue(conf.is_enabled(MockRequest(features=['test'], internal=True)))
        self.assertEqual(conf.variant(MockRequest(features=['test:alt'], admin=True)), 'alt')
        self.assertFalse(conf.is_enabled(MockRequest(features=['test'])))
        self.assertNotEqual(conf.variant(MockRequest(features=['test:alt'])), 'alt')

    def test_public_url_override(self):
        conf = config.Feature('test', self.world, {'public_url_override': True})
        self.assertTrue(conf.is_enabled(MockRequest(features=['test'], admin=True)))
        self.assertTrue(conf.is_enabled(MockRequest(features=['test'], internal=True)))
        self.assertEqual(conf.variant(MockRequest(features=['test:alt'], admin=True)), 'alt')
        self.assertTrue(conf.is_enabled(MockRequest(features=['test'])))
        self.assertEqual(conf.variant(MockRequest(features=['test:alt'])), 'alt')
