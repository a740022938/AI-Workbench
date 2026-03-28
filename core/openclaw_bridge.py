import json
import os
import subprocess
from datetime import datetime

# 导入操作决策规范
try:
    from core.action_policy import (
        get_action_policy,
        get_all_policies,
        get_policy_summary,
        check_action_allowed,
        get_risk_summary
    )
    ACTION_POLICY_AVAILABLE = True
except ImportError:
    ACTION_POLICY_AVAILABLE = False
    # 定义占位函数
    def get_action_policy(action_name):
        return None
    def get_all_policies():
        return {}
    def get_policy_summary(action_name, **kwargs):
        return f"策略模块未加载: {action_name}"
    def check_action_allowed(action_name, context):
        return {
            "allowed": True,
            "action_name": action_name,
            "policy": None,
            "reasons": ["策略模块未加载，跳过检查"],
            "suggestions": []
        }
    def get_risk_summary():
        return {"error": "策略模块未加载"}

# 导入分身任务中心
try:
    from core.task_center import (
        get_task_center,
        get_task_executor,
        create_task_from_template,
        get_task_summary_telegram
    )
    TASK_CENTER_AVAILABLE = True
except ImportError:
    TASK_CENTER_AVAILABLE = False
    # 定义占位函数
    def get_task_center():
        return None
    def get_task_executor(main_window=None):
        return None
    def create_task_from_template(template_name, **kwargs):
        return None
    def get_task_summary_telegram(task):
        return "任务中心模块未加载"


BRIDGE_DIR = r"./openclaw_bridge"


def _ensure_bridge_dir():
    os.makedirs(BRIDGE_DIR, exist_ok=True)


def _box_lines(boxes, class_names):
    lines = []
    for i, box in enumerate(boxes):
        cls_id, cx, cy, w, h = box
        cls_name = class_names[cls_id] if 0 <= cls_id < len(class_names) else str(cls_id)
        lines.append(
            f"框{i}: 类别={cls_name}, cls_id={cls_id}, cx={cx:.6f}, cy={cy:.6f}, w={w:.6f}, h={h:.6f}"
        )
    return "\n".join(lines) if lines else "当前没有标注框"


def build_prompt(image_path, label_path, boxes, selected_idx, class_names):
    selected_text = "当前未选中任何框"
    if selected_idx is not None and 0 <= selected_idx < len(boxes):
        cls_id, cx, cy, w, h = boxes[selected_idx]
        cls_name = class_names[cls_id] if 0 <= cls_id < len(class_names) else str(cls_id)
        selected_text = (
            f"索引={selected_idx}, 类别={cls_name}, "
            f"cx={cx:.6f}, cy={cy:.6f}, w={w:.6f}, h={h:.6f}"
        )

    prompt = f"""你现在是一个“麻将YOLO标注分析助手”。

请根据下面这张当前样本的信息，给出中文分析建议。
你的任务：
1. 判断当前图像的标注是否存在明显风险
2. 判断当前选中框是否可疑
3. 判断是否建议标记为 bad_case
4. 给出最多 5 条简洁建议
5. 如果没有明显问题，也请明确说明

【图片路径】
{image_path}

【标签路径】
{label_path}

【类别列表】
{", ".join(class_names)}

【当前所有框】
{_box_lines(boxes, class_names)}

【当前选中框】
{selected_text}

请按下面格式输出：

【总结】
...

【可疑点】
...

【建议】
1. ...
2. ...

【bad_case建议】
是/否 + 原因
"""
    return prompt


