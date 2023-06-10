from base.Model import Model


class Order(Model):
    _name = 'wassallyOrder'
    _fields = [
        {
            'name': 'name',
            'type':'S',
            'index': True
        },
        {
            'name': 'email',
            'type':'S',
            'index': True
        },
    ]

