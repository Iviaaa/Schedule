# Gunicorn配置文件
# 可以根据服务器资源调整这些参数

import multiprocessing
import os

# 服务器socket
# Render会自动设置PORT环境变量
port = int(os.environ.get('PORT', 5000))
bind = f"0.0.0.0:{port}"

# Worker进程数
# 公式: workers = (2 x CPU核心数) + 1
# 对于Render免费计划，使用2个worker
workers = 2

# Worker类型
worker_class = 'sync'

# 超时时间（秒）- 增加到5分钟，因为Excel处理可能需要较长时间
timeout = 300

# 保持连接时间
keepalive = 5

# 最大请求数（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50

# 日志级别
loglevel = 'info'

# 访问日志
accesslog = '-'
errorlog = '-'

# 进程名称
proc_name = '排程计算工具'

# 预加载应用（节省内存）
preload_app = True

# Worker超时后的优雅重启
graceful_timeout = 30

