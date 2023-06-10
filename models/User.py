from base.Model import Model


class User(Model):
    _name = 'userWassallyTable'
    _fields = [
        {
            'name': 'name',
            'type': 'S',
            'index': True
        },
        {
            'name': 'email',
            'type': 'S',
            'index': True
        },
    ]

