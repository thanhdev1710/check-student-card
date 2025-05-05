from fastapi import UploadFile
import easyocr
from process_text import extract_info
from process_img import enhance_image, is_image_clear, read_image, resize_if_needed
from barcode import read_barcode_from_image
# Init EasyOCR
reader = easyocr.Reader(['vi'], gpu=False, verbose=False)


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

    # Đọc mã vạch từ ảnh đã xử lý
    barcode_results = read_barcode_from_image(image)  # dùng ảnh đã enhance
    barcode_mssv = None
    for result in barcode_results:
        if result["type"] in ["CODE128", "EAN13", "CODE39"]:  # tuỳ loại mã vạch
            barcode_mssv = result["data"]
            break

    # So sánh MSSV OCR và Barcode (nếu cả hai cùng có)
    ocr_mssv = info.get("mssv")
    if barcode_mssv and ocr_mssv and "Không tìm thấy" not in ocr_mssv:
        if barcode_mssv != ocr_mssv:
            return {
                "error": f"MSSV không khớp giữa OCR ({ocr_mssv}) và mã vạch ({barcode_mssv}). Vui lòng kiểm tra lại ảnh!"
            }

    missing = [k for k, v in info.items() if "Không tìm thấy" in v]
    if missing:
        return {"error": f"Thiếu thông tin: {', '.join(missing)}. Vui lòng kiểm tra lại ảnh!"}

    # Gộp kết quả trả về
    return {
        "texts": texts,
        "info": info,
        "barcode_mssv": barcode_mssv
    }
