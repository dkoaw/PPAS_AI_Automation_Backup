import bpy
import os
import subprocess
import time
import shutil

class PPAS_OT_CloudBackupSync(bpy.types.Operator):
    """一键同步管线逻辑与记忆至 GitHub"""
    bl_idname = "ppas.cloud_backup_sync"
    bl_label = "☁️ 备份至 GitHub"
    bl_options = {'REGISTER'}

    repo_url = "git@github.com:dkoaw/PPAS_AI_Automation_Backup.git"
    staging_dir = r"X:\AI_Automation\Github_Backup_Staging"
    
    def execute(self, context):
        print("--- 启动云端备份同步程序 ---")
        
        # 1. 准备暂存区
        if not os.path.exists(self.staging_dir):
            os.makedirs(self.staging_dir)
            subprocess.run(["git", "init"], cwd=self.staging_dir)
            subprocess.run(["git", "remote", "add", "origin", self.repo_url], cwd=self.staging_dir)

        # 2. 物理搬运资产
        # A. 技能包
        src_skills = r"X:\AI_Automation\.gemini\skills"
        dst_skills = os.path.join(self.staging_dir, "skills")
        if os.path.exists(dst_skills): shutil.rmtree(dst_skills)
        shutil.copytree(src_skills, dst_skills, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        
        # B. 加载器工具
        src_tools = r"X:\AI_Automation\Pipeline_Tools"
        dst_tools = os.path.join(self.staging_dir, "Pipeline_Tools")
        if os.path.exists(dst_tools): shutil.rmtree(dst_tools)
        shutil.copytree(src_tools, dst_tools)

        # C. 记忆与文档快照 (暂存区)
        memo_path = os.path.join(self.staging_dir, "memory_snapshot.md")
        with open(memo_path, "w", encoding="utf-8") as f:
            f.write("# 🧠 PPAS AI 记忆快照\n")
            f.write(f"备份时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## 核心原则记录\n")
            f.write("- UI开发准则: Append-Only (只增不删)\n")
            f.write("- 软件标准: Maya 2025 (USD Export), Blender 5.0.1 (LGT/Comp)\n")
            f.write("- 项目基准: 以 v15.9 架构为核心地基\n")

        # 3. Git 推送
        try:
            # 检查是否有变更
            subprocess.run(["git", "add", "."], cwd=self.staging_dir)
            commit_msg = f"Automatic Backup: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=self.staging_dir)
            
            # 推送 (强制使用 main 分支)
            result = subprocess.run(["git", "push", "-u", "origin", "master"], cwd=self.staging_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.report({'INFO'}, "云端备份成功！所有逻辑已同步至 GitHub。")
            else:
                # 兼容不同分支名
                subprocess.run(["git", "push", "-u", "origin", "main"], cwd=self.staging_dir)
                self.report({'INFO'}, "备份完成。")
                
        except Exception as e:
            self.report({'ERROR'}, f"同步失败: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}

classes = (PPAS_OT_CloudBackupSync,)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
