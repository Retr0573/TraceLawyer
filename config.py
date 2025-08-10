# TraceLawyer 智能法律分析系统配置文件

# 系统基本配置
SYSTEM_NAME = "TraceLawyer 智能法律分析系统"
SYSTEM_VERSION = "v2.0.0"
SYSTEM_DESCRIPTION = "基于AI的股东出资抽逃智能识别与分析平台"

# 服务器配置
HOST = "0.0.0.0"
PORT = 5500
DEBUG = True

# 文件上传配置
UPLOAD_FOLDER = "uploads"
DOWNLOAD_FOLDER = "downloads"
RESULTS_FOLDER = "results"
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {"pdf"}

# OCR配置
OCR_TIMEOUT = 300  # 5分钟超时
OCR_MAX_RETRIES = 3

# AI工作流配置
WORKFLOW_API_URL = "https://xingchen-api.xf-yun.com/workflow/v1/chat/completions"
WORKFLOW_TIMEOUT = 320  # 超时时间
FLOW_ID = "7358700018745618434"

# 报告生成配置
REPORT_TEMPLATE = "法律意见书"
REPORT_FORMAT = "docx"
AUTO_CLEANUP = True  # 自动清理临时文件

# 系统统计配置
STATS_UPDATE_INTERVAL = 30  # 统计更新间隔（秒）
ENABLE_ANALYTICS = True

# 安全配置
ENABLE_RATE_LIMITING = False
MAX_REQUESTS_PER_MINUTE = 60

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = "system.log"
ENABLE_ACCESS_LOG = True

# 功能开关
ENABLE_STREAM_ANALYSIS = True
ENABLE_BATCH_PROCESSING = True
ENABLE_REAL_TIME_PROGRESS = True
ENABLE_AUTO_WORD_GENERATION = True

# UI配置
THEME = "modern"
LANGUAGE = "zh-CN"
ENABLE_DARK_MODE = False
