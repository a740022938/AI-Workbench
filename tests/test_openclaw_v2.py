#!/usr/bin/env python3
"""
OpenClaw分身能力扩张v2测试脚本
测试新增的无弹窗选框控制动作
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.openclaw_bridge import execute_action_with_policy

def test_action(action_name, context=None):
    """测试单个动作"""
    print(f"\n{'='*60}")
    print(f"测试动作: {action_name}")
    print(f"上下文: {context}")
    
    # 模拟一个MainWindow对象（简化版）
    class MockMainWindow:
        def __init__(self):
            self.boxes = [
                [0, 0.5, 0.5, 0.2, 0.2],  # 类别0，中心(0.5,0.5)，宽高(0.2,0.2)
                [1, 0.3, 0.3, 0.15, 0.15], # 类别1，中心(0.3,0.3)，宽高(0.15,0.15)
                [2, 0.7, 0.7, 0.1, 0.1],   # 类别2，中心(0.7,0.7)，宽高(0.1,0.1)
            ]
            self.selected_idx = 0
            self.current_class_names = ["1W", "2W", "3W"]
            
        def execute_action(self, action_name, **kwargs):
            print(f"  execute_action被调用: {action_name}, kwargs={kwargs}")
            
            # 模拟动作执行
            if action_name == "select_next_box":
                if self.boxes:
                    self.selected_idx = (self.selected_idx + 1) % len(self.boxes)
                    return {'success': True, 'message': f'已选中下一个框，当前选中: {self.selected_idx}'}
                return {'success': False, 'message': '没有标注框'}
                
            elif action_name == "select_prev_box":
                if self.boxes:
                    self.selected_idx = (self.selected_idx - 1) % len(self.boxes)
                    return {'success': True, 'message': f'已选中上一个框，当前选中: {self.selected_idx}'}
                return {'success': False, 'message': '没有标注框'}
                
            elif action_name == "select_box_by_index":
                box_index = kwargs.get('box_index')
                if box_index is not None and 0 <= box_index < len(self.boxes):
                    self.selected_idx = box_index
                    return {'success': True, 'message': f'已按索引选中框: {box_index}'}
                return {'success': False, 'message': f'无效的框索引: {box_index}'}
                
            elif action_name == "delete_box_by_index":
                box_index = kwargs.get('box_index')
                if box_index is not None and 0 <= box_index < len(self.boxes):
                    # 模拟删除
                    deleted_class = self.boxes[box_index][0]
                    self.boxes.pop(box_index)
                    if self.selected_idx == box_index:
                        self.selected_idx = None
                    elif self.selected_idx is not None and self.selected_idx > box_index:
                        self.selected_idx -= 1
                    return {'success': True, 'message': f'已删除框 #{box_index} (类别: {deleted_class})'}
                return {'success': False, 'message': f'无效的框索引: {box_index}'}
                
            elif action_name == "analyze_box_by_index":
                box_index = kwargs.get('box_index')
                if box_index is not None and 0 <= box_index < len(self.boxes):
                    return {'success': True, 'message': f'已分析框 #{box_index}'}
                return {'success': False, 'message': f'无效的框索引: {box_index}'}
                
            elif action_name == "edit_box_by_index":
                box_index = kwargs.get('box_index')
                if box_index is not None and 0 <= box_index < len(self.boxes):
                    return {'success': True, 'message': f'已打开框 #{box_index} 的编辑窗口'}
                return {'success': False, 'message': f'无效的框索引: {box_index}'}
                
            elif action_name == "change_box_class_by_index":
                box_index = kwargs.get('box_index')
                class_name = kwargs.get('class_name')
                if (box_index is not None and 0 <= box_index < len(self.boxes) and 
                    class_name is not None and class_name in self.current_class_names):
                    # 模拟修改类别
                    old_class = self.boxes[box_index][0]
                    new_class_id = self.current_class_names.index(class_name)
                    self.boxes[box_index][0] = new_class_id
                    return {'success': True, 'message': f'已修改框 #{box_index} 类别: {old_class} -> {class_name}'}
                return {'success': False, 'message': f'无效参数: box_index={box_index}, class_name={class_name}'}
                
            else:
                return {'success': False, 'message': f'不支持的动作: {action_name}'}
    
    # 创建模拟对象
    mock_window = MockMainWindow()
    
    # 执行动作
    result = execute_action_with_policy(action_name, mock_window, context)
    
    print(f"执行结果:")
    print(f"  成功: {result.get('success')}")
    print(f"  动作: {result.get('action_name')}")
    print(f"  决策: {result.get('decision')}")
    print(f"  消息: {result.get('telegram_response', '无消息')}")
    
    if not result.get('success'):
        print(f"  错误: {result.get('error', '无错误信息')}")
    
    return result

def main():
    """主测试函数"""
    print("OpenClaw分身能力扩张v2测试")
    print("测试新增的无弹窗选框控制动作")
    
    # 测试基础动作
    test_action("select_next_box")
    test_action("select_prev_box")
    
    # 测试带参数的动作
    test_action("select_box_by_index", {"box_index": 1})
    test_action("select_box_by_index", {"box_index": 5})  # 无效索引
    
    test_action("delete_box_by_index", {"box_index": 0})
    test_action("delete_box_by_index", {"box_index": 5})  # 无效索引
    
    test_action("analyze_box_by_index", {"box_index": 1})
    test_action("edit_box_by_index", {"box_index": 1})
    test_action("change_box_class_by_index", {"box_index": 1, "class_name": "2W"})
    test_action("change_box_class_by_index", {"box_index": 1, "class_name": "InvalidClass"})  # 无效类别
    
    print(f"\n{'='*60}")
    print("测试完成!")

if __name__ == "__main__":
    main()