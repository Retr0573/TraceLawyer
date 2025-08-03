from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import hashlib
import base64
import hmac
from urllib.parse import urlencode
import json
import requests
import fitz  # PyMuPDF
from PIL import Image
import io
import os


class OCRService:
    """
    讯飞通用文字识别服务封装类
    支持中英文、手写和印刷文字识别
    """
    
    def __init__(self, app_id, api_secret, api_key):
        """
        初始化OCR服务
        
        Args:
            app_id (str): 讯飞开放平台的APP ID
            api_secret (str): 讯飞开放平台的API Secret
            api_key (str): 讯飞开放平台的API Key
        """
        self.app_id = app_id
        self.api_secret = api_secret
        self.api_key = api_key
        self.url = 'https://api.xf-yun.com/v1/private/sf8e6aca1'
    
    def _sha256base64(self, data):
        """计算sha256并编码为base64"""
        sha256 = hashlib.sha256()
        sha256.update(data)
        digest = base64.b64encode(sha256.digest()).decode(encoding='utf-8')
        return digest
    
    def _parse_url(self, request_url):
        """解析URL"""
        class Url:
            def __init__(self, host, path, schema):
                self.host = host
                self.path = path
                self.schema = schema
        
        stidx = request_url.index("://")
        host = request_url[stidx + 3:]
        schema = request_url[:stidx + 3]
        edidx = host.index("/")
        if edidx <= 0:
            raise Exception("invalid request url:" + request_url)
        path = host[edidx:]
        host = host[:edidx]
        return Url(host, path, schema)
    
    def _assemble_ws_auth_url(self, request_url, method="POST"):
        """构建认证URL"""
        u = self._parse_url(request_url)
        host = u.host
        path = u.path
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                                digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
        
        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.api_key, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        values = {
            "host": host,
            "date": date,
            "authorization": authorization
        }
        
        return request_url + "?" + urlencode(values)
    
    def _extract_text_from_ocr_result(self, ocr_result):
        """
        从OCR结果JSON中提取文字内容
        
        Args:
            ocr_result (dict): OCR识别结果的JSON数据
            
        Returns:
            str: 提取出的文字内容
        """
        text_lines = []
        
        if 'pages' in ocr_result:
            for page in ocr_result['pages']:
                if 'lines' in page:
                    for line in page['lines']:
                        if 'words' in line:
                            # 提取每行的文字内容
                            line_text = ""
                            for word in line['words']:
                                if 'content' in word:
                                    line_text += word['content']
                            if line_text.strip():
                                text_lines.append(line_text.strip())
        
        # 将所有行的文字连接起来
        return "".join(text_lines) if text_lines else ""
    
    def recognize_text_from_image(self, image_path):
        """
        从图片中识别文字
        
        Args:
            image_path (str): 图片文件路径
            
        Returns:
            str: 识别出的文字内容，如果识别失败返回None
            
        Raises:
            FileNotFoundError: 当图片文件不存在时
            Exception: 当API调用失败时
        """
        try:
            # 读取图片文件
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            # 构建请求体
            body = {
                "header": {
                    "app_id": self.app_id,
                    "status": 3
                },
                "parameter": {
                    "sf8e6aca1": {
                        "category": "ch_en_public_cloud",
                        "result": {
                            "encoding": "utf8",
                            "compress": "raw",
                            "format": "json"
                        }
                    }
                },
                "payload": {
                    "sf8e6aca1_data_1": {
                        "encoding": "jpg",
                        "image": str(base64.b64encode(image_bytes), 'UTF-8'),
                        "status": 3
                    }
                }
            }
            
            # 获取认证URL
            request_url = self._assemble_ws_auth_url(self.url, "POST")
            
            # 设置请求头
            headers = {
                'content-type': "application/json", 
                'host': 'api.xf-yun.com', 
                'app_id': self.app_id
            }
            
            # 发送请求
            response = requests.post(request_url, data=json.dumps(body), headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"API调用失败，状态码: {response.status_code}")
            
            # 解析响应
            result = json.loads(response.content.decode())
            
            # 检查是否有错误
            if 'code' in result and result['code'] != 0:
                raise Exception(f"API返回错误: {result.get('message', '未知错误')}")
            
            # 解码文字内容
            if 'payload' in result and 'result' in result['payload'] and 'text' in result['payload']['result']:
                text_base64 = result['payload']['result']['text']
                decoded_result = base64.b64decode(text_base64).decode()
                
                # 解析JSON格式的识别结果
                try:
                    ocr_result = json.loads(decoded_result)
                    # 提取所有文字内容
                    text_content = self._extract_text_from_ocr_result(ocr_result)
                    return text_content
                except json.JSONDecodeError:
                    # 如果不是JSON格式，直接返回原始文本
                    final_result = decoded_result.replace(" ", "").replace("\n", "").replace("\t", "").strip()
                    return final_result
            else:
                return None
                
        except FileNotFoundError:
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        except Exception as e:
            raise Exception(f"文字识别失败: {str(e)}")


def create_ocr_service():
    """
    创建OCR服务实例
    使用默认的API凭证（需要替换为你自己的凭证）
    
    Returns:
        OCRService: OCR服务实例
    """
    # 请替换为你自己的API凭证
    APP_ID = "9bdba858"
    API_SECRET = "NDNkOTVmZmJjYzc0OTg5MTg5ODI5MDNi"
    API_KEY = "98fb62695047338d32729257a65a48a6"
    
    return OCRService(APP_ID, API_SECRET, API_KEY)


def recognize_image_text(image_path):
    """
    便捷函数：识别图片中的文字
    
    Args:
        image_path (str): 图片文件路径
        
    Returns:
        str: 识别出的文字内容，如果识别失败返回None
    """
    ocr_service = create_ocr_service()
    return ocr_service.recognize_text_from_image(image_path)


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
        # # 测试图片OCR
        # print("=== 图片OCR测试 ===")
        # image_path = "1.jpg"  # 替换为你的图片路径
        # if os.path.exists(image_path):
        #     text = recognize_image_text(image_path)
        #     if text:
        #         print(f"图片识别结果: {text}")
        #     else:
        #         print("未识别到文字内容")
        # else:
        #     print(f"图片文件不存在: {image_path}")
        
        # print("\n=== PDF OCR测试 ===")
        # 测试PDF OCR
        pdf_path = "变更.pdf"  # 替换为你的PDF路径
        if os.path.exists(pdf_path):
            # 方法1: 直接获取识别结果
            page_texts = recognize_pdf_text(pdf_path)
            print("PDF识别结果:")
            for i, page_text in enumerate(page_texts):
                print(f"\n{page_text}")
            
            # # 方法2: 保存到文件
            # output_file = save_pdf_text_to_file(pdf_path)
            # print(f"\n识别结果已保存到文件: {output_file}")
        else:
            print(f"PDF文件不存在: {pdf_path}")
            
    except Exception as e:
        print(f"错误: {e}")
