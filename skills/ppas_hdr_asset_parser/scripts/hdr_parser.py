import os
from pathlib import Path
import json

class HDRAssetParser:
    """
    环境光资产流扫描引擎 (HDR Asset Parser Engine)
    
    用于深层扫描给定的网络/本地目录，将其按子文件夹分类，
    并提取 .hdr/.exr 原文件及对应的 .jpg/.png 预览图。
    """
    
    def __init__(self, root_path=r"X:\AI_Automation\AI_Asset_lib\hdr_lighting_pic_for_lighting"):
        self.root_path = Path(root_path)
        self.valid_hdr_exts = {".hdr", ".exr"}
        self.valid_thumb_exts = {".jpg", ".png", ".jpeg"}

    def scan_assets(self, force_rebuild=False):
        """
        执行资产扫描
        :param force_rebuild: 强制跳过缓存做底层慢盘扫描
        :return: dict 结构的分类字典
        """
        cache_file = self.root_path / "hdr_cache.json"
        
        if not force_rebuild and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
            
        asset_dict = {}
        
        if not self.root_path.exists() or not self.root_path.is_dir():
            print(f"[HDR_Parser] 严重警告: 无法挂载配置目标磁盘路径 '{self.root_path}'")
            return asset_dict

        # 遍历根目录下的子文件夹（第一级作为 Category）
        for category_dir in self.root_path.iterdir():
            if not category_dir.is_dir():
                continue
                
            category_name = category_dir.name
            asset_list = []
            
            # 使用一个字典来暂存同前缀的文件，以方便配对 HDR 和 JPG
            file_map = {}
            
            # 扫描并分类收集 (改进的 rglob 检索)
            for file_path in category_dir.rglob('*.*'):
                if file_path.is_file():
                    if file_path.stem.lower().endswith("_blur"):
                        continue
                        
                    ext = file_path.suffix.lower()
                    base_name = file_path.stem
                    
                    if base_name not in file_map:
                        file_map[base_name] = {"hdr": None, "thumb": None}
                        
                    if ext in self.valid_hdr_exts:
                        file_map[base_name]["hdr"] = str(file_path.absolute())
                    elif ext in self.valid_thumb_exts:
                        file_map[base_name]["thumb"] = str(file_path.absolute())

            for base_name, paths in file_map.items():
                if paths["hdr"]:
                    asset_list.append({
                        "name": base_name,
                        "hdr_path": paths["hdr"],
                        "thumbnail_path": paths["thumb"]
                    })
                    
            if asset_list:
                asset_list.sort(key=lambda x: x["name"])
                asset_dict[category_name] = asset_list
                
        # 写回热缓存
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(asset_dict, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[HDR_Parser] 热写缓存失败: {e}")
            
        return asset_dict

if __name__ == "__main__":
    # 测试执行点
    parser = HDRAssetParser()
    result = parser.scan_assets()
    print(f"成功扫到了以下归类: {list(result.keys())}")
    print(json.dumps(result, indent=4, ensure_ascii=False))
