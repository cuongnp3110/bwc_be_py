import json
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
import os
import logging

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get the table name from the environment variable
table_name = os.getenv('TABLE_NAME')

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_table = dynamodb.Table(table_name)

status_check_path = '/status'
inventory_path = '/inventory'
products_path = '/products'
orders_path = '/orders'

def lambda_handler(event, context):
    print('Request event: ', event)
    response = None

    try:
        http_method = event.get('httpMethod')
        path = event.get('path')
        
        logger.info(f' Path: {path}')

        if http_method == 'GET' and path == status_check_path:
            response = build_response(200, 'Service is operational')
            
        elif http_method == 'GET' and path == products_path:
            response = get_all_products()
            
        elif http_method == 'GET' and path.startswith(products_path):
            product_id = int(path[len(products_path)+1:])
            response = get_products(product_id)
            
        elif http_method == 'POST' and path == products_path:
            response = save_product(json.loads(event['body']))
            
        elif http_method == 'PUT' and path == products_path:
            body = json.loads(event['body'])
            response = modify_product(body['productId'], body['updateKey'], body['updateValue'])
            
        elif http_method == 'DELETE' and path == products_path:
            body = json.loads(event['body'])
            response = delete_product(body['productId'])
            
        elif http_method == 'GET' and path == inventory_path:
            response = get_total_inventory()
            
        elif http_method == 'GET' and path.startswith(inventory_path):
            product_id = int(path[len(inventory_path)+1:])
            response = get_inventory(product_id)
            
        else:
            response = build_response(404, '404 Not Found')

    except Exception as e:
        print('Error:', e)
        response = build_response(400, 'Error processing request')

    return response

def get_products(product_id):
    try:
        print(f'Fetching product with productId: {product_id}')
        response = dynamodb_table.get_item(Key={'productId': product_id})
        print('DynamoDB response:', response)
        return build_response(200, response.get('Item'))
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

def get_all_products():
    try:
        scan_params = {
            'TableName': dynamodb_table.name
        }
        return build_response(200, scan_dynamo_records(scan_params, []))
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

def get_inventory(product_id):
    try:
        print(f'Fetching product with productId: {product_id}')
        
        response = dynamodb_table.get_item(
            Key={'productId': product_id},
            ProjectionExpression ='stockLevel'
        )
        print('DynamoDB response:', response)
        return build_response(200, response.get('Item'))
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])
        
def get_total_inventory():
    try:
        scan_params = {
            'TableName': dynamodb_table.name,
            'ProjectionExpression': 'stockLevel'
        }
        
        total_stock_level = 0
        response = dynamodb_table.scan(**scan_params)
        
        # Iterate over the items and sum the stockLevel values
        for item in response.get('Items', []):
            stock_level = int(item.get('stockLevel', 0))
            total_stock_level += stock_level

        # Handle pagination if necessary
        while 'LastEvaluatedKey' in response:
            scan_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = dynamodb_table.scan(**scan_params)
            
            for item in response.get('Items', []):
                stock_level = int(item.get('stockLevel', 0))
                total_stock_level += stock_level
                
        return build_response(200, {'inventory': total_stock_level})
        
    except ClientError as e:
        logger.error(f'Error fetching all products: {e}')
        return build_response(400, e.response['Error']['Message'])

def scan_dynamo_records(scan_params, item_array):
    response = dynamodb_table.scan(**scan_params)
    item_array.extend(response.get('Items', []))

    if 'LastEvaluatedKey' in response:
        scan_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
        return scan_dynamo_records(scan_params, item_array)
    else:
        return {'products': item_array}

def save_product(request_body):
    try:
        dynamodb_table.put_item(Item=request_body)
        body = {
            'Operation': 'SAVE',
            'Message': 'SUCCESS',
            'Item': request_body
        }
        return build_response(200, body)
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

def modify_product(product_id, update_key, update_value):
    try:
        response = dynamodb_table.update_item(
            Key={'productId': product_id},
            UpdateExpression=f'SET {update_key} = :value',
            ExpressionAttributeValues={':value': update_value},
            ReturnValues='UPDATED_NEW'
        )
        body = {
            'Operation': 'UPDATE',
            'Message': 'SUCCESS',
            'UpdatedAttributes': response
        }
        return build_response(200, body)
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

def delete_product(product_id):
    try:
        response = dynamodb_table.delete_item(
            Key={'productId': product_id},
            ReturnValues='ALL_OLD'
        )
        body = {
            'Operation': 'DELETE',
            'Message': 'SUCCESS',
            'Item': response
        }
        return build_response(200, body)
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Check if it's an int or a float
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        # Let the base class default method raise the TypeError
        return super(DecimalEncoder, self).default(obj)

def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }
