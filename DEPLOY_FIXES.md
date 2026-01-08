# 部署问题修复说明

## 已修复的问题

### 1. Pandas FutureWarning 警告
**问题**: `FutureWarning: Starting with pandas version 3.0 all arguments of to_excel except for the argument 'excel_writer' will be keyword-only.`

**修复**: 所有 `to_excel()` 调用已更新为使用关键字参数：
```python
# 修复前
df.to_excel(writer, 'Sheet名称', index=False)

# 修复后
df.to_excel(writer, sheet_name='Sheet名称', index=False)
```

### 2. Worker Timeout 超时问题
**问题**: `WORKER TIMEOUT` - 处理Excel文件时超时

**修复**:
- 增加Gunicorn超时时间到300秒（5分钟）
- 减少worker数量到2个（减少内存使用）
- 添加了 `gunicorn_config.py` 配置文件
- 添加文件大小检查（限制30MB）

### 3. 内存优化
**优化**:
- 明确指定 `engine='openpyxl'` 提高性能
- 限制文件大小为30MB
- 使用2个worker而不是默认的4个
- 添加了 `max_requests` 限制防止内存泄漏

## 部署步骤

1. **提交更改到GitHub**:
   ```bash
   git add .
   git commit -m "Fix pandas warnings and timeout issues"
   git push
   ```

2. **Render会自动重新部署**

3. **如果还有问题，可以手动触发重新部署**:
   - 在Render控制台点击 "Manual Deploy" → "Deploy latest commit"

## 配置说明

### Gunicorn配置 (`gunicorn_config.py`)
- **Workers**: 2个（适合免费计划）
- **Timeout**: 300秒（5分钟）
- **Max Requests**: 1000（自动重启worker防止内存泄漏）

### 文件大小限制
- **最大上传**: 30MB
- 如果文件太大，建议：
  1. 压缩Excel文件
  2. 删除不必要的数据
  3. 分批处理

## 性能优化建议

如果处理大文件仍然超时，可以考虑：

1. **增加超时时间**（在 `gunicorn_config.py` 中）:
   ```python
   timeout = 600  # 10分钟
   ```

2. **升级到付费计划**（Render Starter计划）:
   - 更多内存
   - 更快的CPU
   - 无休眠

3. **优化代码**:
   - 使用流式处理大文件
   - 分批处理数据
   - 使用更高效的数据结构

## 监控和调试

### 查看日志
在Render控制台可以查看：
- 实时日志
- 错误信息
- 性能指标

### 常见错误

**内存不足**:
- 减少worker数量到1
- 限制文件大小
- 优化代码减少内存使用

**超时**:
- 增加timeout值
- 优化处理逻辑
- 考虑异步处理

## 测试建议

部署后测试：
1. 上传小文件（< 1MB）测试基本功能
2. 上传中等文件（5-10MB）测试性能
3. 监控内存和CPU使用情况

