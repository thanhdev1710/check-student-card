import re

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
        "mssv": mssv.group(0) if mssv else "Không tìm thấy MSSV",
        "name": name or "Không tìm thấy họ tên",
        "dob": dob.group(0) if dob else "Không tìm thấy ngày sinh",
        "major": major.group(1).strip() if major else "Không tìm thấy ngành",
        "course": course.group(1).strip() if course else "Không tìm thấy khoá học"
    }
