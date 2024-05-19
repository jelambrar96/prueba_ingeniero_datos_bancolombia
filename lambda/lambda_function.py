import json
import os
from datetime import datetime

import hashlib
import boto3

# leer variables de entorno de aws lambda
MY_AWS_ACCESS_KEY_ID = os.environ['MY_AWS_ACCESS_KEY_ID']
MY_AWS_SECRET_ACCESS_KEY = os.environ['MY_AWS_SECRET_ACCESS_KEY']
MY_AWS_REGION = os.environ['MY_AWS_REGION']

environment_condition = (not MY_AWS_ACCESS_KEY_ID is None) \
    and (not MY_AWS_SECRET_ACCESS_KEY is None) and (not MY_AWS_REGION is None)

AWS_DINAMODB_TABLE = os.environ['AWS_DINAMODB_TABLE']
# AWS_S3_BUCKET = os.environ['AWS_S3_BUCKET']

# Crear un cliente de S3 y DynamoDB utilizando las credenciales de las variables de entorno
s3_client = None
if environment_condition:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=MY_AWS_ACCESS_KEY_ID,
        aws_secret_access_key=MY_AWS_SECRET_ACCESS_KEY,
        region_name=MY_AWS_REGION
    )
else:
    s3_client = boto3.client('s3')

dynamodb_client = None
if environment_condition:
    dynamodb_client = boto3.resource(
        'dynamodb',
        aws_access_key_id=MY_AWS_ACCESS_KEY_ID,
        aws_secret_access_key=MY_AWS_SECRET_ACCESS_KEY,
        region_name=MY_AWS_REGION
    )
else:
    dynamodb_client = boto3.resource('dynamodb')


def lambda_handler(event, context) -> dict:
    """
    La función se activa automáticamente cuando se sube un archivo a un 
    bucket S3 específico. Su propósito es procesar el contenido del archivo, 
    validar su integridad mediante un hash MD5, almacenar los datos en una 
    tabla de DynamoDB y luego eliminar el archivo del bucket S3.

    Parameters
    ----------
    event : dict
        Contiene información sobre el evento que activó la Lambda Function, 
        en este caso, la subida de un archivo a S3.

    context : dict
        Proporciona información sobre el tiempo de ejecución de la Lambda Function.

    Returns
    -------
    Dictionary
    """


    # Obtener el bucket y el nombre del archivo del evento
    bucket, key = None, None
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
    except (KeyError, IndexError):
        raise Exception('Invalid data from event')

    # Obtener el contenido del archivo de S3
    try:
        file_content = s3_client.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8')
    except (ValueError, KeyError):
        raise Exception('Invalid data from file')


    # Procesar el contenido del archivo
    data = {}
    for line in file_content.strip().split('\n'):
        try:
            key, value = line.split('=')
            data[key] = value
        except ValueError:
            continue

    # Concatenar los valores en el orden especificado
    try:
        concatenated_string = (
            f"{data['totalContactoClientes']}~"
            f"{data['motivoReclamo']}~"
            f"{data['motivoGarantia']}~"
            f"{data['motivoDuda']}~"
            f"{data['motivoCompra']}~"
            f"{data['motivoFelicitaciones']}~"
            f"{data['motivoCambio']}"
        )
    except KeyError as k:
        raise k

    # Generar el HASH MD5
    generated_hash = hashlib.md5(concatenated_string.encode()).hexdigest()

    data_hash = None
    try:
        data_hash = str(data['hash'])
    except KeyError as k:
        raise k
    except TypeError as t:
        raise t
    except ValueError as v:
        raise v

    # Validar el HASH
    if generated_hash != data_hash:
        exception_message = (
            f'Hash mismatch: data integrity validation failed'
            f'HASH_GENERATED: "{generated_hash}"'
            f'EXPECTED_HASH: "{data_hash}"'
            f'CONCAT_STR: {concatenated_string}'
        )
        raise Exception(exception_message)

    # Preparar los datos para DynamoDB
    timestamp = datetime.utcnow().isoformat()
    item = {
        'timestamp': timestamp,
        'totalContactoClientes': data['totalContactoClientes'],
        'motivoReclamo': data['motivoReclamo'],
        'motivoGarantia': data['motivoGarantia'],
        'motivoDuda': data['motivoDuda'],
        'motivoCompra': data['motivoCompra'],
        'motivoFelicitaciones': data['motivoFelicitaciones'],
        'motivoCambio': data['motivoCambio']
    }

    # Almacenar los datos en DynamoDB
    table = dynamodb_client.Table(AWS_DINAMODB_TABLE)
    table.put_item(Item=item)

    # Eliminar el archivo de S3
    s3_client.delete_object(Bucket=bucket, Key=key)

    return {
        'statusCode': 200,
        'body': json.dumps('File processed and deleted successfully')
    }
