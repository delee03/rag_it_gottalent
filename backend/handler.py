import json
import boto3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Khởi tạo Bedrock client
bedrock_agent_client = boto3.client("bedrock-agent-runtime")
dynamodb_client = boto3.client("dynamodb")

DYNAMODB_TABLE_NAME = "UserInputTable"  # Tên bảng DynamoDB
KNOWLEDGE_BASE_ID = "FAMVRWKZRX"
MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"

# Hàm lưu vào DynamoDB
def save_to_dynamodb(user_input, timestamp):
    """Lưu dữ liệu vào DynamoDB"""
    try:
        dynamodb_client.put_item(
            TableName=DYNAMODB_TABLE_NAME,
            Item={
                'timestamp': {'S': timestamp},
                'user_input': {'S': user_input}
            }
        )
    except Exception as e:
        logger.error(f"Error saving to DynamoDB: {str(e)}")

# Hàm truy vấn Knowledge Base từ AWS Bedrock
def retrieve_and_generate(user_request, kb_id="FAMVRWKZRX"):
    """Query the Knowledge Base via AWS Bedrock API."""
    payload = {
        "text": user_request,  # Chỉ gửi user_input tới Bedrock
    }

    try:
        response = bedrock_agent_client.retrieve_and_generate(
            input=payload,
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": kb_id,
                    "modelArn": MODEL_ARN
                }
            }
        )
        output = response["output"]["text"]
        citations = response.get("citations", [])
        retrieved_references = [
            ref["retrievedReferences"] for ref in citations if "retrievedReferences" in ref
        ]
        return output, retrieved_references

    except Exception as e:
        logger.error(f"Error calling Retrieve and Generate API: {str(e)}")
        return None, None

# Hàm xử lý yêu cầu và lưu kết quả vào DynamoDB
def extract_and_store(event, context):
    """Xử lý yêu cầu và lưu kết quả vào DynamoDB"""
    logger.info("Processing request")

    try:
        # Lấy user_input từ frontend
        body = json.loads(event['body'])
        user_input = body.get("user_input", "")

        if not user_input:
            raise ValueError("User input is required.")

        # Truy vấn Knowledge Base
        kb_output, retrieved_references = retrieve_and_generate(user_input)

        # Lưu vào DynamoDB
        timestamp = datetime.now().isoformat()
        save_to_dynamodb(user_input, timestamp)

        # Trả về kết quả
        return {
            'statusCode': 200,
            'headers': {
            "Access-Control-Allow-Origin": "*",  # Các domain được phép truy cập
            "Access-Control-Allow-Methods": "OPTIONS,POST",# Các phương thức được phép
            "Access-Control-Allow-Headers": "Content-Type,Authorization", # Các header được phép
            },
            'body': json.dumps({
                'status': 'success',
                'user_input': user_input,
                'kb_output': kb_output,
                'retrieved_references': retrieved_references
            })
        }
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({"status": "error", "message": str(e)})
        }
