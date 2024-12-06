document
    .getElementById("submitButton")
    .addEventListener("click", async function () {
        const imageInput = document.getElementById("imageInput").files[0];
        const userInput = document.getElementById("userInput").value;
        const responseText = document.getElementById("responseText");

        const formData = new FormData();

        if (imageInput) {
            formData.append("image", await toBase64(imageInput));
        }

        formData.append("text", userInput);

        // Gửi dữ liệu tới API Lambda (chú ý thay API_ENDPOINT bằng endpoint thực tế của bạn)
        const API_ENDPOINT =
            "https://xyz123456.execute-api.us-east-1.amazonaws.com/dev/extract";

        const response = await fetch(API_ENDPOINT, {
            method: "POST",
            body: formData,
        });

        const result = await response.json();
        responseText.textContent = JSON.stringify(result, null, 2);
    });

// Convert image file to base64
function toBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result.split(",")[1]); // Remove the data URL prefix
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}
