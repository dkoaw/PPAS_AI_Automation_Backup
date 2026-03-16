# -*- coding: utf-8 -*-
import json
import codecs
import os
import sys

def compare_json_data(file_a, file_b):
    """
    对比两个资产结构 JSON 文件
    file_a: 环节 A 的 JSON 路径
    file_b: 环节 B 的 JSON 路径
    """
    try:
        with codecs.open(file_a, 'r', 'utf-8') as f:
            data_a = json.load(f)
        with codecs.open(file_b, 'r', 'utf-8') as f:
            data_b = json.load(f)
    except Exception as e:
        return "Error reading JSON files: {}".format(str(e))

    keys_a = set(data_a.keys())
    keys_b = set(data_b.keys())

    only_in_a = keys_a - keys_b
    only_in_b = keys_b - keys_a
    common_keys = keys_a & keys_b

    report = []
    report.append(u"=== 资产核心模型数据对比报告 ===")
    report.append(u"文件 A: {}".format(os.path.basename(file_a)))
    report.append(u"文件 B: {}".format(os.path.basename(file_b)))
    report.append(u"-" * 40)

    # 1. 检查层级结构差异 (DAG Path)
    if only_in_a or only_in_b:
        report.append(u"🚨 [层级结构不一致]")
        if only_in_a:
            report.append(u"  - 仅在 A 中存在的路径 ({} 个):".format(len(only_in_a)))
            for k in sorted(list(only_in_a))[:10]: report.append(u"    * {}".format(k))
            if len(only_in_a) > 10: report.append(u"    * ... (略)")
        if only_in_b:
            report.append(u"  - 仅在 B 中存在的路径 ({} 个):".format(len(only_in_b)))
            for k in sorted(list(only_in_b))[:10]: report.append(u"    * {}".format(k))
            if len(only_in_b) > 10: report.append(u"    * ... (略)")
    else:
        report.append(u"✅ 层级路径完全一致 ({} 个模型)".format(len(common_keys)))

    # 2. 检查拓扑与几何差异
    vert_count_mismatches = []
    pos_mismatches = []

    for key in sorted(list(common_keys)):
        # 顶点数对比
        if data_a[key]['vertices'] != data_b[key]['vertices']:
            vert_count_mismatches.append(u"  * {}: A({}) vs B({})".format(key, data_a[key]['vertices'], data_b[key]['vertices']))
            continue
            
        # 顶点坐标对比 (点序检查)
        pos_a = data_a[key]['vert_positions']
        pos_b = data_b[key]['vert_positions']
        
        is_pos_match = True
        if len(pos_a) != len(pos_b):
            is_pos_match = False
        else:
            for i in range(len(pos_a)):
                # 放宽容差至 0.005，吸收跨 DCC 软件浮点精度带来的微小误差
                if abs(pos_a[i] - pos_b[i]) > 0.005:
                    is_pos_match = False
                    break
        
        if not is_pos_match:
            pos_mismatches.append(key)

    if vert_count_mismatches:
        report.append(u"🚨 [顶点总数不匹配] ({} 个模型):".format(len(vert_count_mismatches)))
        for m in vert_count_mismatches[:10]: report.append(m)
        if len(vert_count_mismatches) > 10: report.append(u"    * ... (略)")
    else:
        if common_keys:
            report.append(u"✅ 所有匹配模型的顶点总数一致")

    if pos_mismatches:
        report.append(u"🚨 [几何形变/点序不一致] ({} 个模型坐标发生漂移):".format(len(pos_mismatches)))
        for m in pos_mismatches[:10]: report.append(u"    * {}".format(m))
        if len(pos_mismatches) > 10: report.append(u"    * ... (略)")
    else:
        if common_keys and not vert_count_mismatches:
            report.append(u"✅ 所有匹配模型的几何指纹完全一致")

    if not only_in_a and not only_in_b and not vert_count_mismatches and not pos_mismatches:
        report.append(u"\n🏆 结论：两个环节资产核心数据完！全！一！致！")
    else:
        report.append(u"\n❌ 结论：资产核心数据存在差异，请根据上方详情进行同步或排查。")

    return u"\n".join(report)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python compare_asset_data.py <json_a> <json_b> [output_md]")
        sys.exit(1)
        
    path_a = sys.argv[1]
    path_b = sys.argv[2]
    
    result = compare_json_data(path_a, path_b)
    
    if len(sys.argv) > 3:
        with codecs.open(sys.argv[3], 'w', 'utf-8') as f:
            f.write(result)
        print("Comparison report saved to: {}".format(sys.argv[3]))
    else:
        print(result.encode('utf-8'))
