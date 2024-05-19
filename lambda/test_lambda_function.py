"""Module to testing"""
import os
import unittest

from unittest.mock import patch, MagicMock

import lambda_function
# from lambda_function import lambda_handler

MY_AWS_ACCESS_KEY_ID = os.environ['MY_AWS_ACCESS_KEY_ID']
MY_AWS_SECRET_ACCESS_KEY = os.environ['MY_AWS_SECRET_ACCESS_KEY']
MY_AWS_REGION = os.environ['MY_AWS_REGION']

environment_condition = (not MY_AWS_ACCESS_KEY_ID is None) \
    and (not MY_AWS_SECRET_ACCESS_KEY is None) and (not MY_AWS_REGION is None)

AWS_DINAMODB_TABLE = os.environ['AWS_DINAMODB_TABLE']
AWS_S3_BUCKET = os.environ['AWS_S3_BUCKET']

class TestLambdaFunction(unittest.TestCase):
    """
    class to testing
    """

    @patch('lambda_function.s3_client')
    @patch('lambda_function.dynamodb_client')
    def test_lambda_handler(self, mock_dynamodb_client, mock_s3_client) -> None:
        """test_lambda_handler"""
        # Configurar el mock del evento de S3
        event = {
            'Records': [{
                's3': {
                    'bucket': {'name': AWS_S3_BUCKET},
                    'object': {'key': 'test-file.txt'}
                }
            }]
        }

        # Configurar el contenido del archivo S3
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
                    )                )
            )
        }

        # Llamar a la función Lambda handler
        response = lambda_function.lambda_handler(event, None)

        # Verificar que la función Lambda respondió con éxito
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('File processed and deleted successfully', response['body'])

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

if __name__ == '__main__':
    unittest.main()
