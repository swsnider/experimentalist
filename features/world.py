class World(object):
    def log(self, *args):
        '''Logs the given args to somewhere.

        Args should be concatenated by spaces.
        '''
        print *args

    def get_bucket_from_request(self, request):
        '''Given a request, determine what ID to use for bucketing.

        This is typically the primary key or email of the current user.
        '''
        return 1

    def features_from_request(self, request):
        '''Extract the features parameter from the request's url.

        For instance, get the 'features' query parameter, splitting on comma.
        '''
        return []

    def is_admin(self, request):
        '''Determine whether the current request comes from an admin.'''
        return False

    def is_internal(self, request):
        '''Determine whether the current request is internal.'''
        return False

    def user_name(self, request):
        '''Get the current user's username from the request.'''
        return ''

    def group_list(self, request):
        '''Return a list of group of which the current user is a member.'''
        return []
