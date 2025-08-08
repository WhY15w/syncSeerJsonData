# syncSeerJsonData

该项目用于自动同步 赛尔号 的配置文件，通过定时任务检查远程版本变化并更新本地文件，确保数据与远程服务保持一致。

## 功能说明

- 定期检查远程服务器的配置文件版本
- 对比本地版本与远程版本，检测文件变化
- 自动下载更新的 JSON 和 XML 文件
- 对下载的 JSON 文件进行格式化处理
- 自动提交更新到代码仓库（通过 GitHub Actions）

## 工作原理

1. 从远程服务器获取最新的版本信息（`version.json`）
2. 与本地保存的版本信息对比，找出变化的文件
3. 下载变化的文件并保存到本地对应路径
4. 更新本地版本信息为最新版本
5. 通过 GitHub Actions 定时执行同步任务并提交更新

## 核心脚本说明

### syncSeerH5Data.py

主要功能模块：

- `load_local_version()`: 加载本地版本信息
- `save_local_version()`: 保存最新版本信息到本地
- `get_nested()`: 获取嵌套字典中的目标数据
- `diff_json_files()`: 对比本地与远程版本，找出变化的文件
- `download_and_format()`: 下载文件并格式化 JSON
- `main()`: 主函数，协调各模块执行同步流程

## 自动同步配置

通过 GitHub Actions 实现定时同步，配置文件 `auto-sync.yml` 定义了：

- 触发时机：每天北京时间 15:00 和 18:00 自动执行，也可手动触发
- 执行步骤：
  1. 拉取代码仓库
  2. 配置 Python 环境
  3. 安装依赖（requests）
  4. 运行同步脚本
  5. 提交更新到仓库

## 使用方法

1. 克隆本仓库到本地
2. 安装依赖：`pip install requests`
3. 手动执行同步：`python syncSeerH5Data.py`

对于 GitHub 仓库用户，无需额外操作，自动同步任务会按预定时间执行。

## 注意事项

- 同步的文件会保存在 `files/resource/config` 目录下
- JSON 文件会自动进行格式化处理，确保格式统一
- 本地版本信息存储在 `version.json`，请勿手动修改
- 网络问题可能导致同步失败，失败时会在控制台输出错误信息

## 依赖项

- Python 3.11+
- requests 库
