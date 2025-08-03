from utils.ocr_service import recognize_pdf_text
import os
if __name__ == "__main__":
    # 示例用法
    try:
        print("=== PDF OCR识别测试 ===")
        
        # 测试PDF OCR
        pdf_path = "其他.pdf"  # 替换为你的PDF路径
        if os.path.exists(pdf_path):
            print(f"找到PDF文件: {pdf_path}")
            
            # 方法1: 直接获取识别结果
            page_texts = recognize_pdf_text(pdf_path)
            print("\n=== PDF识别结果 ===")
            for i, page_text in enumerate(page_texts):
                print(f"{i + 1} 页: {page_text}")
        else:
            print(f"PDF文件不存在: {pdf_path}")
    except Exception as e:
        print(f"发生错误: {str(e)}")

