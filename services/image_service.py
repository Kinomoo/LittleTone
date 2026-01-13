import base64
from PIL import Image
import io

class ImageService:
    def encode_image_to_base64(self, image_path):
        """
        將本地圖片路徑轉換為 Base64 字串
        """
        try:
            with Image.open(image_path) as img:
                # 縮放圖片以節省 Token (GPT-4o 建議尺寸)
                img.thumbnail((1024, 1024))
                
                buffered = io.BytesIO()
                # 轉成 RGB 並儲存為 JPEG
                img.convert("RGB").save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                return img_str
        except Exception as e:
            print(f"圖片編碼出錯: {e}")
            return None