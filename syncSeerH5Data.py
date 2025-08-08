import requests
import json
import time
import os
from typing import List, Dict


def build_path_from_keys(keys: List[str]) -> str:
    """将键列表转换为路径字符串"""
    return "/".join(keys)


def download_files(
    version_resp_json: Dict, keys: List[str], base_domain: str = "http://seerh5.61.com"
) -> None:
    try:
        current_data = version_resp_json
        for key in keys:
            current_data = current_data[key]
            if not current_data:
                raise ValueError(f"在路径 {keys[:keys.index(key)+1]} 处找到空值")

        path_str = build_path_from_keys(keys).replace("files/", "")
        base_url = f"{base_domain}/{path_str}"
        save_dir = os.path.join(*keys)

        print(f"构建的路径: {path_str}")

        if not isinstance(current_data, dict):
            print(f"路径 {path_str} 指向的不是文件列表")
            return

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            print(f"创建保存目录: {save_dir}")

        for file_name, file_path in current_data.items():
            try:
                file_url = f"{base_url}/{file_path}"
                print(f"正在下载: {file_url}")

                file_resp = requests.get(file_url, timeout=10)
                file_resp.raise_for_status()  # 抛出HTTP错误状态码

                save_path = os.path.join(save_dir, file_name)
                with open(save_path, "wb") as f:
                    f.write(file_resp.content)

                print(f"成功保存: {save_path}")
            except Exception as e:
                print(f"下载 {file_name} 时出错: {str(e)}")

    except KeyError as e:
        print(f"JSON结构中缺少键: {e}")
    except Exception as e:
        print(f"处理路径 {keys} 时出错: {str(e)}")


def main():
    try:
        download_paths = [
            ["files", "resource", "config", "json"],
            ["files", "resource", "config", "xml"],
        ]

        version_url = f"http://seerh5.61.com/version/version.json?t={int(time.time())}"
        print(f"获取版本信息: {version_url}")

        version_resp = requests.get(version_url, timeout=10)
        version_resp.raise_for_status()
        version_resp_json = version_resp.json()

        remote_version = version_resp_json.get("version")
        if remote_version:
            print(f"检测到远程版本: {remote_version}")

        for path_keys in download_paths:
            download_files(version_resp_json, path_keys)

    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {str(e)}")
    except json.JSONDecodeError:
        print("无法解析服务器返回的JSON数据")
    except Exception as e:
        print(f"程序执行出错: {str(e)}")


if __name__ == "__main__":
    main()
