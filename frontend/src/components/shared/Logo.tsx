import { Link } from "react-router-dom";
import { Typography } from "@mui/material";

const Logo = () => {
    return (
        <div
            style={{
                display: "flex",
                marginRight: "auto",
                alignItems: "center",
                gap: "15px",
            }}
        >
            {/* <Link to="/" className=" !bg-white">
                <img
                    src="HDBANK HACKATHON 2024-Photoroom.png"
                    alt="HDBANK HACKATHON 2024"
                    width={"100px"}
                    height={"50px"}
                />
            </Link> */}
            <Typography
                sx={{
                    display: { md: "block", sm: "none", xs: "none" },
                    mr: "auto",
                    fontWeight: "800",
                    textShadow: "2px 2px 20px #000",
                    transition: "all .5s",
                    ":hover": {
                        color: "purple",
                        fontSize: "24px",
                        filter: "drop-shadow(5px 5px 20px rgb(255, 0, 255))",
                    },
                }}
            >
                <img
                    src="HDBANK HACKATHON 2024-Photoroom.png"
                    alt="HDBANK HACKATHON 2024"
                    width={"200px"}
                    height={"80px"}
                />
                {/* <span style={{ fontSize: "20px" }}>TryHard </span>- GPT */}
            </Typography>
        </div>
    );
};

export default Logo;
