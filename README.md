# serverlessORM

An Odoo-like serverless ORM using AWS DynamoDB 


## Model

To create a new model

``` python
from base.Model import Model


class Users(Model):
    _name = 'Users'
    _fields = [
        {
            'name': 'fieldName',
            'type': 'S',
            'index': True, 
            'default': 'String'
        }, ...
    ]
```

## Methods
Currently available methods
### create
``` python
    from models import users

    someUser = users.create({
        'key': 'value',
    }) # create single record

    someUsers = users.create([
        {
            'key': 'value',
        },
        {
            'key': 'value',
        }, ...
    ]) # or create multiple records
```

### read
``` python
    from models import users

    ids = [
        'UUID4',
        'UUID4',
        'UUID4',
    ]
    someUsers = users.read(ids) # returns list of dictionaries
    for user in someUsers:
        print(user.get('name'))
```

### search
``` python
    from models import users

    domain = [
        ('key', '=', 'value')
    ] # currently simple query operatorssoon will add full polish-notation support

    someUsers = users.search(domain) # returns list of records

    for user in someUsers:
        print(user.name) 
```

### write
``` python
    from models import users

    users.write({
        'id': 'UUIDv4'
        'key': 'value',
    }) # you can update single record by passing its id to model method

    users.write([
        {
            'id': 'UUIDv4'
            'key': 'value',
        },
        {
            'id': 'UUIDv4'
            'key': 'value',
        },...
    ]) # you can update multiple records by passing id of record

    someUser = users.read(ids)

    for user in someUsers:
        user.write({
            'key': 'value',
        }) # no need to include id if you use update on the instance
```



### delete
``` python
    from models import users

    someUser = users.delete(ids) # you can delete single or multiple records
```


