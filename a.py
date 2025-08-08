import requests
import re
from collections import defaultdict


def parse_manifest(binary_data):
    """解析二进制清单数据，提取关键信息"""
    # 尝试多种编码解码（游戏清单常用编码）
    encodings = ["latin-1", "utf-8", "utf-16"]
    text = ""
    for encoding in encodings:
        try:
            text = binary_data.decode(encoding, errors="ignore")
            if len(text) > 0:
                break
        except:
            continue

    # 定义关键信息的正则模式
    patterns = {
        # 资源路径（Assets/开头，包含扩展名）
        "paths": re.compile(r"Assets/[\w/]+?\.\w+"),
        # 哈希值（32-40位十六进制，游戏常用SHA-1）
        "hashes": re.compile(r"[0-9a-fA-F]{32,40}"),
        # 时间戳（YYYYMMDDHHMMSS格式）
        "timestamps": re.compile(r"\b20\d{12}\b"),
        # 版本号（x.y.z格式）
        "versions": re.compile(r"\d+\.\d+\.\d+"),
        # 包名相关（Package/Startup等关键词）
        "packages": re.compile(r"[A-Za-z]+Package"),
    }

    # 提取信息并去重
    result = defaultdict(list)
    for key, pattern in patterns.items():
        matches = pattern.findall(text)
        result[key] = list(set(matches))  # 去重

    return result


def print_parsed_info(info):
    """格式化输出解析结果"""
    print("===== 解析到的关键信息 =====")
    print(
        f"时间戳: {', '.join(info['timestamps']) if info['timestamps'] else '未找到'}"
    )
    print(f"包名: {', '.join(info['packages']) if info['packages'] else '未找到'}\n")

    print("资源路径列表:")
    for path in sorted(info["paths"]):
        print(f"  - {path}")

    print("\n哈希值列表:")
    for hash_str in info["hashes"][:10]:
        print(f"  - {hash_str}")
    if len(info["hashes"]) > 10:
        print(f"  - ... 还有{len(info['hashes'])-10}个哈希值")


# 目标清单文件URL
# url = "https://h5-seer.61.com/StreamingAssets/yoo/DefaultPackage/PackageManifest_DefaultPackage_20250725100104.bytes"
url = "https://h5-seer.61.com/StreamingAssets/yoo/StartupPackage/PackageManifest_StartupPackage_20250725100104.bytes"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()  # 检查请求是否成功

    # 解析并输出信息
    parsed_info = parse_manifest(response.content)
    print_parsed_info(parsed_info)

except requests.exceptions.RequestException as e:
    print(f"请求错误: {e}")
except Exception as e:
    print(f"解析错误: {e}")
