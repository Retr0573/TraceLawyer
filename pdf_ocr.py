#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF OCR识别模块
基于ocr_service.py，提供PDF文件的文字识别功能
"""

from utils.ocr_service import create_ocr_service
import fitz  # PyMuPDF
import os


def recognize_pdf_text(pdf_path, temp_dir=None):
    """
    识别PDF文件中的文字内容
    
    Args:
        pdf_path (str): PDF文件路径
        temp_dir (str, optional): 临时文件存储目录，默认为None（使用系统临时目录）
        
    Returns:
        list: 每页的文字内容列表，格式为 ["====文件名第1页====\n内容", "====文件名第2页====\n内容", ...]
        如果识别失败返回空列表
        
    Raises:
        FileNotFoundError: 当PDF文件不存在时
        Exception: 当PDF处理或OCR识别失败时
    """
    try:
        # 检查PDF文件是否存在
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        # 获取文件名（不含路径和扩展名）
        filename = os.path.splitext(os.path.basename(pdf_path))[0]
        
        # 创建临时目录用于存储转换的图片
        if temp_dir is None:
            temp_dir = os.path.join(os.path.dirname(pdf_path), "temp_images")
        
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        # 打开PDF文件
        pdf_document = fitz.open(pdf_path)
        page_texts = []
        
        # 创建OCR服务实例
        ocr_service = create_ocr_service()
        
        print(f"正在处理PDF文件: {pdf_path}")
        print(f"总页数: {len(pdf_document)}")
        
        # 逐页处理
        for page_num in range(len(pdf_document)):
            try:
                print(f"正在处理第 {page_num + 1} 页...")
                
                # 获取页面
                page = pdf_document.load_page(page_num)
                
                # 将页面转换为图片（设置较高的分辨率以提高OCR准确性）
                mat = fitz.Matrix(2.0, 2.0)  # 2倍缩放，提高图片质量
                pix = page.get_pixmap(matrix=mat)
                
                # 保存为临时图片文件
                temp_image_path = os.path.join(temp_dir, f"page_{page_num + 1}.png")
                pix.save(temp_image_path)
                
                # 使用OCR识别图片中的文字
                text_content = ocr_service.recognize_text_from_image(temp_image_path)
                
                # 格式化输出
                if text_content:
                    formatted_text = f"===={filename}第{page_num + 1}页====\n{text_content}"
                else:
                    formatted_text = f"===={filename}第{page_num + 1}页====\n[未识别到文字内容]"
                
                page_texts.append(formatted_text)
                
                # 删除临时图片文件
                try:
                    os.remove(temp_image_path)
                except:
                    pass  # 忽略删除失败的情况
                
            except Exception as e:
                print(f"处理第 {page_num + 1} 页时出错: {str(e)}")
                error_text = f"===={filename}第{page_num + 1}页====\n[页面处理失败: {str(e)}]"
                page_texts.append(error_text)
                continue
        
        # 关闭PDF文档
        pdf_document.close()
        
        # 清理临时目录（如果为空）
        try:
            os.rmdir(temp_dir)
        except:
            pass  # 目录不为空或其他原因，忽略删除失败
        
        print(f"PDF处理完成，共处理 {len(page_texts)} 页")
        return page_texts
        
    except FileNotFoundError:
        raise
    except Exception as e:
        raise Exception(f"PDF文字识别失败: {str(e)}")


def save_pdf_text_to_file(pdf_path, output_path=None):
    """
    识别PDF文件中的文字并保存到文本文件
    
    Args:
        pdf_path (str): PDF文件路径
        output_path (str, optional): 输出文本文件路径，默认为None（自动生成）
        
    Returns:
        str: 输出文件的路径
        
    Raises:
        Exception: 当处理失败时
    """
    try:
        # 识别PDF文字
        page_texts = recognize_pdf_text(pdf_path)
        
        # 生成输出文件路径
        if output_path is None:
            base_name = os.path.splitext(pdf_path)[0]
            output_path = f"{base_name}_ocr_result.txt"
        
        # 保存到文件
        with open(output_path, 'w', encoding='utf-8') as f:
            for page_text in page_texts:
                f.write(page_text + '\n\n')
        
        print(f"识别结果已保存到: {output_path}")
        return output_path
        
    except Exception as e:
        raise Exception(f"保存PDF识别结果失败: {str(e)}")


if __name__ == "__main__":
    # 示例用法
    try:
        print("=== PDF OCR识别测试 ===")
        
        # 测试PDF OCR
        pdf_path = "变更.pdf"  # 替换为你的PDF路径
        if os.path.exists(pdf_path):
            print(f"找到PDF文件: {pdf_path}")
            
            # 方法1: 直接获取识别结果
            page_texts = recognize_pdf_text(pdf_path)
            print("\n=== PDF识别结果 ===")
            for i, page_text in enumerate(page_texts):
                print(f"{page_text}")
                print("-" * 50)  # 分隔线
            
            # 方法2: 保存到文件
            output_file = save_pdf_text_to_file(pdf_path)
            print(f"\n识别结果已保存到文件: {output_file}")
            
        else:
            print(f"PDF文件不存在: {pdf_path}")
            print("当前目录下的文件:")
            for file in os.listdir("."):
                if file.endswith(".pdf"):
                    print(f"  - {file}")
                    
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
