import os
import glob
import re
import stat

def get_latest_file(directory, pattern):
    """
    获取目录下符合 pattern 且版本号或修改时间最新的文件。
    例如: pattern = "ysj_chr_hamaguai_tex_texMaster_v*.blend"
    """
    search_path = os.path.join(directory, pattern)
    files = glob.glob(search_path)
    if not files: return None
    
    def sort_key(f):
        # Primary: Version number (_v001)
        match = re.search(r'_v(\d+)', os.path.basename(f))
        ver = int(match.group(1)) if match else 0
        # Secondary: Modification time
        mtime = os.path.getmtime(f)
        return (ver, mtime)
        
    return max(files, key=sort_key)

def pre_clean_stale_files(fixed_path):
    """
    [Pre-Clean] 暴力清除所有的残留 .blend 变体文件 (.blend1, .blend@ 等)，防止覆盖失败。
    """
    stale_files = glob.glob(fixed_path + "*") # Matches .blend, .blend1, .blend@
    for stale in stale_files:
        try:
            # Force remove read-only attribute first (Windows)
            os.chmod(stale, stat.S_IWRITE)
            os.remove(stale)
            print("[Pre-Clean] Removed stale: " + os.path.basename(stale))
        except Exception as e:
            print("[Pre-Clean] WARNING: Could not remove {}: {}".format(stale, e))

def post_clean_atomic_save(fixed_path):
    """
    [Post-Clean/Finalize] 处理网络盘上 Blender 原子保存失败产生的残留 @ 文件。
    如果 .blend@ 存在但 .blend 不存在，则自动更名转正。
    如果都存在，则删除无用的 @ 临时文件。
    """
    blend_at = fixed_path + "@"
    if os.path.exists(blend_at):
        if not os.path.exists(fixed_path):
            try:
                os.rename(blend_at, fixed_path)
                print("[Post-Clean] Successfully finalized atomic save: " + os.path.basename(fixed_path))
            except Exception as e:
                print("[Post-Clean] ERROR: Final rename failed: " + str(e))
        else:
            # Both exist? The @ one is a redundant leftover.
            try:
                os.remove(blend_at)
                print("[Post-Clean] Removed redundant atomic temp file: " + os.path.basename(blend_at))
            except: 
                pass
