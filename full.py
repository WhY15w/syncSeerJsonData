import requests
import json
import time
import os
from typing import List, Dict
from jsonFormatter import format_single_json  # 直接复用你原来的格式化方法


VERSION_FILE = "version.json"
BASE_DOMAIN = "http://seerh5.61.com"


def build_path_from_keys(keys: List[str]) -> str:
    """将键列表转换为路径字符串"""
    return "/".join(keys)


def load_local_version() -> Dict:
    """加载本地 version.json"""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("本地 version.json 解析失败，将视为无本地版本")
    return {}


def save_local_version(data: Dict):
    """保存最新 version.json"""
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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
    """下载并格式化指定文件"""
    for url_path, local_path in files_to_download:
        try:
            # 去掉开头的 'files/'，防止 URL 多一层
            if url_path.startswith("files/"):
                url_path_clean = url_path[len("files/") :]
            else:
                url_path_clean = url_path

            url = f"{BASE_DOMAIN}/{url_path_clean}"

            save_path = os.path.join(*local_path.split("/"))
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            print(f"正在下载: {url}")
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()

            with open(save_path, "wb") as f:
                f.write(resp.content)
            print(f"已保存: {save_path}")

            format_single_json(save_path)

        except Exception as e:
            print(f"下载或处理 {local_path} 出错: {e}")


def main():
    try:
        # 加载本地版本信息
        local_version_data = load_local_version()

        # 获取远程版本信息
        version_url = f"{BASE_DOMAIN}/version/version.json?t={int(time.time())}"
        print(f"获取版本信息: {version_url}")
        version_resp = requests.get(version_url, timeout=10)
        version_resp.raise_for_status()
        remote_version_data = version_resp.json()

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

        # 保存最新 version.json
        save_local_version(remote_version_data)
        print("已更新本地 version.json")

    except requests.RequestException as e:
        print(f"网络请求错误: {e}")
    except Exception as e:
        print(f"执行出错: {e}")


if __name__ == "__main__":
    main()
