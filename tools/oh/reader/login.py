

class User(object):
    user_dict = {
        'aa': 'ert345',
        'bb': 'uio890',
    }

    def __init__(self, username):
        self.id = username
        self.is_active = True
        self.is_authenticated = True
        self.is_anonymous = False

    def get_id(self):
        try:
            return unicode(self.id)
        except AttributeError:
            raise NotImplementedError('No "id" attribute - override "get_id"')

    def __eq__(self, other):
        if isinstance(other, User):
            return self.get_id() == other.get_id()
        else:
            return NotImplemented

    def __ne__(self, other):
        equal = self.__eq__(other)
        if equal is NotImplemented:
            return NotImplemented
        return not equal
