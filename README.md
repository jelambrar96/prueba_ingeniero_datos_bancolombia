# Prueba Ingeniero Datos Bancolombia

##  Componente práctico Contexto:

La empresa Muebles SAS usa un chat en su página web como canal principal de comunicación con sus clientes. Este chat es de un proveedor llamado TuContacto, quien envía varias veces al día información consolidada a Muebles SAS con las estadísticas respecto al motivo de contacto de sus clientes (esta información son la base de la estrategia de fidelización de clientes de Muebles SAS). Actualmente esta información es enviada como un archivo de texto plano a un Bucket de S3 de Muebles SAS.

## Necesidad:

Se deben procesar los archivos y realizar las siguientes acciones:
- Se debe generar un HASH (MD5) de la información concatenada y validar que sea el mismo HASH que se encuentra en el archivo (así garantizar que los datos son correctos).
- El artefacto desarrollado se debe subir a una lambda en lenguaje de Python. La lambda se ejecuta automáticamente apenas se sube un archivo al bucket.
- Se debe almacenar la información procesada en una tabla de DynamoDB en formato JSON.
- Se debe eliminar el archivo plano de S3.
- El desarrollo debe contar con pruebas unitarias de al menos 70% cobertura.
- El desarrolló se debe subir a github y compartirlo a leyser7, Alexsanchez-WP y ManuLasker
- Contenido del archivo plano:

```
totalContactoClientes=250
motivoReclamo=25
motivoGarantia=10
motivoDuda=100
motivoCompra=100
motivoFelicitaciones=7
motivoCambio=8
hash=2f941516446dce09bc2841da60bf811f
```

- El HASH (MD5) se genera a partir de la concatenación de los campos del archivo de la siguiente manera:
Orden de los campos `totalContactoClientes~motivoReclamo~motivoGarantia~motivoDuda~motivoCompra~motivoFelicitaciones~motivoCambio`
Ejemplo con los datos anteriores: String base `250~25~10~100~100~7~8` Ejemplo con los datos `2f941516446dce09bc2841da60bf811f` anteriores: HASH
- Datos de la infraestructura
    - Lambda:
        - `arn:aws:lambda:us-east-1:223690032992:function: ai-technical-test-<userName>`
    - S3:
        - ARN del bucket: `arn:aws:s3:::ai-technical-test-<userName>`
    - Dynamodb
        - ARN de la tabla: `arn:aws:dynamodb:us-east-1:223690032992:table/ai-technical-test-<userName>`
        - Clave principal: “timestamp” (tipo String)


Nota:
    - En el campo `“<userName>”`, ingrese el nombre de usuario proporcionado en el correo electrónico. Ejemplo: Si su nombre de usuario es “juan123”, el arn de su lambda es `arn:aws:lambda:us-east-1:223690032992:function: ai-technical-test-juan123`
    - En la página 3 de este documento encontrada un ejemplo de un evento de s3 para la lambda.

## Solucion propuesta

Para cumplir con las necesidades descritas, vamos a desarrollar una solución en Python utilizando AWS Lambda, S3 y DynamoDB. Aquí hay un desglose de los pasos y el código necesario para completar la tarea:

### 1. Configuración de AWS Lambda para activar al subir un archivo a S3

Primero, configuraremos una Lambda Function en AWS que se active automáticamente cuando se suba un archivo al bucket S3. Luego, crearemos el código para la Lambda Function.

###  2. Código de la Lambda Function en Python

