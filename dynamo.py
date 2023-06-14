import os
import boto3

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

client = session.client('dynamodb')
resource = session.resource('dynamodb')
