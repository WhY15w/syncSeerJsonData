import requests
import json
import time
import os
from typing import List, Dict
from jsonFormatter import format_single_json

VERSION_FILE = "version.json"
BASE_DOMAIN = "http://seerh5.61.com"
TARGET_PATHS = [
    ["files", "resource", "config", "json"],
    ["files", "resource", "config", "xml"],
]


def load_local_version() -> Dict:
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("本地 version.json 解析失败，将视为无本地版本")
    return {}


def save_local_version(data: Dict):
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_nested(data: Dict, keys: List[str]):
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return {}
    return data


def diff_json_files(old_data: Dict, new_data: Dict, base_path: str = "") -> List[tuple]:
    """
    返回不同文件的 (url_path, local_path) 列表
    url_path: 下载路径（带hash）
    local_path: 本地保存路径（原文件名）
    """
    changed_files = []
    for key, new_val in new_data.items():
        old_val = old_data.get(key)

        if isinstance(new_val, dict):
            sub_path = f"{base_path}/{key}" if base_path else key
            changed_files.extend(diff_json_files(old_val or {}, new_val, sub_path))
        else:
            if key.lower().endswith((".json", ".xml")) and old_val != new_val:
                url_path = f"{base_path}/{new_val}"
                local_path = f"{base_path}/{key}"
                changed_files.append((url_path, local_path))
    return changed_files


def download_and_format(files_to_download: List[tuple]):
    for url_path, local_path in files_to_download:
        try:
            # URL 去掉 'files/'
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

            if save_path.lower().endswith(".json"):
                format_single_json(save_path)

        except Exception as e:
            print(f"下载或处理 {local_path} 出错: {e}")


def main():
    try:
        local_version_data = load_local_version()

        version_url = f"{BASE_DOMAIN}/version/version.json?t={int(time.time())}"
        print(f"获取版本信息: {version_url}")
        version_resp = requests.get(version_url, timeout=10)
        version_resp.raise_for_status()
        remote_version_data = version_resp.json()

        changed_files = []
        for path_keys in TARGET_PATHS:
            local_target = get_nested(local_version_data, path_keys)
            remote_target = get_nested(remote_version_data, path_keys)
            changed_files.extend(
                diff_json_files(local_target, remote_target, "/".join(path_keys))
            )

        if not changed_files:
            print("没有需要更新的文件")
            return

        print(f"需要更新 {len(changed_files)} 个文件：")
        for _, local_path in changed_files:
            print("  -", local_path)

        download_and_format(changed_files)

        save_local_version(remote_version_data)
        print("已更新本地 version.json")

    except requests.RequestException as e:
        print(f"网络请求错误: {e}")
    except Exception as e:
        print(f"执行出错: {e}")


if __name__ == "__main__":
    main()
