import requests
import base64

# Đọc ảnh và chuyển thành base64
with open("image.jpg", "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

# Gửi ảnh và input của người dùng đến Lambda
url = "https://<API_URL>/extract"
data = {
    "image": image_base64,
    "user_input": "User's question or input"
}
response = requests.post(url, json=data)

# Xử lý kết quả trả về từ Lambda
result = response.json()
print(result)
