import time
import uuid
import boto3
import os


def load_env_file(file_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    abs_file_path = os.path.join(script_dir, file_path)

    with open(abs_file_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key] = value


# Specify the path to your environment file
env_file_path = '.env'

# Load the environment variables from the file
load_env_file(env_file_path)

# Access the environment variables
aws_access_key_id = os.environ.get('aws_access_key_id')
aws_secret_access_key = os.environ.get('aws_secret_access_key')
region_name = os.environ.get('region_name')

session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name,
)


dynamodbClient = session.client('dynamodb')
dynamodbResource = session.resource('dynamodb')


def bootstrap(name, fields, billing_mode='PAY_PER_REQUEST'):
    try:
        table = dynamodbResource.Table(name)
        tableFields = list(map(lambda field: field.get('AttributeName'), table.attribute_definitions))
        missingFields = list(filter(lambda field: field.get('name') not in tableFields, fields))
        if missingFields:
            AttributeDefinitions=[]
            GlobalSecondaryIndexUpdates=[]
            for field in missingFields:
                AttributeDefinitions.append({
                    'AttributeName': field.get('name'),
                    'AttributeType': field.get('type')
                })
                GlobalSecondaryIndexUpdates.append({
                    'Create': {
                        'IndexName': f'{field.get("name")}Index',
                        'KeySchema': [
                            {
                                'AttributeName': field.get('name'),
                                'KeyType': 'HASH'
                            }
                            # Add more key schema attributes if needed
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'  # Projection type (e.g., ALL, KEYS_ONLY, INCLUDE)
                        },
                    }
                })
            table.update(
                AttributeDefinitions=AttributeDefinitions,
                GlobalSecondaryIndexUpdates=GlobalSecondaryIndexUpdates,
            )
    except Exception as e:
        try:
            AttributeDefinitions = [
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                }
            ]
            indexFields = list(filter(lambda field: field.get('index'), fields))
            for field in indexFields:
                AttributeDefinitions.append({
                    'AttributeName': field.get('name'),
                    'AttributeType': field.get('type')
                })
            GlobalSecondaryIndexes = list(map(lambda field: {
                    'IndexName': f'{field.get("name")}Index',
                    'KeySchema': [
                        {
                            'AttributeName': field.get('name'),
                            'KeyType': 'HASH'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    },
                }, indexFields))
            table = dynamodbResource.create_table(
                TableName=name,
                KeySchema=[
                    {
                        'AttributeName': 'id',
                        'KeyType': 'HASH'
                    }
                ],
                BillingMode=billing_mode,
                AttributeDefinitions=AttributeDefinitions,
                GlobalSecondaryIndexes=GlobalSecondaryIndexes,
            )
            table.wait_until_exists()
        except Exception as e:
            print(e)
            return None
    return table


class Model:
    _name = None
    _table = None
    _fields = None
    _billing_mode = 'PAY_PER_REQUEST'

    def __init__(self, **kwargs):
        self.id = None
        for key, value in kwargs.items():
            setattr(self, key, value)

    def create(self, values):
        if isinstance(values, list):
            for value in values:
                value['id'] = str(uuid.uuid4())
            return self._create(values)
        if isinstance(values, object):
            values['id'] = str(uuid.uuid4())
            return self._create(values)

    @classmethod
    def _create(cls, values):
        records = []
        if isinstance(values, list):
            try:
                cls._table = bootstrap(cls._name, cls._fields, cls._billing_mode) if cls._name else None
                with cls._table.batch_writer() as batch:
                    for value in values:
                        value['createdAt'] = str(time.time())
                        value['updatedAt'] = str(time.time())
                        batch.put_item(Item=value)
                        records.append(cls(**value))
            except Exception as e:
                print(e, "line 123")
        if isinstance(values, dict):
            try:
                cls._table = bootstrap(cls._name, cls._fields, cls._billing_mode) if cls._name else None
                values['createdAt'] = str(time.time())
                values['updatedAt'] = str(time.time())
                cls._table.put_item(Item=values)
                return cls(**values)
            except Exception as e:
                print(e)
                return cls()
        return records

    def read(self, ID=None):
        if not ID:
            ID = self.id
        return self._read(ID)

    @classmethod
    def _read(cls, IDS):
        Keys=list(map(lambda ID: {'id': ID}, IDS))
        try:
            cls._table = bootstrap(cls._name, cls._fields, cls._billing_mode) if cls._name else None
            response = dynamodbResource.batch_get_item(
                RequestItems={
                    cls._name: {
                        'Keys': Keys
                    }
                }

            )
            items = response['Responses'][cls._name]
            return items
        except Exception as e:
            raise Exception(e)

    def write(self, values):
        if isinstance(values, list):
            if any([not id for id in list(map(lambda item: item.get('id'), values))]):
                raise Exception('One record or more missing id')
            self._write(values)
        elif isinstance(values, dict):
            if 'id' not in values and not self.id:
                raise Exception('Missing id or not single record')
            for key, value in values.items():
                setattr(self, key, value)
            return self._write(self.__dict__)
        else:
            return False

    @classmethod
    def _write(cls, values):
        try:
            cls._table = bootstrap(cls._name, cls._fields, cls._billing_mode) if cls._name else None
            with cls._table.batch_writer() as batch:
                if isinstance(values, list):
                    recs = cls._read(list(map(lambda rec: rec.get('id'), values)))
                    for rec in recs:
                        for item in values:
                            if rec.get('id') == item.get('id'):
                                for key, value in item.items():
                                    rec[key] = value
                                    rec['updatedAt'] = str(time.time())
                                batch.put_item(Item=rec)
                elif isinstance(values, dict):
                    recs = cls._read([values.get('id')])
                    for key, value in values.items():
                        recs[0][key] = value
                        recs[0]['updatedAt'] = str(time.time())
                    batch.put_item(Item=recs[0])
                else:
                    return False
            return True
        except Exception as e:
            print(e)
            return False

    def delete(self, ids=[]):
        if self.id:
            ids.append(self.id)
        if not ids:
            return False
        return self._delete(ids)

    @classmethod
    def _delete(cls, ids=None):
        try:
            if ids is None:
                return False
            cls._table = bootstrap(cls._name, cls._fields, cls._billing_mode) if cls._name else None
            with cls._table.batch_writer() as batch:
                for ID in ids:
                    batch.delete_item(Key={'id': ID})
            return True
        except Exception as e:
            print(e)
            return False

    def search(self, gsi_domain):
        return self._search(gsi_domain)

    @classmethod
    def _search(cls, gsi_domain):
        indexFields = list(map(lambda filteredIndexField: filteredIndexField.get('name'), filter(lambda indexField: indexField.get('index'), cls._fields)))
        for domain in gsi_domain:
            if domain[0] not in indexFields:
                raise Exception(f'{domain[0]} is not an index field')
        try:
            cls._table = bootstrap(cls._name, cls._fields, cls._billing_mode) if cls._name else None
            TableName = cls._name
            IndexName = f'{gsi_domain[0][0]}Index'
            KeyConditionExpression = f'#{gsi_domain[0][0]} {gsi_domain[0][1]} :{gsi_domain[0][0]}'
            ExpressionAttributeNames = {}
            ExpressionAttributeValues = {}
            FilterExpression = f''
            for key, value in enumerate(gsi_domain):
                if key > 0:
                    FilterExpression += f'#{value[0]} {value[1]} :{value[0]}'
                ExpressionAttributeNames[f'#{value[0]}'] = value[0]
                ExpressionAttributeValues[f':{value[0]}'] = value[2]

            query_params = {
                'TableName': TableName,
                'IndexName': IndexName,
                'KeyConditionExpression': KeyConditionExpression,
                'ExpressionAttributeNames': ExpressionAttributeNames,
                'ExpressionAttributeValues': ExpressionAttributeValues,
            }
            if FilterExpression:
                query_params['FilterExpression'] = FilterExpression
            response = cls._table.query(**query_params)
            items = response.get('Items', [])
            results = []
            for item in items:
                instance = cls()
                for key, value in item.items():
                    setattr(instance, key, value)
                results.append(instance)
            return results
        except Exception as e:
            print(e)
            return []

