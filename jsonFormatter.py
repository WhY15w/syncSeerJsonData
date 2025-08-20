import json
import os


def format_single_json(input_file, indent=2):
    """格式化单个JSON文件，带更强的错误处理"""
    if not input_file or not os.path.exists(input_file):
        print(f"❌ 文件不存在: {input_file}")
        return False
        
    # 检查文件权限
    if not os.access(input_file, os.R_OK):
        print(f"❌ 文件无读取权限: {input_file}")
        return False
        
    if not os.access(input_file, os.W_OK):
        print(f"❌ 文件无写入权限: {input_file}")
        return False
    
    try:
        # 备份原文件
        backup_path = f"{input_file}.bak"
        try:
            import shutil
            shutil.copy2(input_file, backup_path)
        except Exception:
            pass  # 备份失败不影响主流程
        
        # 读取JSON文件
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 写入临时文件
        temp_file = f"{input_file}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent, sort_keys=False)
        
        # 验证临时文件
        with open(temp_file, "r", encoding="utf-8") as f:
            json.load(f)  # 验证JSON格式
        
        # 原子性替换
        os.replace(temp_file, input_file)
        
        # 清理备份文件（如果格式化成功）
        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
            except:
                pass

        print(f"已处理: {input_file}")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ 无效JSON格式: {input_file} - {e}")
        # 尝试从备份恢复
        backup_path = f"{input_file}.bak"
        if os.path.exists(backup_path):
            try:
                import shutil
                shutil.copy2(backup_path, input_file)
                print(f"已从备份恢复: {input_file}")
            except:
                pass
        return False
    except Exception as e:
        print(f"❌ 处理失败 {input_file}: {str(e)}")
        # 清理临时文件
        temp_file = f"{input_file}.tmp"
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        return False


def batch_format_json(directory, indent=2, exclude_dirs=None):
    """
    批量格式化目录下的所有JSON文件，带改进的错误处理

    参数:
        directory: 要处理的根目录
        indent: 缩进空格数
        exclude_dirs: 要排除的目录列表
    """
    if exclude_dirs is None:
        exclude_dirs = []

    # 检查目录是否存在
    if not directory or not os.path.isdir(directory):
        print(f"错误: 目录 '{directory}' 不存在或不是目录")
        return

    # 检查目录权限
    if not os.access(directory, os.R_OK):
        print(f"错误: 目录 '{directory}' 无读取权限")
        return

    total_files = 0
    processed_files = 0
    error_files = 0

    try:
        # 递归遍历目录
        for root, dirs, files in os.walk(directory):
            # 排除指定目录
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            # 处理当前目录下的JSON文件
            for file in files:
                if file.lower().endswith(".json"):
                    total_files += 1
                    file_path = os.path.join(root, file)
                    
                    try:
                        if format_single_json(file_path, indent):
                            processed_files += 1
                        else:
                            error_files += 1
                    except Exception as e:
                        print(f"处理文件时发生错误 {file_path}: {e}")
                        error_files += 1

    except Exception as e:
        print(f"遍历目录时发生错误: {e}")

    print(f"\n处理完成 - 共发现 {total_files} 个JSON文件，成功处理 {processed_files} 个，失败 {error_files} 个")


if __name__ == "__main__":
    # 配置参数
    target_directory = "./files"
    indent_spaces = 2
    exclude_directories = [".git", "venv", "node_modules"]  # 排除不需要处理的目录

    print(f"开始处理目录: {os.path.abspath(target_directory)}")
    batch_format_json(target_directory, indent_spaces, exclude_directories)