def analyze_with_openclaw(image_path, label_path, boxes, selected_idx, class_names, agent_name="main"):
    _ensure_bridge_dir()

    request = {
        "image_path": image_path,
        "label_path": label_path,
        "boxes": boxes,
        "selected_idx": selected_idx,
        "class_names": class_names,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "agent": agent_name,
    }

    request_path = os.path.join(BRIDGE_DIR, "request.json")
    response_path = os.path.join(BRIDGE_DIR, "response.txt")

    with open(request_path, "w", encoding="utf-8") as f:
        json.dump(request, f, indent=2, ensure_ascii=False)

    prompt = build_prompt(image_path, label_path, boxes, selected_idx, class_names)

    try:
        result = subprocess.run(
            ["openclaw", "agent", "--agent", agent_name, "--message", prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180
        )
    except Exception as e:
        return False, f"调用 OpenClaw 失败：{e}"

    output = (result.stdout or "").strip()
    err = (result.stderr or "").strip()

    if result.returncode != 0:
        return False, err or output or "OpenClaw 调用失败"

    with open(response_path, "w", encoding="utf-8") as f:
        f.write(output)

    return True, output or "OpenClaw 未返回内容"


def execute_workbench_action(action_name, main_window=None, **kwargs):
    """
    OpenClaw 调用工作台动作的统一桥接
    
    参数:
        action_name: 动作名称
        main_window: MainWindow 实例（可选，如果为None则尝试从全局获取）
        **kwargs: 额外参数
        
    返回:
        dict: 执行结果
    """
    if main_window is None:
        # 尝试从全局或上下文获取 MainWindow 实例
        # 这里需要根据实际项目架构调整
        return {
            'success': False,
            'action': action_name,
            'message': '未提供 MainWindow 实例，无法执行动作',
            'error': 'MainWindow 实例为 None'
        }
    
    # 检查是否支持 execute_action 方法
    if not hasattr(main_window, 'execute_action'):
        return {
            'success': False,
            'action': action_name,
            'message': 'MainWindow 不支持 execute_action 方法',
            'error': 'execute_action 方法不存在'
        }
    
    # 调用统一动作入口
    try:
        return main_window.execute_action(action_name, **kwargs)
    except Exception as e:
        return {
            'success': False,
            'action': action_name,
            'message': f'执行动作时发生异常: {action_name}',
            'error': str(e)
        }


def test_execute_action(main_window, action_name):
    """
    测试调用 execute_action 方法
    
    参数:
        main_window: MainWindow 实例
        action_name: 要测试的动作名称
        
    返回:
        bool: 是否成功
    """
    print(f"[OpenClaw桥接测试] 尝试调用动作: {action_name}")
    
    if not hasattr(main_window, 'execute_action'):
        print("[错误] MainWindow 没有 execute_action 方法")
        return False
    
    result = main_window.execute_action(action_name)
    
    print(f"[结果] 成功: {result['success']}")
    print(f"[消息] {result['message']}")
    if result['error']:
        print(f"[错误] {result['error']}")
    
    return result['success']


# ==================== OpenClaw 分身背包 ====================
# 轻量级背包系统，用于存储动作映射、上下文快照和安全规则
openclaw_backpack = {
    'action_map': {
        'prev_image': '切换到上一张图片',
        'next_image': '切换到下一张图片',
        'save_current_labels': '保存当前标注',
        'delete_selected_box': '删除选中框',
        'copy_labels_from_previous_image': '复制上一张图片标注',
        'run_openclaw_analysis': '启动 OpenClaw 分析'
    },
    'context_snapshot': {
        'last_image': None,
        'last_boxes_count': 0,
        'last_action_time': None,
        'current_state': 'idle'
    },
    'last_result': None,
    'safety_rules': {
        'allow_delete': False,           # 是否允许删除操作
        'max_actions_per_minute': 10,    # 每分钟最大动作数
        'require_confirmation': ['delete_selected_box', 'copy_labels_from_previous_image'],
        'blocked_actions': []
    }
}
# ==================== OpenClaw 分身背包结束 ====================


def get_openclaw_status_summary():
    """
    获取 OpenClaw 桥接层状态摘要
    
    返回:
        dict: OpenClaw 状态摘要
    """
    from datetime import datetime
    
    # 更新上下文快照中的时间
    if openclaw_backpack['context_snapshot']['last_action_time'] is None:
        openclaw_backpack['context_snapshot']['last_action_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 构建状态摘要
    summary = {
        'role': 'OpenClaw 桥接层',
        'current_status': openclaw_backpack['context_snapshot'].get('current_state', 'idle'),
        'last_action': openclaw_backpack['context_snapshot'].get('last_action_time'),
        'last_result': openclaw_backpack.get('last_result'),
        'available_actions': {
            'total': len(openclaw_backpack['action_map']),
            'actions': list(openclaw_backpack['action_map'].keys()),
            'descriptions': openclaw_backpack['action_map']
        },
        'safety_rules_summary': {
            'allow_delete': openclaw_backpack['safety_rules'].get('allow_delete', False),
            'max_actions_per_minute': openclaw_backpack['safety_rules'].get('max_actions_per_minute', 10),
            'require_confirmation_count': len(openclaw_backpack['safety_rules'].get('require_confirmation', [])),
            'blocked_actions_count': len(openclaw_backpack['safety_rules'].get('blocked_actions', []))
        },
        'context_snapshot': openclaw_backpack['context_snapshot'],
        'backpack_info': {
            'has_action_map': bool(openclaw_backpack.get('action_map')),
            'has_context_snapshot': bool(openclaw_backpack.get('context_snapshot')),
            'has_last_result': openclaw_backpack.get('last_result') is not None,
            'has_safety_rules': bool(openclaw_backpack.get('safety_rules'))
        },
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return summary


def query_boss_status(main_window=None):
    """
    查询老板状态摘要（Telegram友好格式）
    
    参数:
        main_window: MainWindow 实例
        
    返回:
        str: Telegram适合显示的简短状态摘要
    """
    if main_window is None:
        return "❌ 未提供 MainWindow 实例，无法查询老板状态"
    
    # 检查是否支持状态摘要方法
    if not hasattr(main_window, 'get_boss_status_summary'):
        return "❌ MainWindow 不支持状态摘要查询"
    
    try:
        # 获取完整状态摘要
        summary = main_window.get_boss_status_summary()
        
        # 构建Telegram友好格式（使用文本替代emoji）
        lines = [
            "[老板] *老板状态摘要*",
            f"[图片] 当前图片: `{summary['current_image_name']}` ({summary['current_image_index']+1}/{summary['total_images']})",
            f"[框] 标注框: {summary['box_count']}个 (选中: {summary['selected_box_index'] or '无'})",
            f"[标签] 类别: {summary['class_names_count']}个",
            f"[背包] 背包: 工具{summary['backpack_data']['tools_count']}个, 资源{summary['backpack_data']['resources_count']}个, 笔记{summary['backpack_data']['notes_count']}条",
            f"[闪电] 最近动作: `{summary['recent_actions']['last_action'] or '无'}` (总数: {summary['recent_actions']['action_count']})",
            f"[齿轮] UI状态: 图片目录{'[OK]' if summary['ui_state']['has_image_dir'] else '[NO]'}, 标签目录{'[OK]' if summary['ui_state']['has_label_dir'] else '[NO]'}, 自动保存{'[OK]' if summary['ui_state']['auto_save_enabled'] else '[NO]'}",
            f"[时间] 更新时间: {summary['timestamp']}"
        ]
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ 查询老板状态失败: {str(e)}"


def query_openclaw_status():
    """
    查询 OpenClaw 状态摘要（Telegram友好格式）
    
    返回:
        str: Telegram适合显示的简短状态摘要
    """
    try:
        # 获取完整状态摘要
        summary = get_openclaw_status_summary()
        
        # 构建Telegram友好格式（使用文本替代emoji）
        lines = [
            "[机器人] *OpenClaw 状态摘要*",
            f"[图表] 当前状态: `{summary['current_status']}`",
            f"[时钟] 最后动作: {summary['last_action'] or '无'}",
            f"[手柄] 可用动作: {summary['available_actions']['total']}个",
            f"[盾牌] 安全规则: 删除{'[允许]' if summary['safety_rules_summary']['allow_delete'] else '[禁止]'}, 限速{summary['safety_rules_summary']['max_actions_per_minute']}/分钟",
            f"[警告] 需确认动作: {summary['safety_rules_summary']['require_confirmation_count']}个",
            f"[阻止] 阻止动作: {summary['safety_rules_summary']['blocked_actions_count']}个",
            f"[时间] 更新时间: {summary['timestamp']}"
        ]
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ 查询 OpenClaw 状态失败: {str(e)}"


def execute_status_query(query_type, main_window=None):
    """
    统一状态查询入口
    
    参数:
        query_type: 查询类型 ('boss_status' 或 'openclaw_status')
        main_window: MainWindow 实例（仅boss_status需要）
        
    返回:
        dict: 查询结果
    """
    if query_type == 'boss_status':
        result_text = query_boss_status(main_window)
        return {
            'success': not result_text.startswith('❌'),
            'query_type': query_type,
            'result': result_text,
            'error': None if not result_text.startswith('❌') else result_text
        }
    elif query_type == 'openclaw_status':
        result_text = query_openclaw_status()
        return {
            'success': not result_text.startswith('❌'),
            'query_type': query_type,
            'result': result_text,
            'error': None if not result_text.startswith('❌') else result_text
        }
    else:
        return {
            'success': False,
            'query_type': query_type,
            'result': f'未知查询类型: {query_type}',
            'error': f'支持的查询类型: boss_status, openclaw_status'
        }


# ==================== 操作决策规范桥接函数 ====================

def get_action_policy_info(action_name):
    """
    获取动作策略信息
    
    参数:
        action_name: 动作名称
        
    返回:
        dict: 策略信息
    """
    policy = get_action_policy(action_name)
    
    if not policy:
        return {
            "success": False,
            "action_name": action_name,
            "error": f"未知动作: {action_name}",
            "available_actions": list(get_all_policies().keys())
        }
    
    return {
        "success": True,
        "action_name": action_name,
        "policy": policy.to_dict(),
        "summary": get_policy_summary(action_name),
        "module_available": ACTION_POLICY_AVAILABLE
    }


def get_all_action_policies():
    """
    获取所有动作策略
    
    返回:
        dict: 所有策略信息
    """
    return {
        "success": True,
        "total_actions": len(get_all_policies()),
        "policies": get_all_policies(),
        "risk_summary": get_risk_summary(),
        "module_available": ACTION_POLICY_AVAILABLE
    }


def check_action_with_policy(action_name, context=None):
    """
    使用策略检查动作是否允许执行
    
    参数:
        action_name: 动作名称
        context: 执行上下文（可选）
        
    返回:
        dict: 检查结果
    """
    if context is None:
        context = {}
    
    result = check_action_allowed(action_name, context)
    
    return {
        "success": True,
        "action_name": action_name,
        "check_result": result,
        "module_available": ACTION_POLICY_AVAILABLE
    }


def get_policy_summary_telegram(action_name):
    """
    获取动作策略摘要（Telegram友好格式）
    
    参数:
        action_name: 动作名称
        
    返回:
        str: Telegram格式的策略摘要
    """
    policy = get_action_policy(action_name)
    
    if not policy:
        return f"❌ 未知动作: {action_name}"
    
    policy_dict = policy.to_dict()
    
    # 风险等级图标
    risk_icons = {
        "low": "🟢",
        "medium": "🟡", 
        "high": "🔴"
    }
    
    # 执行模式描述
    mode_descriptions = {
        "direct": "直接执行",
        "choose": "选择执行",
        "preview": "预览执行",
        "backup": "备份执行",
        "confirm": "确认执行"
    }
    
    lines = [
        f"[策略] *动作策略摘要: {action_name}*",
        f"[风险] 风险等级: {risk_icons.get(policy_dict['risk_level'], '⚪')} {policy_dict['risk_level'].upper()}",
        f"[模式] 执行模式: {mode_descriptions.get(policy_dict['execution_mode'], policy_dict['execution_mode'])}",
        f"[确认] 需要确认: {'✅是' if policy_dict['needs_confirmation'] else '❌否'}",
        f"[备份] 需要备份: {'✅是' if policy_dict['needs_backup'] else '❌否'}",
        f"[描述] {policy_dict['description']}",
        f"[摘要] {policy.get_summary()}"
    ]
    
    # 替换emoji为文本避免编码问题
    telegram_text = "\n".join(lines)
    telegram_text = telegram_text.replace("✅", "[是]").replace("❌", "[否]")
    telegram_text = telegram_text.replace("🟢", "[低风险]").replace("🟡", "[中风险]").replace("🔴", "[高风险]").replace("⚪", "[未知]")
    
    return telegram_text


# ==================== 远程执行前置判断 ====================

def evaluate_action_execution(action_name, main_window=None, context=None):
    """
    评估动作执行（前置判断）
    
    参数:
        action_name: 动作名称
        main_window: MainWindow 实例
        context: 执行上下文
        
    返回:
        dict: 评估结果和执行建议
    """
    if context is None:
        context = {}
    
    # 1. 检查动作策略
    policy = get_action_policy(action_name)
    if not policy:
        return {
            "success": False,
            "action_name": action_name,
            "decision": "reject",
            "reason": f"未知动作: {action_name}",
            "suggestion": f"支持的动作: {', '.join(get_all_policies().keys())}",
            "telegram_response": f"❌ 未知动作: {action_name}"
        }
    
    policy_dict = policy.to_dict()
    execution_mode = policy_dict["execution_mode"]
    risk_level = policy_dict["risk_level"]
    needs_confirmation = policy_dict["needs_confirmation"]
    needs_backup = policy_dict["needs_backup"]
    
    # 2. 根据执行模式决定处理方式
    if execution_mode == "direct":
        # 直接执行 - 低风险动作
        return {
            "success": True,
            "action_name": action_name,
            "decision": "execute_direct",
            "execution_mode": execution_mode,
            "risk_level": risk_level,
            "needs_confirmation": needs_confirmation,
            "needs_backup": needs_backup,
            "summary": policy.get_summary(),
            "telegram_response": f"✅ 执行 {action_name}: {policy.get_summary()}\n[风险: {risk_level.upper()}] 正在执行..."
        }
    
    elif execution_mode == "confirm":
        # 需要确认 - 高风险动作
        return {
            "success": True,
            "action_name": action_name,
            "decision": "require_confirmation",
            "execution_mode": execution_mode,
            "risk_level": risk_level,
            "needs_confirmation": needs_confirmation,
            "needs_backup": needs_backup,
            "summary": policy.get_summary(),
            "confirmation_prompt": f"⚠️ 高风险操作需要确认: {action_name}\n{policy.get_summary()}\n\n请回复 '确认执行 {action_name}' 来继续。",
            "telegram_response": f"⚠️ *需要确认*: {action_name}\n{policy.get_summary()}\n[风险: {risk_level.upper()}] 请回复 '确认执行 {action_name}' 来继续。"
        }
    
    elif execution_mode == "choose":
        # 提供选择 - 中风险动作
        choices = []
        if action_name == "copy_labels_from_previous_image":
            choices = ["追加", "替换", "取消"]
        
        return {
            "success": True,
            "action_name": action_name,
            "decision": "provide_choices",
            "execution_mode": execution_mode,
            "risk_level": risk_level,
            "needs_confirmation": needs_confirmation,
            "needs_backup": needs_backup,
            "summary": policy.get_summary(),
            "choices": choices,
            "choice_prompt": f"🔄 请选择执行方式: {action_name}\n{policy.get_summary()}\n\n可用选项: {', '.join(choices)}",
            "telegram_response": f"🔄 *请选择*: {action_name}\n{policy.get_summary()}\n[风险: {risk_level.upper()}] 请回复选项: {', '.join(choices)}"
        }
    
    elif execution_mode == "backup":
        # 备份执行 - 中风险动作
        return {
            "success": True,
            "action_name": action_name,
            "decision": "execute_with_backup",
            "execution_mode": execution_mode,
            "risk_level": risk_level,
            "needs_confirmation": needs_confirmation,
            "needs_backup": needs_backup,
            "summary": policy.get_summary(),
            "backup_note": "⚠️ 注意: 执行前将自动创建备份",
            "telegram_response": f"📋 执行 {action_name} (带备份)\n{policy.get_summary()}\n[风险: {risk_level.upper()}] 正在执行并创建备份..."
        }
    
    elif execution_mode == "preview":
        # 预览执行 - 未来扩展
        return {
            "success": True,
            "action_name": action_name,
            "decision": "provide_preview",
            "execution_mode": execution_mode,
            "risk_level": risk_level,
            "needs_confirmation": needs_confirmation,
            "needs_backup": needs_backup,
            "summary": policy.get_summary(),
            "preview_note": "👁️ 预览模式: 先查看效果再决定",
            "telegram_response": f"👁️ *预览模式*: {action_name}\n{policy.get_summary()}\n[风险: {risk_level.upper()}] 预览功能开发中..."
        }
    
    else:
        # 未知执行模式
        return {
            "success": False,
            "action_name": action_name,
            "decision": "reject",
            "reason": f"未知执行模式: {execution_mode}",
            "suggestion": "请联系管理员",
            "telegram_response": f"❌ 配置错误: 未知执行模式 {execution_mode}"
        }


def execute_action_with_policy(action_name, main_window=None, context=None, force_execute=False):
    """
    根据策略执行动作（完整流程）
    
    参数:
        action_name: 动作名称
        main_window: MainWindow 实例
        context: 执行上下文
        force_execute: 是否强制执行（跳过确认）
        
    返回:
        dict: 执行结果
    """
    # 1. 评估动作执行
    evaluation = evaluate_action_execution(action_name, main_window, context)
    
    if not evaluation["success"]:
        return evaluation
    
    decision = evaluation["decision"]
    
    # 2. 根据决策处理
    if decision == "execute_direct":
        # 直接执行
        if main_window and hasattr(main_window, 'execute_action'):
            try:
                # 传递context参数给execute_action
                result = main_window.execute_action(action_name, **(context or {}))
                return {
                    "success": True,
                    "action_name": action_name,
                    "decision": "executed",
                    "execution_mode": evaluation["execution_mode"],
                    "result": result,
                    "telegram_response": f"✅ *执行完成*: {action_name}\n{evaluation['summary']}\n结果: {result.get('message', '成功')}"
                }
            except Exception as e:
                return {
                    "success": False,
                    "action_name": action_name,
                    "decision": "execution_failed",
                    "error": str(e),
                    "telegram_response": f"❌ 执行失败: {action_name}\n错误: {str(e)}"
                }
        else:
            return {
                "success": False,
                "action_name": action_name,
                "decision": "cannot_execute",
                "reason": "MainWindow 实例不可用或缺少 execute_action 方法",
                "telegram_response": f"❌ 无法执行: MainWindow 不可用"
            }
    
    elif decision == "require_confirmation":
        # 需要确认
        if force_execute:
            # 强制执行（跳过确认）
            if main_window and hasattr(main_window, 'execute_action'):
                try:
                    # 传递context参数给execute_action
                    result = main_window.execute_action(action_name, **(context or {}))
                    return {
                        "success": True,
                        "action_name": action_name,
                        "decision": "executed_forced",
                        "execution_mode": evaluation["execution_mode"],
                        "result": result,
                        "telegram_response": f"⚠️ *强制执行完成*: {action_name}\n{evaluation['summary']}\n结果: {result.get('message', '成功')}"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "action_name": action_name,
                        "decision": "execution_failed",
                        "error": str(e),
                        "telegram_response": f"❌ 强制执行失败: {action_name}\n错误: {str(e)}"
                    }
            else:
                return {
                    "success": False,
                    "action_name": action_name,
                    "decision": "cannot_execute",
                    "reason": "MainWindow 实例不可用",
                    "telegram_response": f"❌ 无法执行: MainWindow 不可用"
                }
        else:
            # 返回确认提示
            return evaluation
    
    elif decision == "provide_choices":
        # 提供选择
        return evaluation
    
    elif decision == "execute_with_backup":
        # 备份执行（简化版，实际应创建备份）
        if main_window and hasattr(main_window, 'execute_action'):
            try:
                # 这里应该先创建备份，然后执行
                # 传递context参数给execute_action
                result = main_window.execute_action(action_name, **(context or {}))
                return {
                    "success": True,
                    "action_name": action_name,
                    "decision": "executed_with_backup_note",
                    "execution_mode": evaluation["execution_mode"],
                    "result": result,
                    "backup_note": "已执行（备份功能待实现）",
                    "telegram_response": f"📋 *执行完成*: {action_name}\n{evaluation['summary']}\n结果: {result.get('message', '成功')}\n备注: 备份功能待实现"
                }
            except Exception as e:
                return {
                    "success": False,
                    "action_name": action_name,
                    "decision": "execution_failed",
                    "error": str(e),
                    "telegram_response": f"❌ 执行失败: {action_name}\n错误: {str(e)}"
                }
        else:
            return {
                "success": False,
                "action_name": action_name,
                "decision": "cannot_execute",
                "reason": "MainWindow 实例不可用",
                "telegram_response": f"❌ 无法执行: MainWindow 不可用"
            }
    
    elif decision == "provide_preview":
        # 预览模式
        return evaluation
    
    else:
        # 其他决策
        return evaluation


def process_telegram_command(command, main_window=None, context=None):
    """
    处理Telegram命令（简化版）
    
    参数:
        command: 命令文本
        main_window: MainWindow 实例
        context: 执行上下文
        
    返回:
        str: Telegram响应文本
    """
    # 简单命令解析
    command = command.strip().lower()
    
    # 状态查询命令
    if command == "status" or command == "状态":
        return query_openclaw_status()
    
    elif command == "boss status" or command == "老板状态":
        return query_boss_status(main_window)
    
    elif command.startswith("policy "):
        # 查询策略
        action_name = command[7:].strip()
        return get_policy_summary_telegram(action_name)
    
    elif command.startswith("执行 "):
        # 执行动作
        action_name = command[3:].strip()
        result = execute_action_with_policy(action_name, main_window, context)
        return result.get("telegram_response", f"未知响应: {action_name}")
    
    elif command.startswith("确认执行 "):
        # 确认执行
        action_name = command[5:].strip()
        result = execute_action_with_policy(action_name, main_window, context, force_execute=True)
        return result.get("telegram_response", f"未知响应: {action_name}")
    
    elif command.startswith("task_") or command.startswith("任务") or command.startswith("创建"):
        # 任务命令
        return process_task_command(command, main_window)
    
    else:
        # 未知命令
        return f"❓ 未知命令: {command}\n可用命令:\n- status / 状态\n- boss status / 老板状态\n- policy <动作名>\n- 执行 <动作名>\n- 确认执行 <动作名>\n- 创建轻量标注任务 / task_create_light\n- 创建巡查任务 / task_create_inspection\n- 创建清理任务 / task_create_cleanup\n- 任务列表 / task_list\n- task_status <任务ID>\n- task_run <任务ID>"


# ==================== 分身任务中心桥接函数 ====================

def task_create_light_annotation(main_window=None, **kwargs):
    """
    创建轻量标注任务
    
    参数:
        main_window: MainWindow 实例
        **kwargs: 额外参数
        
    返回:
        dict: 创建结果
    """
    if not TASK_CENTER_AVAILABLE:
        return {
            "success": False,
            "error": "任务中心模块未加载",
            "telegram_response": "❌ 任务中心模块未加载"
        }
    
    try:
        task = create_task_from_template('light_annotation', **kwargs)
        
        if not task:
            return {
                "success": False,
                "error": "创建任务失败",
                "telegram_response": "❌ 创建轻量标注任务失败"
            }
        
        telegram_summary = get_task_summary_telegram(task)
        
        return {
            "success": True,
            "task_id": task.task_id,
            "task_name": task.task_name,
            "action_count": len(task.action_list),
            "telegram_response": f"✅ *任务创建成功*\n{telegram_summary}\n\n使用 'task_run {task.task_id}' 执行任务"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "telegram_response": f"❌ 创建任务异常: {str(e)}"
        }


def task_create_inspection(main_window=None, **kwargs):
    """
    创建巡查任务
    
    参数:
        main_window: MainWindow 实例
        **kwargs: 额外参数
        
    返回:
        dict: 创建结果
    """
    if not TASK_CENTER_AVAILABLE:
        return {
            "success": False,
            "error": "任务中心模块未加载",
            "telegram_response": "❌ 任务中心模块未加载"
        }
    
    try:
        task = create_task_from_template('inspection', **kwargs)
        
        if not task:
            return {
                "success": False,
                "error": "创建任务失败",
                "telegram_response": "❌ 创建巡查任务失败"
            }
        
        telegram_summary = get_task_summary_telegram(task)
        
        return {
            "success": True,
            "task_id": task.task_id,
            "task_name": task.task_name,
            "action_count": len(task.action_list),
            "telegram_response": f"✅ *任务创建成功*\n{telegram_summary}\n\n使用 'task_run {task.task_id}' 执行任务"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "telegram_response": f"❌ 创建任务异常: {str(e)}"
        }


def task_create_cleanup(main_window=None, **kwargs):
    """
    创建清理任务
    
    参数:
        main_window: MainWindow 实例
        **kwargs: 额外参数
        
    返回:
        dict: 创建结果
    """
    if not TASK_CENTER_AVAILABLE:
        return {
            "success": False,
            "error": "任务中心模块未加载",
            "telegram_response": "❌ 任务中心模块未加载"
        }
    
    try:
        task = create_task_from_template('cleanup', **kwargs)
        
        if not task:
            return {
                "success": False,
                "error": "创建任务失败",
                "telegram_response": "❌ 创建清理任务失败"
            }
        
        telegram_summary = get_task_summary_telegram(task)
        
        return {
            "success": True,
            "task_id": task.task_id,
            "task_name": task.task_name,
            "action_count": len(task.action_list),
            "telegram_response": f"✅ *任务创建成功*\n{telegram_summary}\n\n使用 'task_run {task.task_id}' 执行任务"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "telegram_response": f"❌ 创建任务异常: {str(e)}"
        }


def task_get(task_id, main_window=None):
    """
    获取任务信息
    
    参数:
        task_id: 任务ID
        main_window: MainWindow 实例
        
    返回:
        dict: 任务信息
    """
    if not TASK_CENTER_AVAILABLE:
        return {
            "success": False,
            "error": "任务中心模块未加载",
            "telegram_response": "❌ 任务中心模块未加载"
        }
    
    try:
        task_center = get_task_center()
        task = task_center.get_task(task_id)
        
        if not task:
            return {
                "success": False,
                "error": f"任务不存在: {task_id}",
                "telegram_response": f"❌ 任务不存在: {task_id}"
            }
        
        telegram_summary = get_task_summary_telegram(task)
        
        return {
            "success": True,
            "task_id": task.task_id,
            "task_name": task.task_name,
            "task_status": task.task_status.value,
            "progress": task.get_progress(),
            "telegram_response": telegram_summary
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "telegram_response": f"❌ 获取任务异常: {str(e)}"
        }


def task_list(main_window=None, status_filter=None):
    """
    列出所有任务
    
    参数:
        main_window: MainWindow 实例
        status_filter: 状态过滤
        
    返回:
        dict: 任务列表
    """
    if not TASK_CENTER_AVAILABLE:
        return {
            "success": False,
            "error": "任务中心模块未加载",
            "telegram_response": "❌ 任务中心模块未加载"
        }
    
    try:
        task_center = get_task_center()
        tasks = task_center.list_tasks(status_filter)
        
        if not tasks:
            return {
                "success": True,
                "task_count": 0,
                "tasks": [],
                "telegram_response": "📭 当前没有任务"
            }
        
        # 构建Telegram响应
        lines = [f"📋 *任务列表* (共{len(tasks)}个)"]
        
        for i, task in enumerate(tasks, 1):
            status_icon = {
                'pending': '⏳',
                'running': '▶️',
                'completed': '✅',
                'failed': '❌',
                'cancelled': '🚫'
            }.get(task['task_status'], '📋')
            
            lines.append(f"{i}. {status_icon} `{task['task_id']}` - {task['task_name']}")
            lines.append(f"   状态: {task['task_status']}, 进度: {task['progress']}")
        
        telegram_response = "\n".join(lines)
        telegram_response = telegram_response.replace("✅", "[完成]").replace("❌", "[失败]")
        telegram_response = telegram_response.replace("⏳", "[等待]").replace("▶️", "[运行]")
        telegram_response = telegram_response.replace("🚫", "[取消]").replace("📋", "[任务]")
        
        return {
            "success": True,
            "task_count": len(tasks),
            "tasks": tasks,
            "telegram_response": telegram_response
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "telegram_response": f"❌ 列出任务异常: {str(e)}"
        }


def task_run(task_id, main_window=None):
    """
    执行任务
    
    参数:
        task_id: 任务ID
        main_window: MainWindow 实例
        
    返回:
        dict: 执行结果
    """
    if not TASK_CENTER_AVAILABLE:
        return {
            "success": False,
            "error": "任务中心模块未加载",
            "telegram_response": "❌ 任务中心模块未加载"
        }
    
    if not main_window:
        return {
            "success": False,
            "error": "未提供 MainWindow 实例",
            "telegram_response": "❌ 未提供 MainWindow 实例，无法执行任务"
        }
    
    try:
        # 获取任务
        task_center = get_task_center()
        task = task_center.get_task(task_id)
        
        if not task:
            return {
                "success": False,
                "error": f"任务不存在: {task_id}",
                "telegram_response": f"❌ 任务不存在: {task_id}"
            }
        
        # 获取执行器并执行任务
        task_executor = get_task_executor(main_window)
        result = task_executor.execute_task(task)
        
        # 构建Telegram响应
        if result['success']:
            telegram_response = f"✅ *任务执行完成*\n任务: {task.task_name}\n状态: {result['task_status']}\n\n"
            
            summary = result['summary']
            telegram_response += f"进度: {summary['progress']}\n"
            telegram_response += f"完成动作: {summary['completed_actions']}/{summary['total_actions']}\n"
            
            if summary.get('execution_time'):
                telegram_response += f"执行时间: {summary['execution_time']:.1f}秒\n"
            
            # 添加中断提示
            if result['task_status'] == 'waiting_confirmation':
                telegram_response += f"\n⚠️ 等待确认: {task.pending_confirmation}\n回复 'task_confirm {task_id}' 确认执行"
            elif result['task_status'] == 'waiting_choice':
                telegram_response += f"\n🔄 等待选择: {task.pending_choice}\n可用选项: {', '.join(task.pending_choice_options)}"
        else:
            telegram_response = f"❌ *任务执行失败*\n任务: {task.task_name}\n错误: {result.get('error', '未知错误')}"
        
        result['telegram_response'] = telegram_response
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "telegram_response": f"❌ 执行任务异常: {str(e)}"
        }


def task_confirm(task_id, main_window=None, confirm=True):
    """
    确认任务动作
    
    参数:
        task_id: 任务ID
        main_window: MainWindow 实例
        confirm: 是否确认
        
    返回:
        dict: 确认结果
    """
    if not TASK_CENTER_AVAILABLE:
        return {
            "success": False,
            "error": "任务中心模块未加载",
            "telegram_response": "❌ 任务中心模块未加载"
        }
    
    try:
        task_center = get_task_center()
        task = task_center.get_task(task_id)
        
        if not task:
            return {
                "success": False,
                "error": f"任务不存在: {task_id}",
                "telegram_response": f"❌ 任务不存在: {task_id}"
            }
        
        task_executor = get_task_executor(main_window)
        result = task_executor.confirm_action(task, confirm)
        
        if result['success']:
            if confirm:
                telegram_response = f"✅ *已确认执行*\n动作: {result['action_name']}\n\n任务将继续执行..."
            else:
                telegram_response = f"🚫 *已取消执行*\n动作: {result['action_name']}\n\n任务已取消"
        else:
            telegram_response = f"❌ 确认失败: {result.get('error', '未知错误')}"
        
        result['telegram_response'] = telegram_response
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "telegram_response": f"❌ 确认任务异常: {str(e)}"
        }


def process_task_command(command, main_window=None):
    """
    处理任务命令
    
    参数:
        command: 命令文本
        main_window: MainWindow 实例
        
    返回:
        str: Telegram响应文本
    """
    command = command.strip().lower()
    
    # 任务创建命令
    if command == "task_create_light" or command == "创建轻量标注任务":
        result = task_create_light_annotation(main_window)
        return result.get("telegram_response", "未知响应")
    
    elif command == "task_create_inspection" or command == "创建巡查任务":
        result = task_create_inspection(main_window)
        return result.get("telegram_response", "未知响应")
    
    elif command == "task_create_cleanup" or command == "创建清理任务":
        result = task_create_cleanup(main_window)
        return result.get("telegram_response", "未知响应")
    
    # 任务列表命令
    elif command.startswith("task_list") or command.startswith("任务列表"):
        result = task_list(main_window)
        return result.get("telegram_response", "未知响应")
    
    # 任务状态命令
    elif command.startswith("task_status "):
        task_id = command[11:].strip()
        result = task_get(task_id, main_window)
        return result.get("telegram_response", "未知响应")
    
    # 任务执行命令
    elif command.startswith("task_run "):
        task_id = command[8:].strip()
        result = task_run(task_id, main_window)
        return result.get("telegram_response", "未知响应")
    
    # 任务确认命令
    elif command.startswith("task_confirm "):
        task_id = command[12:].strip()
        result = task_confirm(task_id, main_window, True)
        return result.get("telegram_response", "未知响应")
    
    # 任务取消命令
    elif command.startswith("task_cancel "):
        task_id = command[11:].strip()
        result = task_confirm(task_id, main_window, False)
        return result.get("telegram_response", "未知响应")
    
    else:
        # 未知任务命令
        return f"❓ 未知任务命令: {command}\n可用任务命令:\n- 创建轻量标注任务 / task_create_light\n- 创建巡查任务 / task_create_inspection\n- 创建清理任务 / task_create_cleanup\n- 任务列表 / task_list\n- task_status <任务ID>\n- task_run <任务ID>\n- task_confirm <任务ID>\n- task_cancel <任务ID>"