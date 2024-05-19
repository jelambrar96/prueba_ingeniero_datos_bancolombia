import boto3
import os

def update_lambda_function(function_name, zip_file_path):
    """
    Actualiza el código de una función Lambda.

    :param function_name: Nombre de la función Lambda
    :param zip_file_path: Ruta al archivo ZIP que contiene el código actualizado
    """
    # Crear el cliente de Lambda
    lambda_client = boto3.client('lambda')

    # Leer el archivo ZIP
    with open(zip_file_path, 'rb') as zip_file:
        zip_data = zip_file.read()

    # Actualizar el código de la función Lambda
    response = lambda_client.update_function_code(
        FunctionName=function_name,
        ZipFile=zip_data
    )

    return response

if __name__ == "__main__":
    # Configuración
    FUNCTION_NAME = os.getenv('LAMBDA_FUNCTION_NAME')  # Nombre de tu función Lambda
    ZIP_FILE_PATH = os.getenv('ZIP_FILE_PATH')  # Ruta al archivo ZIP

    # Validar que el archivo ZIP existe
    if not os.path.exists(ZIP_FILE_PATH):
        print(f"Error: El archivo {ZIP_FILE_PATH} no existe.")
        exit(1)

    # Actualizar la función Lambda
    try:
        response = update_lambda_function(FUNCTION_NAME, ZIP_FILE_PATH)
        print(f"Código de la función Lambda '{FUNCTION_NAME}' actualizado exitosamente.")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error actualizando la función Lambda: {e}")
