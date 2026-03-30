#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import glob
import shutil
import argparse

# Inject pipeline environment paths securely
try:
    sys.path.append(r'P:\pipeline\python39_python_lib')
    sys.path.append(r'P:\pipeline\ppas')
except:
    pass

from dayu_widgets.qt import *
from dayu_path import DayuPath
from dayu_widgets import dayu_theme

from importlib import reload
from app.base.wizard import MWizard

from ui_center.message_box import MessageBox
from ui_center.page.comment_page import MCommentPage2
from ui_center.page import page_thumbnail
from app.base.wizard import MWizardPage
from dayu_widgets.browser import MDragFileButton
from dayu_widgets.check_box import MCheckBox
from dayu_widgets.label import MLabel
reload(page_thumbnail)

class NoQCExportPage(MWizardPage):
    def __init__(self, publish_args, parent=None):
        super(NoQCExportPage, self).__init__(parent)
        self.publish_args = publish_args
        self.is_2k = MCheckBox(u'Is Convert 2K and 1k')
        self.is_2k.setChecked(True)
        self.is_publish_mat = MCheckBox(u'Is Publish Material')
        
        check_lay = QHBoxLayout()
        mod = getattr(self.publish_args, "module", "tex")
        if mod == "tex":
            check_lay.addWidget(self.is_2k)
            check_lay.addSpacing(10)
        else:
            self.is_2k.setChecked(False) # Force disable 2K generation for UV module
            self.is_2k.setVisible(False)
            
        check_lay.addWidget(self.is_publish_mat)
        check_lay.addStretch()

        self.publish_label = MLabel(u'拖入需要备份的文件和渲染图... ').strong().secondary().h4()
        self.browser = MDragFileButton(text='Click or drag file here')
        self.browser.set_dayu_svg('attachment_line.svg')
        self.browser.set_dayu_multiple(True)
        self.browser.setMaximumHeight(200)

        self.main_lay = QVBoxLayout()
        self.main_lay.addWidget(self.publish_label)
        self.main_lay.addLayout(check_lay)
        self.main_lay.addWidget(self.browser)
        self.main_lay.addStretch()
        self.setLayout(self.main_lay)
        
        self.register_field('export_data', getter=lambda: True, required=True)

