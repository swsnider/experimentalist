'''Implements the public API for the features module.'''

from features import parser

class FeatureConfig(object):
    def __init__(self, config, world):
        '''Parses a feature configuration.

        Args:
            config: either a string, in which case we read config from that
                    file, or a feature configuration string
            world: a world object that we'll use to interface with the
                   outside world.
        '''
        try:
            with open(config) as f:
                self._config = parser.parse_config(f.read(), world)
        except:
            self._config = parser.parse_config(config, world)
        self._world = world

    def is_enabled(self, feature, request, alternate_id=None):
        '''Determine whether the given feature is enabled for this request.

        Args:
            feature: a string, the key of the feature in the config.
            request: an object representing the current request.
            alternate_id: optional. A value convertible to string representing
                          the actual id to use to bucketize for percentage
                          based experiments.

        Returns:
            True or False.

        Raises:
            ValueError: if the feature doesn't exist in the configuration
        '''
        if feature not in self.config:
            raise ValueError('Feature {0} is not present in the config'.format(feature))
        return self.config[feature].is_enabled(request, alternate_id)

    def variant(self, feature, request, alternate_id=None):
        '''Determine which feature variant to use for the current request.

        Args:
            feature: a string, the key of the feature in the config.
            request: an object representing the current request.
            alternate_id: optional. A value convertible to string representing
                          the actual id to use to bucketize for percentage
                          based experiments.

        Returns:
            The string name of the variant

        Raises:
            ValueError: if the feature doesn't exist in the configuration
        '''
        if feature not in self.config:
            raise ValueError('Feature {0} is not present in the config'.format(feature))
        return self.config[feature].variant(request, alternate_id)
