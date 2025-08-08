import json
import os


def format_single_json(input_file, indent=2):
    """格式化单个JSON文件"""
    try:
        # 读取JSON文件
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 格式化并写入文件
        with open(input_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent, sort_keys=False)

        print(f"已处理: {input_file}")
        return True

    except json.JSONDecodeError:
        print(f"❌ 无效JSON格式: {input_file}")
        return False
    except Exception as e:
        print(f"❌ 处理失败 {input_file}: {str(e)}")
        return False


def batch_format_json(directory, indent=2, exclude_dirs=None):
    """
    批量格式化目录下的所有JSON文件

    参数:
        directory: 要处理的根目录
        indent: 缩进空格数
        exclude_dirs: 要排除的目录列表
    """
    if exclude_dirs is None:
        exclude_dirs = []

    # 检查目录是否存在
    if not os.path.isdir(directory):
        print(f"错误: 目录 '{directory}' 不存在")
        return

    total_files = 0
    processed_files = 0

    # 递归遍历目录
    for root, dirs, files in os.walk(directory):
        # 排除指定目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        # 处理当前目录下的JSON文件
        for file in files:
            if file.lower().endswith(".json"):
                total_files += 1
                file_path = os.path.join(root, file)
                if format_single_json(file_path, indent):
                    processed_files += 1

    print(
        f"\n处理完成 - 共发现 {total_files} 个JSON文件，成功处理 {processed_files} 个"
    )


if __name__ == "__main__":
    # 配置参数
    target_directory = "./files"
    indent_spaces = 2
    exclude_directories = [".git", "venv", "node_modules"]  # 排除不需要处理的目录

    print(f"开始处理目录: {os.path.abspath(target_directory)}")
    batch_format_json(target_directory, indent_spaces, exclude_directories)
