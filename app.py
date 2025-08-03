from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os
import json
import http.client
import ssl
from utils.ocr_service import recognize_pdf_text
import threading
from datetime import datetime
import uuid

app = Flask(__name__)

# 配置
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'pdf'}

# 确保文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 16MB max file size

# 存储处理状态和结果
processing_status = {}
pdf_results = {}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# def process_pdfs_async(task_id, pdf_files):
#     """异步处理PDF文件"""
#     try:
#         processing_status[task_id] = {'status': 'processing', 'progress': 0, 'total': len(pdf_files)}
#         pdf_results[task_id] = []
        
#         for i, pdf_file in enumerate(pdf_files):
#             try:
#                 # 处理单个PDF
#                 pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file)
#                 page_texts = recognize_pdf_text(pdf_path)
                
#                 # 保存结果
#                 result = {
#                     'filename': pdf_file,
#                     'pages': page_texts,
#                     'timestamp': datetime.now().isoformat()
#                 }
#                 pdf_results[task_id].append(result)
                
#                 # 更新进度
#                 processing_status[task_id]['progress'] = i + 1
                
#             except Exception as e:
#                 # 记录错误但继续处理其他文件
#                 error_result = {
#                     'filename': pdf_file,
#                     'error': str(e),
#                     'timestamp': datetime.now().isoformat()
#                 }
#                 pdf_results[task_id].append(error_result)
#                 processing_status[task_id]['progress'] = i + 1
        
#         processing_status[task_id]['status'] = 'completed'
        
#     except Exception as e:
#         processing_status[task_id] = {'status': 'error', 'error': str(e)}


def process_pdfs_async(task_id, pdf_files):
    """异步处理PDF文件"""
    try:
        processing_status[task_id] = {'status': 'processing', 'progress': 0, 'total': len(pdf_files)}
        pdf_results[task_id] = []
        
        for i, pdf_file in enumerate(pdf_files):
            try:
                # 处理单个PDF
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file)
                page_texts = recognize_pdf_text(pdf_path)
                
                # 保存结果
                result = {
                    'filename': pdf_file,
                    'pages': page_texts,
                    'timestamp': datetime.now().isoformat()
                }
                pdf_results[task_id].append(result)
                
                # OCR处理完成后删除原始PDF文件
                try:
                    os.remove(pdf_path)
                    print(f"已删除处理完成的文件: {pdf_file}")
                except Exception as e:
                    print(f"删除文件失败: {pdf_file}, 错误: {e}")
                
                # 更新进度
                processing_status[task_id]['progress'] = i + 1
                
            except Exception as e:
                # 记录错误但继续处理其他文件
                error_result = {
                    'filename': pdf_file,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                pdf_results[task_id].append(error_result)
                processing_status[task_id]['progress'] = i + 1
                
                # 即使处理失败也删除文件
                try:
                    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file)
                    os.remove(pdf_path)
                except:
                    pass
        
        processing_status[task_id]['status'] = 'completed'
        
    except Exception as e:
        processing_status[task_id] = {'status': 'error', 'error': str(e)}

