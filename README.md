# PDF OCR 和 AI 分析系统

这是一个基于Flask的Web应用，提供PDF文档的OCR识别和AI智能分析功能。

## 功能特点

1. **多PDF文件上传**: 支持同时上传多个PDF文件
2. **OCR文字识别**: 使用讯飞API对PDF逐页进行文字识别
3. **内容合并**: 可按指定页数合并PDF内容
4. **AI智能分析**: 调用工作流API对PDF内容进行智能分析
5. **实时进度**: 显示处理进度和状态
6. **美观界面**: 现代化的响应式Web界面

## 系统架构

```
project_workflow/
├── app.py                 # Flask主应用
├── templates/
│   └── index.html        # 前端页面
├── utils/
│   └── ocr_service.py    # OCR服务模块
├── uploads/              # 上传文件存储目录
├── results/              # 处理结果存储目录
├── temp_images/          # 临时图片存储目录
├── requirements.txt      # Python依赖
├── start.sh             # 启动脚本
└── README.md            # 说明文档
```

## 快速开始

### 1. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 2. 启动应用

#### 方法一：使用启动脚本（推荐）
```bash
chmod +x start.sh
./start.sh
```

#### 方法二：直接运行
```bash
python3 app.py
```

### 3. 访问应用

打开浏览器访问: http://localhost:5050

## 使用流程

1. **上传PDF文件**
   - 点击上传区域选择PDF文件，或直接拖拽文件到上传区域
   - 支持多个文件同时上传
   - 单个文件最大16MB

2. **OCR识别**
   - 点击"开始上传和OCR识别"按钮
   - 系统会自动对每个PDF文件进行逐页OCR识别
   - 实时显示处理进度

3. **查看结果**
   - OCR完成后会显示识别结果
   - 每个PDF文件的每一页内容都会单独显示

4. **AI分析**
   - 设置每K页合并为一个分析单元（默认5页）
   - 点击"开始检索分析"按钮
   - 系统会调用AI工作流进行智能分析
   - 显示分析结果

## API接口

### 1. 上传文件
- **URL**: `/upload`
- **方法**: POST
- **参数**: files (多个PDF文件)
- **返回**: task_id和处理状态

### 2. 查询状态
- **URL**: `/status/<task_id>`
- **方法**: GET
- **返回**: 处理进度和状态

### 3. AI分析
- **URL**: `/analyze`
- **方法**: POST
- **参数**: 
  - task_id: 任务ID
  - k_pages: 每K页合并数量
- **返回**: 分析结果

### 4. 获取结果
- **URL**: `/results/<task_id>`
- **方法**: GET
- **返回**: 详细的OCR结果

## 配置说明

### OCR服务配置
在 `utils/ocr_service.py` 中配置讯飞API credentials:
```python
APP_ID = "your_app_id"
API_SECRET = "your_api_secret"
API_KEY = "your_api_key"
```

### 工作流API配置
在 `app.py` 中的 `call_workflow_api` 函数中配置:
```python
headers = {
    "Authorization": "Bearer your_token",
}
data = {
    "flow_id": "your_flow_id",
}
```

## 技术栈

- **后端**: Flask, Python 3
- **前端**: HTML5, CSS3, JavaScript
- **OCR**: 讯飞开放平台API
- **PDF处理**: PyMuPDF
- **图像处理**: Pillow
- **AI分析**: 自定义工作流API

## 注意事项

1. **文件大小限制**: 单个PDF文件最大16MB
2. **支持格式**: 仅支持PDF格式
3. **网络要求**: 需要访问讯飞API和工作流API
4. **临时文件**: 系统会自动清理临时生成的图片文件
5. **并发处理**: 支持多任务并发处理

## 错误处理

- 文件上传失败: 检查文件格式和大小
- OCR识别失败: 检查网络连接和API配置
- AI分析失败: 检查工作流API配置和网络连接

## 性能优化建议

1. 对于大量PDF文件，建议分批处理
2. 可以调整K页合并数量来优化分析效果
3. 定期清理uploads和results目录中的旧文件

## 开发扩展

如需扩展功能，可以：
1. 添加更多OCR服务提供商
2. 支持更多文件格式
3. 添加用户认证和权限管理
4. 增加数据库存储功能
5. 添加结果导出功能
