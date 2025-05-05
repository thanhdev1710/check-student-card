from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import easyocr
import cv2
import numpy as np
import re

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init EasyOCR
reader = easyocr.Reader(['vi'], gpu=False, verbose=False)

@app.get("/ping")
async def ping():
    return {"message": "pong"}

# ----- Image processing utilities -----
def read_image(uploaded_file: UploadFile) -> np.ndarray | None:
    try:
        image_data = uploaded_file.file.read()
        img_array = np.frombuffer(image_data, dtype=np.uint8)
        return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except:
        return None

def resize_if_needed(image: np.ndarray, max_dim: int = 800) -> np.ndarray:
    h, w = image.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        return cv2.resize(image, (int(w * scale), int(h * scale)))
    return image

def is_image_clear(image: np.ndarray, threshold: float = 120) -> bool:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    return sharpness >= threshold

def enhance_image(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 15, 10
    )

def normalize_whitespace(text: str) -> str:
    """
    Hàm chuẩn hóa khoảng trắng: thay thế tất cả khoảng trắng liên tiếp bằng một khoảng trắng duy nhất,
    và loại bỏ khoảng trắng thừa ở đầu và cuối chuỗi.
    """
    return re.sub(r'\s+', ' ', text).strip()

# ----- OCR and Extraction -----
def extract_info(texts: list[str]) -> dict:
    joined_text = ' '.join(texts)
    
    mssv = re.search(r'\b\d{10}\b', joined_text)
    dob = re.search(r'\b\d{2}[-/]\d{2}[-/]\d{4}\b', joined_text)
    major = re.search(r'Ngành[:\s]*([A-ZÀ-Ỹa-zà-ỹ ]{3,})(?=\s*Khoá học|$)', joined_text)
    course = re.search(r'Khoá học[:\s]*([\d]{4}[-–][\d]{4})', joined_text, re.IGNORECASE)

    name = None
    name_patterns = [
        r'(?:THẺ SINH VIÊN)[\s:]*([A-ZÀ-Ỹ][a-zà-ỹ]+(?: [A-ZÀ-Ỹa-zà-ỹ]+){1,})',
        r'\b([A-ZÀ-Ỹ][a-zà-ỹ]{1,15}(?: [A-ZÀ-Ỹa-zà-ỹ]{1,15}){1,})\b'
    ]
    for pattern in name_patterns:
        match = re.search(pattern, joined_text)
        if match:
            candidate = re.sub(r'\b(Ngày|sinh|Ngày sinh)\b.*', '', match.group(1)).strip()
            if len(candidate.split()) >= 2:
                name = candidate
                break

    return {
        "MSSV": mssv.group(0) if mssv else "Không tìm thấy MSSV",
        "Họ tên": name or "Không tìm thấy họ tên",
        "Ngày sinh": dob.group(0) if dob else "Không tìm thấy ngày sinh",
        "Ngành": major.group(1).strip() if major else "Không tìm thấy ngành",
        "Khoá học": course.group(1).strip() if course else "Không tìm thấy khoá học"
    }

def process_ocr(file: UploadFile) -> dict:
    image = read_image(file)
    if image is None:
        return {"error": "Không thể đọc ảnh"}

    image = resize_if_needed(image)

    if not is_image_clear(image):
        return {"error": "Ảnh quá mờ hoặc ánh sáng kém, vui lòng chụp lại!"}

    processed = enhance_image(image)
    try:
        ocr_results = reader.readtext(processed, detail=1)
    except Exception as e:
        return {"error": f"Lỗi OCR: {str(e)}"}

    texts = [text for (_, text, conf) in ocr_results if conf > 0.4]
    info = extract_info(texts)

    missing = [k for k, v in info.items() if "Không tìm thấy" in v]
    if missing:
        return {"error": f"Thiếu thông tin: {', '.join(missing)}. Vui lòng kiểm tra lại ảnh!"}

    return {"texts": texts, "info": info}

@app.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    result = process_ocr(file)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result
