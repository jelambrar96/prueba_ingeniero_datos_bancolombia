import os
import unittest

from unittest.mock import patch, MagicMock
from lambda_function import lambda_handler

class TestLambdaFunction(unittest.TestCase):

    @patch('lambda_function.s3_client')
    @patch('lambda_function.dynamodb_client')
    def test_lambda_handler(self, mock_dynamodb_client, mock_s3_client) -> None:
        """test_lambda_handler"""
        # Configurar el mock del evento de S3
        event = {
            'Records': [{
                's3': {
                    'bucket': {'name': 'test-bucket'},
                    'object': {'key': 'test-file.txt'}
                }
            }]
        }

        # Configurar el contenido del archivo S3
        mock_s3_client.get_object.return_value = {
            'Body': MagicMock(
                read=MagicMock(
                    return_value=b'totalContactoClientes=250\nmotivoReclamo=25\nmotivoGarantia=10\nmotivoDuda=100\nmotivoCompra=100\nmotivoFelicitaciones=7\nmotivoCambio=8\nhash=2f941516446dce09bc2841da60bf811f'
                )
            )
        }

        # Llamar a la función Lambda handler
        response = lambda_handler(event, None)

        # Verificar que la función Lambda respondió con éxito
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('File processed and deleted successfully', response['body'])

        # Verificar que los métodos esperados fueron llamados
        mock_s3_client.get_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test-file.txt'
        )
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test-file.txt'
        )
        mock_dynamodb_client.Table.return_value.put_item.assert_called_once()

if __name__ == '__main__':
    unittest.main()