#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import json
import zipfile
import tempfile
import xml.etree.ElementTree as ET

def extract_docx(file_path):
    if not os.path.exists(file_path):
        return {"status": "error", "message": "File not found: {}".format(file_path)}
    
    if not zipfile.is_zipfile(file_path):
        return {"status": "error", "message": "Not a valid .docx file."}

    result = {
        "status": "success",
        "text_content": "",
        "extracted_images": [],
        "temp_dir": ""
    }

    try:
        temp_dir = tempfile.mkdtemp(prefix="gemini_docx_img_")
        result["temp_dir"] = temp_dir

        with zipfile.ZipFile(file_path, 'r') as docx_zip:
            if 'word/document.xml' in docx_zip.namelist():
                xml_content = docx_zip.read('word/document.xml')
                tree = ET.fromstring(xml_content)
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                
                paragraphs = []
                for p in tree.findall('.//w:p', ns):
                    texts = [node.text for node in p.findall('.//w:t', ns) if node.text is not None]
                    if texts:
                        # In Python 2, elements can be unicode or str.
                        # Convert to unicode to avoid encode errors on joining
                        if sys.version_info[0] < 3:
                            texts = [t if isinstance(t, unicode) else t.decode('utf-8') for t in texts]
                        paragraphs.append(u''.join(texts))
                
                result["text_content"] = u'\n'.join(paragraphs)

            for item in docx_zip.namelist():
                if item.startswith('word/media/') and item != 'word/media/':
                    image_data = docx_zip.read(item)
                    file_name = os.path.basename(item)
                    save_path = os.path.join(temp_dir, file_name)
                    
                    with open(save_path, 'wb') as img_file:
                        img_file.write(image_data)
                    
                    result["extracted_images"].append(save_path)

        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Please provide a .docx file path."}))
        sys.exit(1)
    
    # In Python 2 on Windows, sys.argv[1] might be an encoded string
    target_file = sys.argv[1]
    if sys.version_info[0] < 3 and isinstance(target_file, str):
        target_file = target_file.decode(sys.getfilesystemencoding())

    output_data = extract_docx(target_file)
    print(json.dumps(output_data, ensure_ascii=True, indent=2))
