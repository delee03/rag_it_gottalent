document
    .getElementById("submitButton")
    .addEventListener("click", async function () {
        const imageInput = document.getElementById("imageInput").files[0];
        const userInput = document.getElementById("userInput").value;
        const responseText = document.getElementById("responseText");
        let imageData = null;
        // Tạo FormData
        const formData = new FormData();

        // Nếu có ảnh, chuyển đổi và thêm vào formData
        if (imageInput) {
            imageData = await toBase64(imageInput);
            formData.append("image", imageData);
            console.log("Image added to formData", imageData);
        }

        // Nếu có text, thêm vào formData
        if (userInput) {
            formData.append("user_input", userInput);
            console.log("User input added to formData", userInput);
        }

        // Tạo đối tượng JSON chứa dữ liệu
        const data = {
            image: imageData,
            user_input: userInput,
        };

        // Kiểm tra nội dung FormData trước khi gửi
        console.log("FormData contents:", data);

        // Gửi dữ liệu tới API Lambda
        const API_ENDPOINT = "http://localhost:3000/dev/extract";
        try {
            const response = await fetch(API_ENDPOINT, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json", // Gửi dữ liệu dưới dạng JSON
                },
                body: JSON.stringify(data),
            });

            if (response.ok) {
                const result = await response.json();
                console.log(result);

                // Cập nhật phản hồi lên giao diện
                responseText.textContent = JSON.stringify(result, null, 2);
            } else {
                console.error("Error in response:", response.statusText);
                responseText.textContent = "Error: " + response.statusText;
            }
        } catch (error) {
            console.error("Error while sending formData:", error);
        }
    });

// Convert image file to base64
function toBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result.split(",")[1]); // Loại bỏ phần tiền tố của Base64
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}