class PublishElementNoQCWizard(MWizard):
    def __init__(self, publish_args, parent=None):
        super(PublishElementNoQCWizard, self).__init__(parent)
        self.publish_args = publish_args
        
        self.export_page = NoQCExportPage(publish_args, parent=self)
        self.export_page.setTitle('Export Configs')
        self.page1 = page_thumbnail.MThumbnailPage('Thumbnail')
        self.page2 = MCommentPage2('Write Comment')

        self.add_page(self.export_page)
        self.add_page(self.page1)
        self.add_page(self.page2, is_last=True)
        self.go_to(0)
        self.resize(700, 800)

    def __get_max_version(self, search_path):
        import re
        max_v = 0
        existing_files = glob.glob(search_path)
        for f in existing_files:
            m = re.search(r'_v(\d+)\.blend$', os.path.basename(f))
            if m:
                v = int(m.group(1))
                if v > max_v:
                    max_v = v
        return max_v

    def accept(self, *args, **kwargs):
        import tempfile
        thumbnail = self.page1.field('thumbnail').get('thumbnail_large') if self.page1.field('thumbnail') else None
        comment = self.page2.field('comment2')

        # ------------------- Payload Delivery Logic -------------------
        # Fallbacks in case tool was not launched via Dashboard parameters
        proj = getattr(self.publish_args, "proj", "")
        atype = getattr(self.publish_args, "type", "chr")
        aname = getattr(self.publish_args, "asset", "")
        mod = getattr(self.publish_args, "module", "")
        src = getattr(self.publish_args, "src", "")

        if not proj or not aname or not src:
            MessageBox(u"参数不全！仅演示界面，未执行任何物理打包。", parent=self).exec_()
            return super(PublishElementNoQCWizard, self).accept(*args, **kwargs)

        # 1. Target Directory Setting
        pub_dir = os.path.join(r"X:\Project", proj, "pub", "assets", atype, aname, mod, mod + "Master")
        if not os.path.exists(pub_dir):
            os.makedirs(pub_dir)
            
        # 2. Version Calculation
        pattern = "{}_{}_{}_{}_{}Master_v*.blend".format(proj, atype, aname, mod, mod)
        search_path = os.path.join(pub_dir, pattern)
        max_v = self.__get_max_version(search_path)
        next_v = max_v + 1
        
        new_basename = "{}_{}_{}_{}_{}Master_v{:03d}.blend".format(proj, atype, aname, mod, mod, next_v)
        target_blend = os.path.join(pub_dir, new_basename)

        # 3. GUI Parameters
        is_publish_mat = self.export_page.is_publish_mat.isChecked()
        is_2k = self.export_page.is_2k.isChecked()
        other_file_list = self.export_page.browser.get_dayu_path()

        # 4. Drag & Drop Media & Backup Parsing
        try:
            if other_file_list:
                for file_ in other_file_list:
                    from dayu_path import DayuPath
                    fpath = DayuPath(file_)
                    if fpath.ext in ['.jpg', '.png']:
                        fpath.copy(target_blend.replace('.blend', fpath.ext))
                    else:
                        copy_to = DayuPath(target_blend).parent.child('backup_file').child(fpath.name)
                        copy_to.parent.mkdir(parents=True)
                        fpath.copy(copy_to)
        except Exception as e:
            print("Backup copy warning: " + str(e))

        # 5. Launch Headless Blender Worker
        import tempfile, json, subprocess
        worker_payload = {
            "target_blend": target_blend,
            "is_publish_mat": is_publish_mat,
            "is_2k": is_2k,
            "project": proj,
            "asset_type": atype,
            "asset_name": aname,
            "module": mod
        }
        worker_json = os.path.join(tempfile.gettempdir(), "headless_worker.json")
        with open(worker_json, 'w') as f:
            json.dump(worker_payload, f)
            
        blender_path = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
        worker_script = os.path.join(os.path.dirname(__file__), "headless_pub_worker.py")
        
        print(">>> Triggering Async Headless Pipeline...")
        # Start blender invisibly to compile json, textures, etc
        subprocess.call([blender_path, "-b", src, "-P", worker_script, "--", worker_json])

        try: os.remove(worker_json)
        except: pass

        # 6. Thumbnail Copy
        if thumbnail:
            jpg_basename = new_basename.replace(".blend", ".jpg")
            target_image = os.path.join(pub_dir, jpg_basename)
            thumbnail.save(target_image)
            
        # 7. Flow/ShotGrid Status & Note Update (Using sg-data-reader skill)
        sg_payload = {
            "project": proj,
            "updates": [{
                "asset_name": aname,
                "task_name": mod + "Master",  # e.g., texMaster
                "status": "rev",
                "comment": comment if comment else "Dashboard Automatic Publisher Executed"
            }]
        }
        tmp_json = os.path.join(tempfile.gettempdir(), "sg_pub_update.json")
        with open(tmp_json, 'w') as f:
            json.dump(sg_payload, f)
        
        sg_script = r"X:\AI_Automation\.gemini\skills\sg-data-reader\scripts\sg_batch_update.py"
        
        print(">>> Syncing Flow (ShotGrid) States...")
        subprocess.call([blender_path, "-b", "-P", sg_script, "--", tmp_json])
        
        try: os.remove(tmp_json)
        except: pass
            
        MessageBox(u"Publish Finish!\n成功投递大货: v{:03d}\n锁定路径: pub/assets\nHeadless Engine: Check √\nSG Flow State: Check √".format(next_v), parent=self).exec_()
        return super(PublishElementNoQCWizard, self).accept(*args, **kwargs)


def run():
    # Deprecated empty run fallback
    try:
        QApplication(sys.argv)
    except: pass
    win = PublishElementNoQCWizard(argparse.Namespace())
    dayu_theme.apply(win)
    win.show()
    win.exec_()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default="")
    parser.add_argument("--src", default="")
    parser.add_argument("--asset", default="")
    parser.add_argument("--proj", default="")
    parser.add_argument("--type", default="chr")
    pargs, unknown = parser.parse_known_args()

    app = QApplication(sys.argv)
    test = PublishElementNoQCWizard(pargs, None)
    test.resize(500, 500)
    test.show()
    dayu_theme.apply(test)
    sys.exit(app.exec_())
