class Error(Exception): pass


class FeatureConfig(object):
    OFF = 'off'
    ON = 'on'
    def __init__(self, world, config):
        self._world = world
        self.config = self._parse_config(config)

    def is_enabled(self, *args, **kargs):
        return self.variant(*args, **kargs) != FeatureConfig.OFF

    def variant(self, feature_name, request, instance=None, other_id=None):
        if instance is None and bucket_id is None:
            raise ValueError('Either a model instance or a other_id must be specified.')
        bucketing_id = other_id
        if other_id is None:
            if instance is not None:
                bucketing_id = instance.id

        feature = self.config.get(feature_name, None)
        if not feature:
            raise ValueError('Feature {0} does not exist in the configuration.'.format(feature_name))
        if isinstance(feature, basestring)
            return feature
        if not getattr(request, 'feature_cache', None):
            request.feature_cache = {}
        if bucketing_id in self._cache:
            return request.feature_cache[bucketing_id]

        v, selector = self._variant_from_url(feature_name, request)
        if not v: v, selector = self._variant_for_user(feature_name, request)
        if not v: v, selector = self._variant_for_group(feature_name, request)
        if not v: v, selector = self._variant_for_admin(feature_name, request)
        if not v: v, selector = self._variant_for_internal(feature_name, request)
        if not v: v, selector = self._variant_by_percentage(feature_name, bucketing_id)
        if not v: v, selector = (FeatureConfig.OFF, 'w')

        request.feature_cache[bucketing_id] = v
        return v

    def _variant_from_url(self, feature_name, request):
        if self.config[feature_name].get('public_url_override', False) or
           self._world.is_admin(request) or
           self._world.is_internal(request):
            features = self._world.get_features(request)
            for feature in features.split(','):
                if feature == feature_name:
                    return FeatureConfig.ON, 'o'
            return False, False

    def _variant_for_user(self, feature_name, request):
        if not self.config[feature_name].get('users', False):
            return False, False

        uname = self._world.get_user_name(request)
        if uname in self.config[feature_name]['users']:
            return self.config[feature_name]['users'][uname], 'u'
        return False, False

    def _variant_for_group(self, feature_name, request):
        if not self.config[feature_name].get('groups', False):
            return False, False

        groups = self._world.get_group_list(request)
        for group in groups:
            if group in self.config[feature_name]['groups']:
                return self.config[feature_name]['groups'][group], 'g'
        return False, False

    def _variant_for_admin(self, feature_name, request):
        if not self.config[feature_name].get('admin', False):
            return False, False

        if self._world.is_admin(request):
            return self.config[feature_name]['admin'], 'a'

        return False, False

    def _variant_for_internal(self, feature_name, request):
        if not self.config[feature_name].get('internal', False):
            return False, False

        if self._world.is_internal(request):
            return self.config[feature_name]['internal'], 'a'

        return False, False

    def _randomish(self, feature_name, bucketing_id):
        if self.config[feature_name].get('bucketing', True) == 'random':
            return self._world.random()
        return self._world.hash(feature_name + '-' + bucketing_id)

    def _variant_by_percentage(self, feature_name, bucketing_id):
        n = 100 * self.randomish(feature_name, bucketing_id)
        for percent, v in self.config[feature_name].get('percentages', {}):
            if n < percent || percent == 100:
                return v, 'w'
