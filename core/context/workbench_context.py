"""
workbench_context.py - 运行期总账本

职责：集中管理 AI Workbench 的运行期状态，为后续架构重构做准备。
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image


@dataclass
class WorkbenchContext:
    """AI Workbench 运行期状态总账本"""
    
    # 配置相关
    config_data: Dict[str, Any] = field(default_factory=dict)
    valid_ext: Tuple[str, ...] = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
    
    # 类别管理
    default_class_names: List[str] = field(default_factory=list)
    current_class_names: List[str] = field(default_factory=list)
    class_source_name: str = "默认麻将类别"
    
    # 路径配置
    image_dir: str = ""
    label_dir: str = ""
    auto_save: bool = True
    
    # 图片文件列表
    image_files: List[str] = field(default_factory=list)
    current_index: int = 0
    current_image_name: str = ""
    
    # 图片数据
    original_image: Optional[Image.Image] = None
    display_image: Optional[Image.Image] = None
    current_tk: Optional[Any] = None  # 当前显示的Tkinter图片对象
    
    # 显示参数
    img_offset_x: int = 0
    img_offset_y: int = 0
    display_w: int = 0
    display_h: int = 0
    orig_w: int = 0
    orig_h: int = 0
    
    # 标注框管理
    boxes: List[List[float]] = field(default_factory=list)  # [cls_id, cx, cy, w, h]
    selected_idx: Optional[int] = None
    
    # 自动推理缓存
    last_auto_infer_image: Optional[str] = None
    
    # 画布交互状态
    drag_mode: str = "select"  # select / move / resize
    dragging: bool = False
    start_x: int = 0
    start_y: int = 0
    temp_x: int = 0
    temp_y: int = 0
    move_offset_x: int = 0
    move_offset_y: int = 0
    active_handle: Optional[str] = None  # nw, n, ne, w, e, sw, s, se
    handle_size: int = 8
    
    @classmethod
    def create(cls, config_data: Dict[str, Any], default_class_names: List[str]) -> 'WorkbenchContext':
        """创建新的运行期上下文"""
        ctx = cls()
        ctx.config_data = config_data or {}
        ctx.default_class_names = list(default_class_names)
        
        # 从配置初始化路径
        paths = ctx.config_data.get("paths", {})
        ctx.image_dir = paths.get("image_dir", "")
        ctx.label_dir = paths.get("label_dir", "")
        
        # 从配置初始化行为
        behavior = ctx.config_data.get("behavior", {})
        ctx.auto_save = behavior.get("auto_save_on_navigate", True)
        
        # 初始化类别列表
        ctx.current_class_names = list(default_class_names)
        ctx.class_source_name = "默认麻将类别"
        
        return ctx
    
    def set_class_names(self, class_names: List[str], source_name: str) -> None:
        """设置当前类别列表和来源"""
        self.current_class_names = list(class_names)
        self.class_source_name = source_name
    
    def get_class_name(self, cls_id: int) -> str:
        """根据类别ID获取类别名称"""
        try:
            cls_id = int(cls_id)
            if 0 <= cls_id < len(self.current_class_names):
                return self.current_class_names[cls_id]
        except (ValueError, TypeError):
            pass
        return f"cls_{cls_id}"
    
    def get_class_id(self, class_name: str) -> Optional[int]:
        """根据类别名称获取类别ID"""
        try:
            if class_name in self.current_class_names:
                return self.current_class_names.index(class_name)
        except ValueError:
            pass
        return None