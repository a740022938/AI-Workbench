#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试人工处理入口功能
"""
import sys
import os
sys.path.insert(0, '.')

# 测试导入
print("=== 测试人工处理入口导入 ===")

try:
    from core.data_health_manager import DataHealthManager
    print("[OK] DataHealthManager 导入成功")
except Exception as e:
    print(f"[FAIL] DataHealthManager 导入失败: {e}")

try:
    from core.data_health_fixer import DataHealthFixer
    print("[OK] DataHealthFixer 导入成功")
except Exception as e:
    print(f"[FAIL] DataHealthFixer 导入失败: {e}")

try:
    # 测试从UI模块导入
    import ui.data_health_window
    print("[OK] data_health_window 导入成功")
except Exception as e:
    print(f"[FAIL] data_health_window 导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 导入测试完成 ===")