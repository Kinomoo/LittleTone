# services/__init__.py

# 1. 從各個子模組導入核心函式或類別
from .chat_service import ChatService, get_little_tone_final_response
from .image_service import ImageService

# 2. 正式啟用 RAG 服務，將註解移除
from .rag_service import retrieve_social_knowledge

# 3. 定義對外公開的接口清單
__all__ = [
    "ChatService",
    "get_little_tone_final_response",
    "ImageService",
    "retrieve_social_knowledge"  # 確保這行有加入
]