![Codigo lambda](https://github.com/jelambrar96/prueba_ingeniero_datos_bancolombia/blob/master/lambda/lambda_function.py)

#### Documentación del Código de la Lambda Function en Python

Este script de Python está diseñado para ejecutarse como una función Lambda en AWS. La función se activa automáticamente cuando se sube un archivo a un bucket S3 específico. Su propósito es procesar el contenido del archivo, validar su integridad mediante un hash MD5, almacenar los datos en una tabla de DynamoDB y luego eliminar el archivo del bucket S3.

#### Dependencias

- `hashlib`: Biblioteca estándar de Python para generar hashes.
- `json`: Biblioteca estándar de Python para trabajar con JSON.
- `boto3`: SDK de Amazon Web Services (AWS) para Python, utilizado para interactuar con los servicios S3 y DynamoDB.
- `datetime`: Biblioteca estándar de Python para trabajar con fechas y horas.

#### Inicialización de Clientes AWS

```python
# Crear un cliente de S3 y DynamoDB
s3_client = boto3.client('s3')
dynamodb_client = boto3.resource('dynamodb')
```

Se crean instancias de clientes de S3 y DynamoDB utilizando `boto3`, lo que permite interactuar con estos servicios desde el script.

#### Función Lambda Handler

```python
def lambda_handler(event, context):
    # Obtener el bucket y el nombre del archivo del evento
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Obtener el contenido del archivo de S3
    file_content = s3_client.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8')
```

- **Parámetros**:
  - `event`: Contiene información sobre el evento que activó la Lambda Function, en este caso, la subida de un archivo a S3.
  - `context`: Proporciona información sobre el tiempo de ejecución de la Lambda Function.

Se obtiene el nombre del bucket y el nombre del archivo del evento. Luego, se lee el contenido del archivo desde S3 y se decodifica de bytes a string.

#### Procesamiento del Contenido del Archivo

```python
    # Procesar el contenido del archivo
    data = {}
    for line in file_content.strip().split('\n'):
        key, value = line.split('=')
        data[key] = value

    # Concatenar los valores en el orden especificado
    concatenated_string = f"{data['totalContactoClientes']}~{data['motivoReclamo']}~{data['motivoGarantia']}~{data['motivoDuda']}~{data['motivoCompra']}~{data['motivoFelicitaciones']}~{data['motivoCambio']}"
    
    # Generar el HASH MD5
    generated_hash = hashlib.md5(concatenated_string.encode()).hexdigest()
    
    # Validar el HASH
    if generated_hash != data['hash']:
        raise ValueError("Hash mismatch: data integrity validation failed")
```

- El contenido del archivo se procesa línea por línea, separando las claves y valores, y almacenándolos en un diccionario `data`.
- Se concatenan los valores de las claves en el orden especificado y se genera un hash MD5 de la cadena concatenada.
- Se valida el hash generado contra el hash proporcionado en el archivo. Si no coinciden, se lanza una excepción.

#### Almacenamiento en DynamoDB

```python
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
    table = dynamodb_client.Table('ai-technical-test-<userName>')
    table.put_item(Item=item)
```

- Se prepara un diccionario `item` que contiene los datos a almacenar en DynamoDB, incluyendo un timestamp.
- Se obtiene la referencia a la tabla DynamoDB y se inserta el ítem en la tabla.

#### Eliminación del Archivo de S3 y Retorno de la Respuesta

```python
    # Eliminar el archivo de S3
    s3_client.delete_object(Bucket=bucket, Key=key)
    
    return {
        'statusCode': 200,
        'body': json.dumps('File processed and deleted successfully')
    }
```

- Se elimina el archivo del bucket S3.
- La función retorna una respuesta indicando que el archivo fue procesado y eliminado exitosamente.


###  3. Configuración de la Lambda Function
Crear una Lambda Function: Crear una Lambda Function en AWS y pegar el código anterior en el editor de la Lambda.
- Configurar el trigger de S3: En la configuración de la Lambda Function, agregar un trigger de S3 para que la func ión se ejecute automáticamente cuando se suba un archivo al bucket especificado.
- Permisos: Asegurarse de que la Lambda Function tenga permisos necesarios para leer del bucket S3, escribir en DynamoDB y eliminar objetos de S3.

## 4. Pruebas Unitarias

Se deben crear pruebas unitarias para asegurar que el código funciona correctamente y cumple con el requisito de al menos un 70% de cobertura de pruebas.

![Codigo pruebas unitarias ](https://github.com/jelambrar96/prueba_ingeniero_datos_bancolombia/blob/master/lambda/test_lambda_function.py)

