#!/usr/bin/env python3
"""
OpenClaw分身能力扩张v2第二刀测试脚本
测试新增的无弹窗框微调动作
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
            self.refresh_called = False
            self.redraw_called = False
            self.update_panel_called = False
            
        def refresh_box_list(self):
            self.refresh_called = True
            
        def redraw_boxes(self):
            self.redraw_called = True
            
        def update_selected_box_panel(self):
            self.update_panel_called = True
            
        def set_status(self, text):
            print(f"  状态栏: {text}")
            
        def execute_action(self, action_name, **kwargs):
            print(f"  execute_action被调用: {action_name}, kwargs={kwargs}")
            
            # 模拟动作执行
            if action_name == "move_box_by_index":
                box_index = kwargs.get('box_index')
                dx = kwargs.get('dx', 0.0)
                dy = kwargs.get('dy', 0.0)
                
                if box_index is not None and 0 <= box_index < len(self.boxes):
                    # 模拟移动
                    box = self.boxes[box_index]
                    cls_id, cx, cy, w, h = box
                    new_cx = max(0.0, min(1.0, cx + dx))
                    new_cy = max(0.0, min(1.0, cy + dy))
                    self.boxes[box_index] = [cls_id, new_cx, new_cy, w, h]
                    
                    # 模拟UI刷新
                    if self.selected_idx == box_index:
                        self.refresh_box_list()
                        self.redraw_boxes()
                        self.update_selected_box_panel()
                    
                    return {'success': True, 'message': f'已移动框 #{box_index} (dx={dx:.3f}, dy={dy:.3f})'}
                return {'success': False, 'message': f'无效的框索引: {box_index}'}
                
            elif action_name == "resize_box_by_index":
                box_index = kwargs.get('box_index')
                dw = kwargs.get('dw', 0.0)
                dh = kwargs.get('dh', 0.0)
                
                if box_index is not None and 0 <= box_index < len(self.boxes):
                    # 模拟调整大小
                    box = self.boxes[box_index]
                    cls_id, cx, cy, w, h = box
                    new_w = max(0.01, min(1.0, w + dw))
                    new_h = max(0.01, min(1.0, h + dh))
                    self.boxes[box_index] = [cls_id, cx, cy, new_w, new_h]
                    
                    # 模拟UI刷新
                    if self.selected_idx == box_index:
                        self.refresh_box_list()
                        self.redraw_boxes()
                        self.update_selected_box_panel()
                    
                    return {'success': True, 'message': f'已调整框 #{box_index} 大小 (dw={dw:.3f}, dh={dh:.3f})'}
                return {'success': False, 'message': f'无效的框索引: {box_index}'}
                
            elif action_name == "nudge_box_by_index":
                box_index = kwargs.get('box_index')
                direction = kwargs.get('direction')
                amount = kwargs.get('amount', 0.01)
                
                direction_map = {
                    'up': (0, -amount),
                    'down': (0, amount),
                    'left': (-amount, 0),
                    'right': (amount, 0)
                }
                
                if (box_index is not None and 0 <= box_index < len(self.boxes) and 
                    direction in direction_map):
                    
                    dx, dy = direction_map[direction]
                    box = self.boxes[box_index]
                    cls_id, cx, cy, w, h = box
                    new_cx = max(0.0, min(1.0, cx + dx))
                    new_cy = max(0.0, min(1.0, cy + dy))
                    self.boxes[box_index] = [cls_id, new_cx, new_cy, w, h]
                    
                    # 模拟UI刷新
                    if self.selected_idx == box_index:
                        self.refresh_box_list()
                        self.redraw_boxes()
                        self.update_selected_box_panel()
                    
                    return {'success': True, 'message': f'已微调框 #{box_index} 向{direction}移动 {amount:.3f}'}
                return {'success': False, 'message': f'无效参数: box_index={box_index}, direction={direction}'}
                
            elif action_name == "set_box_coords_by_index":
                box_index = kwargs.get('box_index')
                cx = kwargs.get('cx')
                cy = kwargs.get('cy')
                w = kwargs.get('w')
                h = kwargs.get('h')
                
                if box_index is not None and 0 <= box_index < len(self.boxes):
                    box = self.boxes[box_index]
                    cls_id, old_cx, old_cy, old_w, old_h = box
                    
                    # 更新坐标
                    new_cx = cx if cx is not None else old_cx
                    new_cy = cy if cy is not None else old_cy
                    new_w = w if w is not None else old_w
                    new_h = h if h is not None else old_h
                    
                    self.boxes[box_index] = [cls_id, new_cx, new_cy, new_w, new_h]
                    
                    # 模拟UI刷新
                    if self.selected_idx == box_index:
                        self.refresh_box_list()
                        self.redraw_boxes()
                        self.update_selected_box_panel()
                    
                    changes = []
                    if cx is not None and cx != old_cx:
                        changes.append(f"cx: {old_cx:.3f}→{new_cx:.3f}")
                    if cy is not None and cy != old_cy:
                        changes.append(f"cy: {old_cy:.3f}→{new_cy:.3f}")
                    if w is not None and w != old_w:
                        changes.append(f"w: {old_w:.3f}→{new_w:.3f}")
                    if h is not None and h != old_h:
                        changes.append(f"h: {old_h:.3f}→{new_h:.3f}")
                    
                    if changes:
                        msg = f'已设置框 #{box_index} 坐标 ({", ".join(changes)})'
                    else:
                        msg = f'框 #{box_index} 坐标未变化'
                    
                    return {'success': True, 'message': msg}
                return {'success': False, 'message': f'无效的框索引: {box_index}'}
                
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
    
    # 检查UI刷新是否被调用
    if mock_window.refresh_called:
        print(f"  UI刷新: refresh_box_list() 被调用")
    if mock_window.redraw_called:
        print(f"  UI刷新: redraw_boxes() 被调用")
    if mock_window.update_panel_called:
        print(f"  UI刷新: update_selected_box_panel() 被调用")
    
    if not result.get('success'):
        print(f"  错误: {result.get('error', '无错误信息')}")
    
    return result

def main():
    """主测试函数"""
    print("OpenClaw分身能力扩张v2第二刀测试")
    print("测试新增的无弹窗框微调动作")
    
    # 测试移动动作
    test_action("move_box_by_index", {"box_index": 1, "dx": 0.05, "dy": -0.03})
    test_action("move_box_by_index", {"box_index": 5, "dx": 0.05, "dy": -0.03})  # 无效索引
    
    # 测试调整大小动作
    test_action("resize_box_by_index", {"box_index": 1, "dw": 0.02, "dh": 0.01})
    test_action("resize_box_by_index", {"box_index": 5, "dw": 0.02, "dh": 0.01})  # 无效索引
    
    # 测试微调动作
    test_action("nudge_box_by_index", {"box_index": 1, "direction": "up", "amount": 0.02})
    test_action("nudge_box_by_index", {"box_index": 1, "direction": "right"})  # 使用默认amount
    test_action("nudge_box_by_index", {"box_index": 1, "direction": "invalid"})  # 无效方向
    
    # 测试设置坐标动作
    test_action("set_box_coords_by_index", {"box_index": 1, "cx": 0.4, "cy": 0.4})
    test_action("set_box_coords_by_index", {"box_index": 1, "w": 0.18, "h": 0.16})
    test_action("set_box_coords_by_index", {"box_index": 1, "cx": 0.45, "cy": 0.45, "w": 0.17, "h": 0.15})
    test_action("set_box_coords_by_index", {"box_index": 5, "cx": 0.4})  # 无效索引
    
    print(f"\n{'='*60}")
    print("测试完成!")

if __name__ == "__main__":
    main()