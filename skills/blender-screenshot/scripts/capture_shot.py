import bpy
import sys
import os

def prepare_outliner():
    try:
        # Check if an outliner exists
        has_outliner = False
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'OUTLINER':
                    has_outliner = True
                    break
        
        # TRAP DEFENSE: If the user saved the file without an outliner, force one to exist
        if not has_outliner:
            max_area = None
            max_size = 0
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    size = area.width * area.height
                    if size > max_size:
                        max_size = size
                        max_area = area
            if max_area:
                max_area.type = 'OUTLINER'
        
        target_area = None
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'OUTLINER':
                    if not target_area:
                        target_area = area
                    # Force View Layer mode
                    area.spaces.active.display_mode = 'VIEW_LAYER'
        
        if not target_area:
            print("Could not find OUTLINER area.")
            bpy.ops.wm.quit_blender()
            return
            
        # Give Blender time to process the UI change before screenshotting
        bpy.app.timers.register(lambda: capture_outliner(target_area), first_interval=0.8)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error during preparation: {str(e)}")
        bpy.ops.wm.quit_blender()

def capture_outliner(target_area):
    try:
        out_dir = os.environ.get("BLENDER_SHOT_OUT", ".")
        asset_name = os.environ.get("BLENDER_ASSET_NAME", "asset")
        final_img = os.path.join(out_dir, f"{asset_name}_outliner.png")
        
        # 全局扫描并清理历史遗留的临时截图文件
        import glob
        for old_temp in glob.glob(os.path.join(out_dir, "temp_outliner_*.png")):
            try:
                os.remove(old_temp)
                print(f"Cleaned up legacy temp file: {old_temp}")
            except:
                pass

        try:
            with bpy.context.temp_override(window=bpy.context.window_manager.windows[0], area=target_area):
                bpy.ops.outliner.show_hierarchy()
        except:
            pass
            
        with bpy.context.temp_override(window=bpy.context.window_manager.windows[0], area=target_area):
            bpy.ops.screen.screen_full_area()
        
        import time
        timestamp = str(int(time.time()))
        temp_img = os.path.join(out_dir, f"temp_outliner_{timestamp}.png")
        bpy.ops.screen.screenshot(filepath=temp_img)
        
        img = bpy.data.images.load(temp_img)
        width = img.size[0]
        height = img.size[1]
        
        target_width = 500
        if target_width > width: target_width = width
        
        orig_pixels = list(img.pixels)
        
        def is_row_empty(y_idx, check_width):
            start = y_idx * width * 4
            for x in range(50, check_width - 50): 
                idx = start + x * 4
                r = orig_pixels[idx]
                g = orig_pixels[idx+1]
                b = orig_pixels[idx+2]
                
                if r > 0.35 or g > 0.35 or b > 0.35:
                    if r > 0.5 or (max(r,g,b) - min(r,g,b) > 0.05):
                        return False
            return True
            
        content_bottom_y = 0
        
        for y in range(60, height):
            if not is_row_empty(y, target_width):
                content_bottom_y = y
                break
                
        top_crop = 50
        content_top_y = height - top_crop
        
        padding = 10
        content_bottom_y = max(0, content_bottom_y - padding)
        
        target_height = content_top_y - content_bottom_y
        if target_height <= 0: target_height = height
            
        cropped_img = bpy.data.images.new("Cropped", width=target_width, height=target_height, alpha=True)
        new_pixels = [0.0] * (target_width * target_height * 4)
        
        for new_y in range(target_height):
            orig_y = content_bottom_y + new_y
            orig_start = orig_y * width * 4
            orig_end = orig_start + (target_width * 4)
            
            new_start = new_y * target_width * 4
            new_end = new_start + (target_width * 4)
            
            new_pixels[new_start:new_end] = orig_pixels[orig_start:orig_end]
            
        cropped_img.pixels = new_pixels
        
        cropped_img.filepath_raw = final_img
        cropped_img.file_format = 'PNG'
        cropped_img.save()
        
        os.remove(temp_img)
        print(f"Saved Dynamic Height Outliner Screenshot: {final_img}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error during capture: {str(e)}")
    finally:
        bpy.ops.wm.quit_blender()

bpy.app.timers.register(prepare_outliner, first_interval=0.5)
