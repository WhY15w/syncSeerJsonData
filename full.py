import requests
import json
import time
import os
import shutil
from typing import List, Dict, Optional
from jsonFormatter import format_single_json  # 直接复用你原来的格式化方法


VERSION_FILE = "version.json"
VERSION_BACKUP_FILE = "version.json.backup"
BASE_DOMAIN = "http://seerh5.61.com"

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 1  # 秒
RETRY_BACKOFF = 2  # 指数退避倍数


def retry_with_backoff(func, *args, max_retries=MAX_RETRIES, delay=RETRY_DELAY, backoff=RETRY_BACKOFF, **kwargs):
    """带指数退避的重试装饰器"""
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except (requests.RequestException, requests.ConnectionError, requests.Timeout) as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = delay * (backoff ** attempt)
                print(f"网络请求失败，{wait_time:.1f}秒后重试 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                time.sleep(wait_time)
            else:
                print(f"网络请求重试次数已达上限: {e}")
        except Exception as e:
            # 对于非网络异常，不重试
            raise e
    
    raise last_exception


def validate_json_data(data) -> bool:
    """验证JSON数据结构"""
    if not isinstance(data, dict):
        return False
    return True


def backup_file(file_path: str) -> bool:
    """备份文件"""
    if not os.path.exists(file_path):
        return True
    
    try:
        backup_path = f"{file_path}.backup"
        shutil.copy2(file_path, backup_path)
        return True
    except Exception as e:
        print(f"备份文件失败 {file_path}: {e}")
        return False


def restore_backup(file_path: str) -> bool:
    """从备份恢复文件"""
    backup_path = f"{file_path}.backup"
    if not os.path.exists(backup_path):
        print(f"备份文件不存在: {backup_path}")
        return False
    
    try:
        shutil.copy2(backup_path, file_path)
        print(f"已从备份恢复: {file_path}")
        return True
    except Exception as e:
        print(f"从备份恢复失败 {file_path}: {e}")
        return False


def safe_make_dirs(path: str) -> bool:
    """安全创建目录"""
    try:
        if path and not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        print(f"创建目录失败 {path}: {e}")
        return False


def build_path_from_keys(keys: List[str]) -> str:
    """将键列表转换为路径字符串"""
    return "/".join(keys)


def load_local_version() -> Dict:
    """加载本地版本信息，带错误恢复"""
    if not os.path.exists(VERSION_FILE):
        return {}
    
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if not validate_json_data(data):
            print("本地 version.json 数据格式无效")
            return {}
            
        return data
        
    except json.JSONDecodeError as e:
        print(f"本地 version.json 解析失败: {e}")
        # 尝试从备份恢复
        if restore_backup(VERSION_FILE):
            try:
                with open(VERSION_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}
    except Exception as e:
        print(f"读取本地版本文件失败: {e}")
        return {}


def save_local_version(data: Dict) -> bool:
    """安全保存版本文件，带备份机制"""
    if not validate_json_data(data):
        print("版本数据格式无效，拒绝保存")
        return False
    
    # 备份现有文件
    if not backup_file(VERSION_FILE):
        print("警告: 无法备份现有版本文件")
    
    try:
        # 写入临时文件
        temp_file = f"{VERSION_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 验证写入的文件
        with open(temp_file, "r", encoding="utf-8") as f:
            json.load(f)  # 验证JSON格式
        
        # 原子性替换
        if os.path.exists(VERSION_FILE):
            os.replace(temp_file, VERSION_FILE)
        else:
            os.rename(temp_file, VERSION_FILE)
            
        return True
        
    except Exception as e:
        print(f"保存版本文件失败: {e}")
        # 清理临时文件
        temp_file = f"{VERSION_FILE}.tmp"
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        return False


def diff_json_files(old_data: Dict, new_data: Dict, base_path: str = "") -> List[tuple]:
    """
    递归比较两个 JSON 数据，返回不同文件的 (url_path, local_path) 元组列表
    url_path: 用于下载的路径（带 hash）
    local_path: 本地保存路径（去掉 hash）
    """
    changed_files = []
    for key, new_val in new_data.items():
        old_val = old_data.get(key)

        if isinstance(new_val, dict):
            sub_path = f"{base_path}/{key}" if base_path else key
            changed_files.extend(diff_json_files(old_val or {}, new_val, sub_path))
        else:
            if key.lower().endswith(".json") and old_val != new_val:
                url_path = f"{base_path}/{new_val}"
                local_path = f"{base_path}/{key}"
                changed_files.append((url_path, local_path))
    return changed_files


def download_and_format(files_to_download: List[tuple]):
    """下载并格式化文件，带重试和验证机制"""
    if not files_to_download:
        return
    
    successful_downloads = 0
    failed_downloads = 0
    
    for url_path, local_path in files_to_download:
        try:
            # 输入验证
            if not url_path or not local_path:
                print(f"无效的文件路径: url_path={url_path}, local_path={local_path}")
                failed_downloads += 1
                continue
            
            # 去掉开头的 'files/'，防止 URL 多一层
            if url_path.startswith("files/"):
                url_path_clean = url_path[len("files/"):]
            else:
                url_path_clean = url_path

            url = f"{BASE_DOMAIN}/{url_path_clean}"
            
            # 验证URL格式
            if not url.startswith(('http://', 'https://')):
                print(f"无效的URL格式: {url}")
                failed_downloads += 1
                continue

            save_path = os.path.join(*local_path.split("/"))
            
            # 安全创建目录
            dir_path = os.path.dirname(save_path)
            if not safe_make_dirs(dir_path):
                print(f"无法创建目录: {dir_path}")
                failed_downloads += 1
                continue

            print(f"正在下载: {url}")
            
            # 使用重试机制下载
            def download_file():
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return response
            
            resp = retry_with_backoff(download_file)
            
            # 验证内容
            if not resp.content:
                print(f"下载内容为空: {url}")
                failed_downloads += 1
                continue
            
            # 如果是JSON文件，验证JSON格式
            if save_path.lower().endswith(".json"):
                try:
                    json.loads(resp.content.decode('utf-8'))
                except json.JSONDecodeError as e:
                    print(f"下载的JSON文件格式无效: {save_path}, 错误: {e}")
                    failed_downloads += 1
                    continue

            # 写入临时文件
            temp_path = f"{save_path}.tmp"
            try:
                with open(temp_path, "wb") as f:
                    f.write(resp.content)
                
                # 原子性替换
                if os.path.exists(save_path):
                    os.replace(temp_path, save_path)
                else:
                    os.rename(temp_path, save_path)
                    
                print(f"已保存: {save_path}")

                # 格式化JSON文件 (full.py 中格式化所有下载的文件)
                if not format_single_json(save_path):
                    print(f"警告: 文件格式化失败: {save_path}")
                
                successful_downloads += 1
                
            except Exception as e:
                print(f"保存文件失败 {save_path}: {e}")
                # 清理临时文件
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                failed_downloads += 1

        except Exception as e:
            print(f"下载或处理 {local_path} 出错: {e}")
            failed_downloads += 1
    
    print(f"下载完成: 成功 {successful_downloads} 个，失败 {failed_downloads} 个")


def main():
    """主函数，带完整的错误处理和恢复机制"""
    try:
        print("开始同步完整 JSON 数据...")
        
        # 加载本地版本信息
        local_version_data = load_local_version()
        print(f"已加载本地版本信息，包含 {len(local_version_data)} 个条目")

        # 获取远程版本信息，使用重试机制
        version_url = f"{BASE_DOMAIN}/version/version.json?t={int(time.time())}"
        print(f"获取版本信息: {version_url}")
        
        def fetch_version():
            response = requests.get(version_url, timeout=10)
            response.raise_for_status()
            
            # 验证响应内容
            if not response.content:
                raise ValueError("远程版本文件内容为空")
            
            data = response.json()
            if not validate_json_data(data):
                raise ValueError("远程版本数据格式无效")
            
            return data
        
        try:
            remote_version_data = retry_with_backoff(fetch_version)
            print(f"成功获取远程版本信息，包含 {len(remote_version_data)} 个条目")
        except Exception as e:
            print(f"获取远程版本失败: {e}")
            return

        # 比对差异
        changed_files = diff_json_files(local_version_data, remote_version_data)
        if not changed_files:
            print("没有需要更新的 JSON 文件")
            return

        print(f"需要更新 {len(changed_files)} 个文件")
        for f in changed_files:
            print("  -", f)

        # 下载并格式化
        download_and_format(changed_files)

        # 保存最新 version.json (只有下载成功才保存)
        if save_local_version(remote_version_data):
            print("已更新本地 version.json")
        else:
            print("警告: 更新本地版本文件失败")

    except requests.RequestException as e:
        print(f"网络请求错误: {e}")
        print("请检查网络连接和服务器状态")
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print("远程数据格式可能有问题")
    except Exception as e:
        print(f"执行出错: {e}")
        print("如果问题持续，请检查日志并重试")


if __name__ == "__main__":
    main()
