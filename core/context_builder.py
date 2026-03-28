import os


def build_context(main_window):
    """
    构建运行上下文
    
    优先从 context 读取运行时信息，保持向后兼容
    冲刺目标A：状态统一收口 - 确保所有状态读取都通过统一源
    """
    # 冲刺目标A：状态统一收口
    context = getattr(main_window, "context", None)
    
    if context is not None:
        # 从 WorkbenchContext 读取 - 统一状态源
        image_name = context.current_image_name
        image_dir = context.image_dir
        label_dir = context.label_dir
        boxes = context.boxes
        selected_idx = context.selected_idx
        
        # 冲刺目标B：类别真值源收口
        class_names = context.current_class_names
        # class_source_name 暂时不需要在返回结果中
    else:
        # 兼容旧逻辑：直接从 MainWindow 属性读取
        image_name = getattr(main_window, "current_image_name", "")
        image_dir = getattr(main_window, "image_dir", "")
        label_dir = getattr(main_window, "label_dir", "")
        boxes = getattr(main_window, "boxes", [])
        selected_idx = getattr(main_window, "selected_idx", None)
        
        # 冲刺目标B：类别真值源收口 - 优先使用current_class_names
        class_names = getattr(main_window, "current_class_names", None)
        if class_names is None:
            # 回退到空列表（不再依赖CLASS_NAMES）
            class_names = []
    
    image_path = os.path.join(image_dir, image_name) if image_name else ""

    # 冲刺目标D：主板健康摘要增强 - 包含主板健康信息
    mainboard_health = {}
    if hasattr(main_window, "get_mainboard_health_summary"):
        try:
            mainboard_health = main_window.get_mainboard_health_summary()
        except Exception:
            # 如果获取失败，不中断主要功能
            mainboard_health = {"error": "无法获取主板健康摘要"}

    return {
        "image_name": image_name,
        "image_path": image_path,
        "image_dir": image_dir,
        "label_dir": label_dir,
        "boxes": boxes,
        "selected_idx": selected_idx,
        "config": getattr(main_window, "config_data", {}),
        
        # 冲刺目标B：类别真值源收口
        "class_names": class_names,
        
        # 冲刺目标C：动作入口统一收口 - 包含动作执行信息
        "action_execution_info": {
            "has_execute_action": hasattr(main_window, "execute_action"),
            "backpack_action_count": getattr(main_window, "backpack", {}).get("runtime_data", {}).get("action_count", 0)
        },
        
        # 冲刺目标D：主板健康摘要增强
        "mainboard_health": mainboard_health,
        
        # 上下文构建信息
        "context_build_info": {
            "used_context_object": context is not None,
            "timestamp": os.path.getmtime(__file__) if os.path.exists(__file__) else 0
        }
    }