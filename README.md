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

Para cumplir con las necesidades descritas, vamos a desarrollar una solución en Python utilizando AWS Lambda, S3 y DynamoDB. 

### Componentes
1. **GitHub Actions**: Representa el pipeline de CI/CD que desencadena despliegues.
2. **AWS Lambda**: La función central de procesamiento.
3. **Amazon S3**: Un bucket donde se suben archivos, lo que desencadena la función Lambda.
4. **Amazon DynamoDB**: Una base de datos donde Lambda almacena los datos procesados.

### 1. Configuración de AWS Lambda para activar al subir un archivo a S3

Primero, configuraremos una Lambda Function en AWS que se active automáticamente cuando se suba un archivo al bucket S3. Luego, crearemos el código para la Lambda Function.

###  2. Código de la Lambda Function en Python

[Codigo lambda](https://github.com/jelambrar96/prueba_ingeniero_datos_bancolombia/blob/master/lambda/lambda_function.py)

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

[Codigo pruebas unitarias ](https://github.com/jelambrar96/prueba_ingeniero_datos_bancolombia/blob/master/lambda/test_lambda_function.py)

Este código es un módulo de pruebas unitarias para una función Lambda de AWS escrita en Python. Utiliza la biblioteca `unittest` y `unittest.mock` para probar el comportamiento de la función Lambda sin tener que interactuar realmente con los servicios de AWS. Aquí tienes una explicación detallada del código:

### Importaciones y Configuración Inicial

```python
import os
import unittest
from unittest.mock import patch, MagicMock
import lambda_function

AWS_S3_BUCKET = os.environ['AWS_S3_BUCKET']
```

1. **Importaciones**:
   - `os`: Para acceder a las variables de entorno.
   - `unittest`: Biblioteca estándar de Python para pruebas unitarias.
   - `unittest.mock`: Para crear objetos simulados (`mock`) y parches (`patch`).
   - `lambda_function`: El módulo que contiene la función Lambda a probar.

2. **Variable de Entorno**:
   - `AWS_S3_BUCKET`: Obtiene el nombre del bucket S3 de una variable de entorno.

### Clase de Prueba

```python
class TestLambdaFunction(unittest.TestCase):
    """
    class to testing
    """
```

- **Clase `TestLambdaFunction`**: Hereda de `unittest.TestCase` y contiene métodos de prueba para la función Lambda.

### Método de Prueba

```python
@patch('lambda_function.dynamodb_client')
@patch('lambda_function.s3_client')
def test_lambda_handler(self, mock_dynamodb_client, mock_s3_client) -> None:
    """test_lambda_handler"""
```

- **Decoradores `@patch`**: 
  - `@patch('lambda_function.dynamodb_client')`: Sustituye `dynamodb_client` en `lambda_function` por un objeto simulado.
  - `@patch('lambda_function.s3_client')`: Sustituye `s3_client` en `lambda_function` por un objeto simulado.
- **Parámetros**:
  - `self`: Referencia a la instancia de la clase `TestLambdaFunction`.
  - `mock_dynamodb_client`: Objeto simulado para DynamoDB.
  - `mock_s3_client`: Objeto simulado para S3.

### Configuración del Evento Simulado

```python
event = {
    'Records': [{
        's3': {
            'bucket': {'name': AWS_S3_BUCKET},
            'object': {'key': 'test-file.txt'}
        }
    }]
}
```

- **Evento Simulado**: Representa un evento de S3 que activa la función Lambda. Contiene el nombre del bucket y el nombre del archivo (`test-file.txt`).

### Configuración del Objeto S3 Simulado

```python
mock_s3_client.get_object.return_value = {
    'Body': MagicMock(
        read=MagicMock(
            return_value=(
                b'totalContactoClientes=250\n'
                b'motivoReclamo=25\n'
                b'motivoGarantia=10\n'
                b'motivoDuda=100\n'
                b'motivoCompra=100\n'
                b'motivoFelicitaciones=7\n'
                b'motivoCambio=8\n'
                b'hash=2f941516446dce09bc2841da60bf811f'
            )
        )
    )
}
```

- **`mock_s3_client.get_object.return_value`**: Define el valor de retorno cuando se llama a `get_object` en el cliente S3 simulado.
  - **`'Body'`**: Simula el cuerpo del archivo S3.
  - **`MagicMock`**: Simula el método `read`, que devuelve el contenido del archivo como un byte string.

### Llamada a la Función Lambda y Verificaciones

```python
# Llamar a la función Lambda handler
response = lambda_function.lambda_handler(event, None)

# Verificar que la función Lambda respondió con éxito
self.assertEqual(response['statusCode'], 200)
self.assertIn('File processed and deleted successfully', response['body'])
```

- **Llamada a `lambda_handler`**: Llama a la función Lambda con el evento simulado.
- **Verificaciones**:
  - `self.assertEqual(response['statusCode'], 200)`: Verifica que el código de estado en la respuesta es `200`.
  - `self.assertIn('File processed and deleted successfully', response['body'])`: Verifica que el cuerpo de la respuesta contiene el mensaje esperado.

### Verificaciones de los Métodos Simulados

```python
# Verificar que los métodos esperados fueron llamados
mock_s3_client.get_object.assert_called_once_with(
    Bucket=AWS_S3_BUCKET,
    Key='test-file.txt'
)
mock_s3_client.delete_object.assert_called_once_with(
    Bucket=AWS_S3_BUCKET,
    Key='test-file.txt'
)
mock_dynamodb_client.Table.return_value.put_item.assert_called_once()
```

- **Verificaciones de `mock_s3_client`**:
  - `mock_s3_client.get_object.assert_called_once_with(Bucket=AWS_S3_BUCKET, Key='test-file.txt')`: Verifica que `get_object` fue llamado una vez con los parámetros correctos.
  - `mock_s3_client.delete_object.assert_called_once_with(Bucket=AWS_S3_BUCKET, Key='test-file.txt')`: Verifica que `delete_object` fue llamado una vez con los parámetros correctos.
- **Verificación de `mock_dynamodb_client`**:
  - `mock_dynamodb_client.Table.return_value.put_item.assert_called_once()`: Verifica que `put_item` fue llamado una vez.

### Ejecución de las Pruebas

```python
if __name__ == '__main__':
    unittest.main()
```

- **`unittest.main()`**: Ejecuta las pruebas cuando se ejecuta el script directamente.


## 5. Replicacion 

### 5.1 Creación de la función lambda

1. **Inicia sesión en la Consola de AWS** y navega a **Lambda**.
2. **Haz clic en "Create function"**.
3. Selecciona **"Author from scratch"**.
4. Ingresa un **nombre** para la función (por ejemplo, `ai-technical-test-<userName>`).
5. Selecciona el **Runtime** (Python 3.x).
6. En la sección **Permissions**, selecciona **"Create a new role with basic Lambda permissions"**.
7. Haz clic en **"Create function"**.

#### 5.1.0 Configurar el Bucket de S3 para Activar la Lambda

1. **Ve a la Consola de S3** y selecciona el bucket que deseas usar como trigger.
2. **Ve a la pestaña "Properties"**.
3. Desplázate hacia abajo hasta la sección **"Event notifications"** y haz clic en **"Create event notification"**.
4. **Configura la notificación del evento**:
   - **Event name**: Ingresa un nombre para el evento (por ejemplo, `TriggerLambdaOnUpload`).
   - **Prefix** y **Suffix**: Si deseas que el evento se active solo para archivos específicos, puedes especificar un prefijo y/o sufijo.
   - **Event types**: Selecciona `All object create events` para que la Lambda se ejecute cuando se cree cualquier objeto en el bucket.
   - **Destination**: Selecciona `Lambda function` y luego selecciona la función Lambda que creaste (`ai-technical-test-<userName>`).
5. **Haz clic en "Save"** para crear la notificación del evento.

#### 5.1.1 Configuración de la función lambda

1. Una vez creada la función, desplázate hacia abajo hasta el **Editor de código**.
2. Pega el código de tu función Lambda en el editor de código:

[Codigo lambda](https://github.com/jelambrar96/prueba_ingeniero_datos_bancolombia/blob/master/lambda/lambda_function.py)

#### Cómo Configurar las Variables de Entorno en AWS Lambda

1. Abrir la consola de AWS Lambda y seleccionar la función Lambda correspondiente.
2. Ir a la sección de configuración y buscar el apartado de variables de entorno.
3. Agregar las variables de entorno con los nombres y valores correspondientes (**MY_AWS_ACCESS_KEY_ID**, **MY_AWS_SECRET_ACCESS_KEY**, **MY_AWS_REGION**, **AWS_DINAMO_TABLE**).

De esta manera, el código utilizará las credenciales y el nombre de la tabla DynamoDB almacenadas como variables de entorno, manteniendo las configuraciones de seguridad y facilidad de administración.

## 6. Un poco de CI/CD con github actions

a implementación de CI/CD (Integración Continua y Despliegue Continuo) en este proyecto usando GitHub Actions se hace para automatizar la construcción, pruebas y despliegue del código, asegurando un flujo de trabajo más eficiente y confiable. Aquí te explico cómo se ha aplicado y las ventajas de esta metodología, así como los pasos detallados para hacerlo posible.

### CI/CD con GitHub Actions en el Proyecto

Aplicar CI/CD con GitHub Actions en este proyecto permite automatizar y optimizar el flujo de desarrollo, pruebas y despliegue. Esto no solo mejora la eficiencia y la calidad del código, sino que también facilita una colaboración más efectiva entre los desarrolladores. Al integrar y probar continuamente los cambios, podemos asegurar que el código desplegado sea siempre el más reciente y más estable.

#### Descripción del Flujo de Trabajo

1. **GitHub Actions**: GitHub Actions se utiliza para definir y automatizar el flujo de trabajo (workflow) de CI/CD. Un archivo YAML describe el proceso que se ejecuta en respuesta a eventos específicos, como una solicitud de pull (pull request) o un push al repositorio.

2. **Pipeline de CI/CD**: El pipeline incluye pasos para:
   - **Despliegue del Código**: Actualización del código de la función Lambda.
   - **Pruebas Automáticas**: Ejecución de pruebas unitarias para asegurar que el código es correcto.
   - **Desencadenadores de Eventos**: Automatización del despliegue y pruebas en respuesta a eventos de GitHub.

### Ventajas de Aplicar CI/CD

- **Automatización**: Reduce el trabajo manual y los errores humanos, mejorando la eficiencia y la consistencia.
- **Integración Continua**: Permite detectar errores temprano en el ciclo de desarrollo, facilitando una corrección más rápida y menos costosa.
- **Despliegue Continuo**: Asegura que el código que pasa las pruebas y revisiones se despliega automáticamente, acelerando la entrega de nuevas funcionalidades.
- **Feedback Rápido**: Los desarrolladores reciben retroalimentación inmediata sobre sus cambios, lo que facilita un desarrollo iterativo y mejora la calidad del software.
- **Colaboración Mejorada**: Facilita la colaboración entre equipos al integrar y probar cambios continuamente.

### Pasos para Implementar CI/CD con GitHub Actions

#### Paso 1: Configuración del Repositorio

- **Crear el Repositorio**: Iniciar un nuevo repositorio en GitHub o utilizar uno existente.
- **Añadir Código Fuente**: Subir el código fuente del proyecto, incluyendo la función Lambda y sus dependencias.

#### Paso 2: Configurar GitHub Actions

1. **Crear el Archivo de Workflow**:
   - Crear un directorio `.github/workflows` en el repositorio.
   - Añadir un archivo YAML (por ejemplo, `pr-test-merge-master.yml`) que define el workflow.

2. **Crear las variables de entorno y los secretos**


#### Paso 3: Definir el Workflow de GitHub Actions

```yaml
name: pr-test-merge-master

on:
  pull_request:
    branches:
      - developer
    paths:
      - 'lambda/**'
  workflow_dispatch:

env:
  MY_AWS_ACCESS_KEY_ID: ${{ secrets.MY_AWS_ACCESS_KEY_ID }}
  MY_AWS_SECRET_ACCESS_KEY: ${{ secrets.MY_AWS_SECRET_ACCESS_KEY }}

jobs:
  test_and_merge:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.x'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install boto3

    - name: Install pylint
      run: |
        python -m pip install --upgrade pip
        pip install pylint

    - name: Run pylint
      run: |
        pylint lambda/*.py

    - name: Zip Lambda function code
      run: |
        zip -r lambda_function.zip lambda/

    - name: Update Lambda function code
      env:
        AWS_ACCESS_KEY_ID: ${{ secrets.MY_AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.MY_AWS_SECRET_ACCESS_KEY }}
        AWS_REGION: ${{ secrets.MY_AWS_REGION }}
        LAMBDA_FUNCTION_NAME: ${{ secrets.AWS_LAMBDA }}
        ZIP_FILE_PATH: 'lambda_function.zip'
      run: |
        python update_lambda_function.py

    - name: Run tests
      run: |
        python -m unittest discover -s lambda -p 'test_*.py'

    - name: Configure git
      run: |
        git config --global user.name 'github-actions'
        git config --global user.email 'github-actions@github.com'

    - name: Accept pull request
      if: success()
      env:
        GITHUB_TOKEN: ${{ secrets.GH_TOKEN }}
      run: |
        PR_NUMBER=$(jq --raw-output .number "$GITHUB_EVENT_PATH")
        curl -s -X PUT \
          -H "Authorization: token $GITHUB_TOKEN" \
          -H "Accept: application/vnd.github.v3+json" \
          https://api.github.com/repos/${{ github.repository }}/pulls/${PR_NUMBER}/merge \
          -d '{"commit_title":"Merging PR #${PR_NUMBER}","merge_method":"merge"}'

    - name: Merge to master
      if: success()
      run: |
        git checkout master
        git merge developer
        git push origin master

```

### Explicación del Workflow

1. **Eventos de Activación**:
   - `pull_request`: El workflow se activa cuando se crea o actualiza un pull request hacia la rama `developer`.
   - `workflow_dispatch`: Permite ejecutar el workflow manualmente desde GitHub.

2. **Variables de Entorno**:
   - Definimos las variables de entorno necesarias para las credenciales de AWS y otros parámetros.

3. **Trabajo `test_and_merge`**:
   - **Plataforma**: `ubuntu-latest`.
   - **Pasos**:
     - **Checkout del Código**: Clona el repositorio.
     - **Configuración de Python**: Configura el entorno de Python.
     - **Instalación de Dependencias**: Instala las dependencias necesarias usando `pip`.
     - **Empaquetado del Código**: Crea un archivo ZIP del código de la función Lambda.
     - **Actualización del Código de Lambda**: Ejecuta el script para actualizar la función Lambda en AWS.
     - **Ejecución de Pruebas**: Ejecuta pruebas unitarias para verificar el código.
     - **Configuración de Git**: Configura el usuario de Git para los siguientes pasos.
     - **Aceptación del Pull Request**: Si todas las pruebas pasan, acepta automáticamente el pull request usando la API de GitHub.


```python
print("Gracias!")
```
____

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/jelambrar1)

Made with Love ❤️ by [@jelambrar96](https://github.com/jelambrar96)
