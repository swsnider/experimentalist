'''Defines the objects that represent an individual feature's config.'''

def compute_percentages(percentages):
    total = 0
    ret = {}
    for percent, variant in percentages:
        if percent < 0 or percent > 100:
            raise ValueError('percentages must be between 0 and 100.')
        if percent > 0:
            total += percent
            ret[total] = variant
        if total > 100:
            raise ValueError('Percentages add up to more than 100%!')
    return ret

class Feature(object):
    def __init__(self, feature, world, stanza):
        self._feature = feature
        self._world = world
        if isinstance(stanza, basestring):
            stanza = dict(enabled=stanza)
        if isinstance(stanza, int) or isinstance(stanza, float):
            stanza = dict(percentages=[(stanza, 'on')])
        if isinstance(stanza.get('enabled', ''), int) or isinstance(stanza.get('enabled', ''), float):
            pers = stanza.get('percentages', [])
            pers.append((stanza.get('enabled'), 'on'))
            stanza['percentages'] = pers
            del stanza['enabled']
        self._users = stanza.get('users', None)
        self._groups = stanza.get('groups', None)
        self._admin = stanza.get('admin', None)
        self._internal = stanza.get('internal', None)
        self._percentages = compute_percentages(stanza.get('percentages', []))
        self._url = stanza.get('url', 'on')
        self._enabled = stanza.get('enabled', None)
        self._public_url = stanza.get('public_url_override', None)
        self._random = stanza.get('random', False)

    def is_enabled(self, request, alternate_id=None):
        '''Determine whether the feature is enabled for this request.

        Args:
            request: an object representing the current request.
            alternate_id: optional. A value convertible to string representing
                          the actual id to use to bucketize for percentage
                          based experiments.

        Returns:
            True or False.
        '''
        return self.variant(request, alternate_id) != 'off'

    def variant(self, request, alternate_id=None):
        '''Determine which feature variant to use for the current request.

        Args:
            request: an object representing the current request.
            alternate_id: optional. A value convertible to string representing
                          the actual id to use to bucketize for percentage
                          based experiments.

        Returns:
            The string name of the variant
        '''
        if self._enabled is not None:
            return self._enabled

        bucketing_id = self._world.get_bucket_from_request(request)
        if bucketing_id is None:
            if alternate_id is None:
                raise ValueError('alternate_id must be provided if the world'
                                 ' object refuses to provide one.')
            bucketing_id = str(alternate_id)
        if getattr(request, 'feature_cache', None) is None:
            request.feature_cache = {}
        if bucketing_id in request.feature_cache:
            return request.feature_cache[bucketing_id]

        res = self.variant_from_url(request)
        if not res: res = self.variant_for_user(request)
        if not res: res = self.variant_for_group(request)
        if not res: res = self.variant_for_admin(request)
        if not res: res = self.variant_for_internal(request)
        if not res: res = self.variant_by_percentage(bucketing_id)
        if not res: res = ('off', 'w')

        self._world.log(self._feature, res[0], res[1])
        request.feature_cache[bucketing_id] = res[0]
        return res[0]

    def variant_from_url(self, request):
        if self._public_url or self._world.is_admin(request) or self._world.is_internal(request):
            features = self._world.features_from_request(request)
            for f in features:
                v = self._url
                if ':' in f:
                    f, v = f.split(':')
                if self._feature == f:
                    return v, 'o'
        return False

    def variant_for_user(self, request):
        name = self._world.user_name(request)
        if self._users and name in self._users:
            return self._users[name], 'u'
        return False

    def variant_for_group(self, request):
        if not self._groups:
            return False
        groups = self._world.group_list(request)
        for group in groups:
            if group in self._groups:
                return self._groups[group], 'g'
        return False

    def variant_for_admin(self, request):
        if self._admin and self._world.is_admin(request):
            return self._admin, 'a'
        return False

    def variant_for_internal(self, request):
        if self._internal and self._world.is_internal(request):
            return self._internal, 'i'
        return False

    def variant_by_percentage(self, bucketing_id):
        if not self._percentages:
            return False
        n = 100 * self.randomish(bucketing_id)
        for percent in sorted(self._percentages.keys()):
            if n < percent:
                return self._percentages[percent], 'w'
        return False

    def randomish(self, bucketing_id):
        return self._world.random() if self._random else self._world.hash(self._feature + '-' + str(bucketing_id))
