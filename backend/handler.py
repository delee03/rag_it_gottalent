import json
import base64
import boto3
from PIL import Image
import pytesseract
import io
import logging
from datetime import datetime
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Khởi tạo Bedrock client
bedrock_client = boto3.client("bedrock-runtime")
bedrock_agent_client = boto3.client("bedrock-agent-runtime")
KNOWLEDGE_BASE_ID = "VIBMDAEXUG"
MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
dynamodb_client = boto3.client("dynamodb")

# Đảm bảo rằng đường dẫn Tesseract được cấu hình đúng
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  #Path to Tesseract OCR executable

DYNAMODB_TABLE_NAME = "UserInputTable"  # Tên bảng DynamoDB của bạn

# Hàm lưu vào DynamoDB
def save_to_dynamodb(extracted_text, user_input, timestamp):
    """Lưu dữ liệu vào DynamoDB"""
    try:
        dynamodb_client.put_item(
            TableName=DYNAMODB_TABLE_NAME,
            Item={
                'timestamp': {'S': timestamp},
                'user_input': {'S': user_input},
                'extracted_text': {'S': extracted_text if extracted_text else ''},
                'image_received': {'BOOL': extracted_text is not None}
            }
        )
    except Exception as e:
        logger.error(f"Error saving to DynamoDB: {str(e)}")


# Hàm truy vấn Knowledge Base từ AWS Bedrock
def retrieve_and_generate(user_request, extracted_text=None, kb_id="VIBMDAEXUG"):
    """Query the Knowledge Base via AWS Bedrock API."""
    combined_input = user_request if user_request else ""
    if extracted_text:
        combined_input += f"\nExtracted Text: {extracted_text}"  # Add OCR text if available

    payload = {
        "text": combined_input,  # Send the combined text to Bedrock
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
    """Xử lý yêu cầu, trích xuất văn bản từ ảnh, và lưu vào DynamoDB"""
    logger.info("Processing request")

    try:
        # Kiểm tra dữ liệu đầu vào
        if not event.get('body'):
            return {
                'statusCode': 400,
                'body': json.dumps({"status": "error", "message": "No data received or data is empty."})
            }

        body = json.loads(event['body'])
        image_data = body.get("image", "")
        user_input = body.get("user_input", "")

        if not image_data or not user_input:
            return {
                'statusCode': 400,
                'body': json.dumps({"status": "error", "message": "Missing image or user input."})
            }

        # Giải mã base64 thành ảnh
        image = Image.open(io.BytesIO(base64.b64decode(image_data)))

        # Trích xuất văn bản từ ảnh (OCR)
        extracted_text = pytesseract.image_to_string(image)
        logger.info(f"Extracted text: {extracted_text}")

        # Truy vấn Knowledge Base
        kb_output, retrieved_references = retrieve_and_generate(user_input or None, extracted_text)

        # Lưu vào DynamoDB
        timestamp = datetime.now().isoformat()
        save_to_dynamodb(extracted_text, user_input, timestamp)

        # Trả về kết quả
        response = {
            'statusCode': 200,
            'body': json.dumps({
                "status": "success",
                "message": "Processed successfully.",
                "extracted_text": extracted_text,
                "kb_output": kb_output,
                # "retrieved_references": retrieved_references
            })
        }
        return response

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({"status": "error", "message": str(e)})
        }
