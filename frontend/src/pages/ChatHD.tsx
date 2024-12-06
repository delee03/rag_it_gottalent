import React, { useState, useEffect } from "react";
import {
    Avatar,
    Box,
    Button,
    TextField,
    IconButton,
    Typography,
    CircularProgress,
} from "@mui/material";
import { IoMdSend } from "react-icons/io";
import { VscLoading } from "react-icons/vsc";

// Custom hook useDebounce
function useDebounce(value: string, delay: number): string {
    const [debouncedValue, setDebouncedValue] = useState(value);

    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        return () => {
            clearTimeout(handler);
        };
    }, [value, delay]);

    return debouncedValue;
}

// Chuyển đổi file thành Base64 và loại bỏ phần đầu
function toBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            // Chỉ lấy phần dữ liệu Base64, bỏ phần prefix 'data:image/png;base64,'
            const base64String = reader.result as string;
            const base64Data = base64String.split(",")[1]; // Lấy phần sau dấu phẩy
            resolve(base64Data); // Trả về chỉ phần dữ liệu Base64
        };
        reader.onerror = (error) => reject(error);
        reader.readAsDataURL(file);
    });
}

const ChatHD = () => {
    const [textInput, setTextInput] = useState<string>("");
    const [imageInput, setImageInput] = useState<File | null>(null);
    const [response, setResponse] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const debouncedTextInput = useDebounce(textInput, 500); // Delay 500ms cho input

    const handleTextInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setTextInput(e.target.value);
    };

    const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files ? e.target.files[0] : null;
        if (file) {
            setImageInput(file);
        }
    };

    const handleSendMessage = async () => {
        if (loading) return;

        setLoading(true);
        const formData = new FormData();

        // Thêm văn bản vào FormData
        if (textInput.trim()) {
            formData.append("user_input", textInput);
        }

        // Nếu có ảnh, chuyển đổi và thêm vào FormData
        if (imageInput) {
            try {
                const base64Data = await toBase64(imageInput); // Mã hóa ảnh thành Base64 và loại bỏ prefix
                formData.append("image", base64Data);
                console.log("Image added to formData", base64Data); // Hiển thị dữ liệu ảnh Base64
            } catch (error) {
                console.error("Error converting image to Base64", error);
            }
        }

        // Gửi dữ liệu tới API
        const API_ENDPOINT = "http://localhost:3000/dev/extract";
        try {
            const response = await fetch(API_ENDPOINT, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    image: imageInput ? await toBase64(imageInput) : null, // Gửi ảnh nếu có
                    user_input: textInput, // Gửi văn bản
                }),
            });

            if (response.ok) {
                const result = await response.json();
                console.log(result);

                // Cập nhật phản hồi lên giao diện
                setResponse(JSON.stringify(result, null, 2));
            } else {
                setResponse("Error: Unable to fetch response.");
            }
        } catch (error) {
            console.error("Error sending request", error);
            setResponse("Error: Failed to send request.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box sx={{ padding: 2, margin: "0 auto" }}>
            <Box sx={{ marginBottom: 2 }}>
                <Typography variant="h6">Chat with API</Typography>
            </Box>

            {/* <TextField
                label="Enter your question"
                fullWidth
                variant="outlined"
                value={textInput}
                onChange={handleTextInputChange}
                margin="normal"
            /> */}
            <input
                id="userInput"
                placeholder="Ask a question"
                className="bg-white !w-full py-6 px-40 rounded-lg"
                type="text"
                style={{
                    padding: "20px 100px",
                    width: "70%",
                    fontSize: 20,
                    borderRadius: 20,
                }}
                value={textInput}
                onChange={handleTextInputChange}
            />

            {/* Input ảnh */}
            <input
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                style={{ marginBottom: "16px" }}
            />

            {/* Hiển thị tên file ảnh */}
            {imageInput && (
                <Typography variant="body2">
                    Selected Image: {imageInput.name}
                </Typography>
            )}

            <Box sx={{ display: "flex", alignItems: "center" }}>
                <Button
                    variant="contained"
                    onClick={handleSendMessage}
                    disabled={loading}
                    sx={{ marginRight: 2 }}
                >
                    {loading ? (
                        <CircularProgress size={24} color="inherit" />
                    ) : (
                        <IoMdSend />
                    )}
                    Send
                </Button>
            </Box>

            {/* Hiển thị phản hồi từ API */}
            {response && (
                <Box
                    sx={{
                        marginTop: 2,
                        padding: 2,
                        color: "black",
                        backgroundColor: "#f4f4f4",
                    }}
                >
                    <Typography variant="body2">
                        Response: {response}
                    </Typography>
                </Box>
            )}
        </Box>
    );
};

export default ChatHD;
