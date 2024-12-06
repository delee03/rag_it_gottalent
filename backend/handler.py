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
 pytesseract.pytesseract.tesseract_cmd = "/opt/bin/tesseract"  # Đường dẫn trong Lambda layer

# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  #Path to Tesseract OCR executable



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
        logger.error(f"Error saving to DynamoDB: {e}")
        raise e

# Hàm truy vấn Knowledge Base từ AWS Bedrock
def retrieve_and_generate(user_request, extracted_text=None, kb_id=KNOWLEDGE_BASE_ID):
    """Query the Knowledge Base via AWS Bedrock API."""
    # Tạo đầu vào cho API, kết hợp text từ input người dùng và OCR
    combined_input = user_request if user_request else ""
    if extracted_text:
        combined_input += f"\nExtracted Text: {extracted_text}"  # Thêm văn bản từ OCR (nếu có)

    # Prepare the payload for Retrieve and Generate API
    payload = {
        "text": combined_input,  # Chỉ cần truyền text vào
    }

    # Gọi API Retrieve and Generate
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

        # Phân tích kết quả trả về
        output = response["output"]["text"]
        citations = response.get("citations", [])
        retrieved_references = [
            ref["retrievedReferences"] for ref in citations if "retrievedReferences" in ref
        ]
        return output, retrieved_references

    except Exception as e:
        print(f"Error calling Retrieve and Generate API: {str(e)}")
        return None, None


# Hàm xử lý yêu cầu và lưu kết quả vào DynamoDB
def extract_and_store(event, context):
    """Xử lý yêu cầu, trích xuất văn bản từ ảnh, và lưu vào DynamoDB"""
    logger.info("Processing request")

    try:
        # if not event.get('body'):
        #     return {
        #         'statusCode': 400,
        #         'body': json.dumps({"status": "error", "message": "No data received or data is empty."})
        #     }
        data = sys.stdin.readline()
        if(data):
            print(data)
            parsed_data = json.loads(data)
            print(parsed_data)

        else:
            print("No data received or data is empty.")
            return {
                'statusCode': 400,
                'body': json.dumps({"status": "error", "message": "No data received or data is empty."})
            }
        # Giải mã base64 của ảnh từ frontend
        body = json.loads(event['body'])
        image_data = body.get("image", "")
        user_input = body.get("user_input", "")
        
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
        if kb_output:
            print("Response: ", kb_output)
            if retrieved_references:
                print("References: ", retrieved_references)
        # Trả về kết quả cho frontend
        response = {
            "status": "success",
            "message": "Processed successfully.",
            "extracted_text": extracted_text,
            "kb_output": kb_output,
            "retrieved_references": retrieved_references
        }
    
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({"status": "error", "message": str(e)})
        }
