import qrcode
import random
from urllib.parse import urlencode

base_url = "https://hashswim.github.io/perfume_mobile_page/"

def generate_qr_code(idx=None, save_path=None):
    """
    QR 코드를 생성하고 이미지로 저장하는 함수
    
    Args:
        idx: QR 코드에 포함할 인덱스 (None이면 랜덤 생성)
        save_path: 저장할 파일 경로 (None이면 기본 경로 사용)
    
    Returns:
        str: 생성된 QR 코드 이미지 파일 경로
    """
    # 0~7 사이의 인덱스를 자동으로 할당
    if idx is None:
        idx = random.randint(0, 7)
    
    print(f"자동 할당된 idx: {idx}")

    params = {"idx": idx}
    full_url = f"{base_url}?{urlencode(params)}"
    print("생성할 URL:", full_url)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(full_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    if save_path is None:
        save_path = f"qrcode_idx_{idx}.png"
    
    img.save(save_path)
    print(f"QR 코드가 '{save_path}'로 저장되었습니다.")
    return save_path

# 기존 코드 (메인 실행용)
if __name__ == "__main__":
    # 0~7 사이의 인덱스를 자동으로 할당
    idx = random.randint(0, 7)  # 또는 random.randrange(0, 8)
    print(f"자동 할당된 idx: {idx}")

    params = {"idx": idx}
    full_url = f"{base_url}?{urlencode(params)}"
    print("생성할 URL:", full_url)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(full_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"qrcode_idx_{idx}.png")
    print(f"QR 코드가 'qrcode_idx_{idx}.png'로 저장되었습니다.")