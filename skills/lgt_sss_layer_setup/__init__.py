bl_info = {
    "name": "LGT SSS Layer Setup",
    "description": "一键创建 SSS 场景、渲染层并挂载智能拦截器，支持原生预览与完美后台渲染。",
    "author": "Pipeline AI",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "category": "Lighting",
}

from .scripts.setup_operator import classes, register, unregister