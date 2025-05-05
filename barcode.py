from pyzbar.pyzbar import decode
import cv2

def read_barcode_from_image(image) -> list:
    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    barcodes = decode(gray_img)

    results = []
    for barcode in barcodes:
        try:
            barcode_data = barcode.data.decode("utf-8")
        except UnicodeDecodeError:
            barcode_data = barcode.data.decode("latin-1")  # fallback cho mã bị lỗi utf-8

        results.append({
            "type": barcode.type,
            "data": barcode_data,
            "rect": barcode.rect
        })

    return results
