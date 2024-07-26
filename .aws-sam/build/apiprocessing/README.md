# Product Inventory API

This project is an AWS Lambda function for managing product inventory using DynamoDB. It includes API endpoints for CRUD operations and inventory management.

## Setup

1. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```

2. Deploy using AWS SAM:
    ```sh
    sam deploy --guided
    ```

3. Run tests:
    ```sh
    python -m unittest discover tests
    ```

## API Endpoints

- `GET /status`: Check service status
- `GET /products`: Get all products
- `GET /products/{productId}`: Get a product by ID
- `POST /products`: Create a new product
- `PUT /products`: Update a product
- `DELETE /products`: Delete a product
- `GET /inventory`: Get total inventory
- `GET /inventory/{productId}`: Get inventory for a product by ID
