import json
import base64
import io
import boto3
from PIL import Image
import pytesseract
from datetime import datetime

# Khởi tạo Bedrock client
bedrock_client = boto3.client("bedrock-runtime")
KNOWLEDGE_BASE_ID = "VIBMDAEXUG"
MODEL_ARN = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"

# Đảm bảo rằng đường dẫn Tesseract được cấu hình đúng
pytesseract.pytesseract.tesseract_cmd = "/opt/bin/tesseract"

def process_request(event, context):
    # Lấy input từ body của yêu cầu HTTP
    body = json.loads(event['body'])
    image_data = body.get('image', None)  # Dữ liệu ảnh gửi lên
    user_input = body.get('user_input', "")  # Văn bản từ người dùng

    if image_data:
        # Giải mã hình ảnh từ base64
        image_data = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_data))

        # Trích xuất văn bản từ ảnh bằng Tesseract
        extracted_text = pytesseract.image_to_string(image)

        # Kết hợp văn bản người dùng và văn bản trích xuất từ ảnh
        full_text = extracted_text + "\n" + user_input
    else:
        full_text = user_input

    # Gửi văn bản đến Bedrock
    try:
        response = bedrock_client.invoke_model(
            modelId=MODEL_ARN,
            body=full_text,
            contentType="application/json",
            accept="application/json"
        )

        result = response['body'].read().decode('utf-8')
        result_json = json.loads(result)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed the request',
                'result': result_json
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }

def extract_and_store(event, context):
    try:
        # Nhận đầu vào từ yêu cầu HTTP
        body = json.loads(event['body'])
        
        # Kiểm tra nếu có ảnh được gửi lên và nó là base64
        if 'image' in body:
            image_data = body['image']
            
            # Giải mã base64 thành ảnh
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Trích xuất văn bản từ ảnh bằng Tesseract
            extracted_text = pytesseract.image_to_string(image)
        else:
            extracted_text = None
        
        # Kiểm tra nếu có text từ người dùng
        user_input_text = body.get('text', '')

        # Kết hợp cả văn bản từ ảnh và văn bản người dùng
        combined_text = extracted_text + "\n" + user_input_text if extracted_text else user_input_text
        
        # Lưu trữ vào DynamoDB
        timestamp = str(datetime.utcnow())
        table.put_item(
            Item={
                'timestamp': timestamp,
                'user_input': combined_text,
                'extracted_text': extracted_text,
                'image_received': extracted_text is not None
            }
        )

        # Gửi dữ liệu đến AWS Bedrock để xử lý từ knowledge base
        response = bedrock_client.invoke_model(
            modelId=KNOWLEDGE_BASE_ID,
            body=json.dumps({
                "input": combined_text
            }),
            contentType="application/json",
            accept="application/json"
        )

        # Lấy kết quả từ Bedrock
        bedrock_response = json.loads(response['body'].read().decode('utf-8'))
        result = bedrock_response.get('result', 'No response from model')

        # Trả về kết quả cho người dùng
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'extracted_text': extracted_text,
                'combined_text': combined_text,
                'result_from_bedrock': result
            })
        }

    except Exception as e:
        # Xử lý lỗi nếu có
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'message': str(e)
            })
        }