def call_workflow_api(pdf_content_list):
    print("pdf_content_list:")
    print(pdf_content_list)
    """调用workflow API"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Authorization": "Bearer 98fb62695047338d32729257a65a48a6:NDNkOTVmZmJjYzc0OTg5MTg5ODI5MDNi",
    }
    
    data = {
        "flow_id": "7357096384330665986",
        "uid": "123",
        "parameters": {
            "AGENT_USER_INPUT": "请分析以下PDF内容",
            "pdf_list": pdf_content_list
        },
        "ext": {"bot_id": "adjfidjf", "caller": "workflow"},
        "stream": True,
    }
    
    payload = json.dumps(data)
    
    try:
        conn = http.client.HTTPSConnection("xingchen-api.xf-yun.com", timeout=120)
        conn.request("POST", "/workflow/v1/chat/completions", payload, headers, encode_chunked=True)
        res = conn.getresponse()
        
        response_content = []
        
        if data.get("stream"):
            while chunk := res.readline():
                chunk_str = chunk.decode("utf-8").strip()
                if chunk_str.startswith("data: "):
                    json_str = chunk_str[6:]
                    try:
                        data_dict = json.loads(json_str)
                        if "choices" in data_dict and len(data_dict["choices"]) > 0:
                            choice = data_dict["choices"][0]
                            if "delta" in choice and "content" in choice["delta"]:
                                content = choice["delta"]["content"]
                                print("content:",content)
                                response_content.append(content)
                    except json.JSONDecodeError:
                        continue
        
        return ''.join(response_content)
        
    except Exception as e:
        return f"API调用错误: {str(e)}"


def call_workflow_api_stream(pdf_content_list):
    """流式调用workflow API"""
    print("pdf_content_list:")
    print(pdf_content_list)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Authorization": "Bearer 98fb62695047338d32729257a65a48a6:NDNkOTVmZmJjYzc0OTg5MTg5ODI5MDNi",
    }
    
    data = {
        "flow_id": "7357096384330665986",
        "uid": "123",
        "parameters": {
            "AGENT_USER_INPUT": "请分析以下PDF内容",
            "pdf_list": pdf_content_list
        },
        "ext": {"bot_id": "adjfidjf", "caller": "workflow"},
        "stream": True,
    }
    
    payload = json.dumps(data)
    
    try:
        conn = http.client.HTTPSConnection("xingchen-api.xf-yun.com", timeout=120)
        conn.request("POST", "/workflow/v1/chat/completions", payload, headers, encode_chunked=True)
        res = conn.getresponse()
        
        if data.get("stream"):
            while chunk := res.readline():
                chunk_str = chunk.decode("utf-8").strip()
                if chunk_str.startswith("data: "):
                    json_str = chunk_str[6:]
                    try:
                        data_dict = json.loads(json_str)
                        if "choices" in data_dict and len(data_dict["choices"]) > 0:
                            choice = data_dict["choices"][0]
                            if "delta" in choice and "content" in choice["delta"]:
                                content = choice["delta"]["content"]
                                print("content:",content)
                                yield content
                    except json.JSONDecodeError:
                        continue
        
        conn.close()
        
    except Exception as e:
        yield f"API调用错误: {str(e)}"


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_files():
    """上传PDF文件"""
    if 'files' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    files = request.files.getlist('files')
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': '没有选择文件'}), 400
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    uploaded_files = []
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # 添加时间戳避免文件名冲突
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{filename}"
            
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            uploaded_files.append(filename)
    
    if not uploaded_files:
        return jsonify({'error': '没有有效的PDF文件'}), 400
    
    # 启动异步处理
    thread = threading.Thread(target=process_pdfs_async, args=(task_id, uploaded_files))
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'message': f'开始处理 {len(uploaded_files)} 个PDF文件',
        'files': uploaded_files
    })


@app.route('/status/<task_id>')
def get_status(task_id):
    """获取处理状态"""
    if task_id not in processing_status:
        return jsonify({'error': '任务不存在'}), 404
    
    status = processing_status[task_id]
    
    # 如果处理完成，返回结果
    if status.get('status') == 'completed' and task_id in pdf_results:
        return jsonify({
            'status': 'completed',
            'results': pdf_results[task_id]
        })
    
    return jsonify(status)


@app.route('/analyze', methods=['POST'])
def analyze_pdfs():
    """分析PDF内容"""
    data = request.get_json()
    task_id = data.get('task_id')
    k_pages = data.get('k_pages', 5)  # 每K页合并，默认5页
    
    if not task_id or task_id not in pdf_results:
        return jsonify({'error': '无效的任务ID或结果不存在'}), 400
    
    try:
        # 获取所有PDF的页面内容
        all_pages = []
        for pdf_result in pdf_results[task_id]:
            if 'pages' in pdf_result:
                all_pages.extend(pdf_result['pages'])
        
        if not all_pages:
            return jsonify({'error': '没有找到可分析的内容'}), 400
        
        # 按K页合并内容
        pdf_content_list = []
        for i in range(0, len(all_pages), k_pages):
            chunk = all_pages[i:i + k_pages]
            combined_content = '\n\n'.join(chunk)
            pdf_content_list.append(combined_content)
        
        # 调用workflow API
        api_response = call_workflow_api(pdf_content_list)
        
        return jsonify({
            'success': True,
            'chunks_count': len(pdf_content_list),
            'k_pages': k_pages,
            'analysis_result': api_response
        })
        
    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500


@app.route('/analyze_stream', methods=['POST'])
def analyze_pdfs_stream():
    """流式分析PDF内容"""
    from flask import Response
    
    data = request.get_json()
    task_id = data.get('task_id')
    k_pages = data.get('k_pages', 5)  # 每K页合并，默认5页
    
    if not task_id or task_id not in pdf_results:
        return jsonify({'error': '无效的任务ID或结果不存在'}), 400
    
    def generate():
        try:
            # 获取所有PDF的页面内容
            all_pages = []
            for pdf_result in pdf_results[task_id]:
                if 'pages' in pdf_result:
                    all_pages.extend(pdf_result['pages'])
            
            if not all_pages:
                yield f"data: {json.dumps({'error': '没有找到可分析的内容'})}\n\n"
                return
            
            # 按K页合并内容
            pdf_content_list = []
            for i in range(0, len(all_pages), k_pages):
                chunk = all_pages[i:i + k_pages]
                combined_content = '\n\n'.join(chunk)
                pdf_content_list.append(combined_content)
            
            # 发送初始信息
            yield f"data: {json.dumps({'type': 'init', 'chunks_count': len(pdf_content_list), 'k_pages': k_pages})}\n\n"
            
            # 调用workflow API并流式传输
            for content in call_workflow_api_stream(pdf_content_list):
                if content:
                    yield f"data: {json.dumps({'type': 'content', 'data': content})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/plain', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no'
    })


@app.route('/results/<task_id>')
def get_results(task_id):
    """获取处理结果详情"""
    if task_id not in pdf_results:
        return jsonify({'error': '结果不存在'}), 404
    
    return jsonify(pdf_results[task_id])


@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': '文件太大，请选择小于50MB的文件'}), 413


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5500)
