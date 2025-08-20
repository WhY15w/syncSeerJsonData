#!/usr/bin/env python3
"""
测试脚本 - 验证容错改进功能
Test script to verify fault tolerance improvements
"""

import sys
import os
import tempfile
import json

# Add the project directory to the path
sys.path.insert(0, '/home/runner/work/syncSeerJsonData/syncSeerJsonData')

import syncSeerH5Data

def test_retry_mechanism():
    """测试重试机制"""
    print("=== 测试重试机制 ===")
    
    attempt_count = 0
    def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            import requests
            raise requests.ConnectionError("Simulated network error")
        return "Success after retries"
    
    try:
        result = syncSeerH5Data.retry_with_backoff(failing_function, max_retries=3, delay=0.1)
        print(f"✅ 重试机制测试通过: {result}")
        print(f"   总尝试次数: {attempt_count}")
        return True
    except Exception as e:
        print(f"❌ 重试机制测试失败: {e}")
        return False

def test_json_validation():
    """测试JSON验证"""
    print("\n=== 测试JSON验证 ===")
    
    # 测试有效JSON
    valid_data = {"key": "value", "nested": {"data": [1, 2, 3]}}
    if syncSeerH5Data.validate_json_data(valid_data):
        print("✅ 有效JSON验证通过")
    else:
        print("❌ 有效JSON验证失败")
        return False
    
    # 测试无效数据
    invalid_data = "not a dict"
    if not syncSeerH5Data.validate_json_data(invalid_data):
        print("✅ 无效数据验证通过")
    else:
        print("❌ 无效数据验证失败")
        return False
    
    return True

def test_backup_restore():
    """测试备份和恢复功能"""
    print("\n=== 测试备份和恢复功能 ===")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
        test_data = {"test": "data", "version": 1}
        json.dump(test_data, temp_file, indent=2)
        temp_file_path = temp_file.name
    
    try:
        # 测试备份
        if syncSeerH5Data.backup_file(temp_file_path):
            print("✅ 文件备份成功")
        else:
            print("❌ 文件备份失败")
            return False
        
        # 修改原文件
        with open(temp_file_path, 'w') as f:
            f.write("corrupted data")
        
        # 测试恢复
        if syncSeerH5Data.restore_backup(temp_file_path):
            print("✅ 文件恢复成功")
            
            # 验证恢复的内容
            with open(temp_file_path, 'r') as f:
                restored_data = json.load(f)
            
            if restored_data == test_data:
                print("✅ 恢复内容验证通过")
                return True
            else:
                print("❌ 恢复内容验证失败")
                return False
        else:
            print("❌ 文件恢复失败")
            return False
    
    finally:
        # 清理临时文件
        for path in [temp_file_path, f"{temp_file_path}.backup"]:
            if os.path.exists(path):
                os.remove(path)

def test_safe_file_operations():
    """测试安全文件操作"""
    print("\n=== 测试安全文件操作 ===")
    
    # 测试安全目录创建
    test_dir = "/tmp/test_fault_tolerance_dir"
    if syncSeerH5Data.safe_make_dirs(test_dir):
        print("✅ 安全目录创建成功")
        
        if os.path.exists(test_dir):
            print("✅ 目录存在验证通过")
            os.rmdir(test_dir)  # 清理
            return True
        else:
            print("❌ 目录存在验证失败")
            return False
    else:
        print("❌ 安全目录创建失败")
        return False

def test_version_operations():
    """测试版本文件操作"""
    print("\n=== 测试版本文件操作 ===")
    
    # 保存当前工作目录
    original_cwd = os.getcwd()
    
    # 切换到临时目录进行测试
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        test_data = {
            "files": {
                "resource": {
                    "config": {
                        "json": {
                            "test.json": "hash123"
                        }
                    }
                }
            },
            "version": "1.0.0"
        }
        
        try:
            # 测试保存版本数据
            if syncSeerH5Data.save_local_version(test_data):
                print("✅ 版本数据保存成功")
            else:
                print("❌ 版本数据保存失败")
                return False
            
            # 测试加载版本数据
            loaded_data = syncSeerH5Data.load_local_version()
            if loaded_data == test_data:
                print("✅ 版本数据加载验证通过")
                return True
            else:
                print("❌ 版本数据加载验证失败")
                print(f"   预期: {test_data}")
                print(f"   实际: {loaded_data}")
                return False
        
        finally:
            # 恢复原工作目录
            os.chdir(original_cwd)

def main():
    """运行所有测试"""
    print("开始容错功能测试...\n")
    
    tests = [
        ("重试机制", test_retry_mechanism),
        ("JSON验证", test_json_validation),
        ("备份恢复", test_backup_restore),
        ("安全文件操作", test_safe_file_operations),
        ("版本文件操作", test_version_operations),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 所有容错功能测试通过！")
        return True
    else:
        print("⚠️  部分测试失败，请检查实现")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)