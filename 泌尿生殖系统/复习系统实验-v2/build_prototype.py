from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent / "Notes"
DB = HERE / "study-prototype.sqlite"
SCHEMA = HERE / "schema.sql"

NOTE_FILES = [
    "1-肾炎肾癌与宫颈病变.md",
    "2-子宫卵巢与乳腺肿瘤.md",
    "3-急性肾损伤机制与表现.md",
    "4-慢性肾衰机制与表现.md",
    "5-利尿药与子宫兴奋药.md",
]

H_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.、)]\s+|[①②③④⑤⑥⑦⑧⑨⑩]\s*)")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


TREE = [
    ("uro", None, "泌尿生殖系统", "syllabus", None),
    ("path", "uro", "病理", "syllabus", None),
    ("path.renal", "path", "泌尿系统病理", "syllabus", None),
    ("path.renal.glom", "path.renal", "肾小球疾病", "syllabus", "掌握"),
    ("path.renal.glom.rpgn", "path.renal.glom", "新月体性/快速进行性肾小球肾炎", "knowledge_outline", "掌握"),
    ("path.renal.glom.goodpasture", "path.renal.glom.rpgn", "Goodpasture syndrome", "knowledge_outline", None),
    ("path.renal.glom.iga", "path.renal.glom", "IgA肾病", "knowledge_outline", None),
    ("path.renal.glom.chronic", "path.renal.glom", "慢性肾小球肾炎", "knowledge_outline", None),
    ("path.renal.pyelo", "path.renal", "肾盂肾炎", "syllabus", "掌握"),
    ("path.renal.pyelo.acute", "path.renal.pyelo", "急性肾盂肾炎", "knowledge_outline", None),
    ("path.renal.pyelo.chronic", "path.renal.pyelo", "慢性肾盂肾炎", "knowledge_outline", None),
    ("path.renal.tumor", "path.renal", "泌尿系统肿瘤", "syllabus", "熟悉"),
    ("path.renal.tumor.rcc", "path.renal.tumor", "肾细胞癌", "knowledge_outline", "熟悉"),
    ("path.renal.tumor.wilms", "path.renal.tumor", "Wilms瘤", "knowledge_outline", "了解"),
    ("path.renal.tumor.urothelial", "path.renal.tumor", "尿路上皮癌", "knowledge_outline", "了解"),

    ("path.repro", "path", "生殖系统与乳腺病理", "syllabus", None),
    ("path.repro.cervix", "path.repro", "宫颈", "syllabus", "掌握"),
    ("path.repro.cervix.cin", "path.repro.cervix", "CIN", "knowledge_outline", "掌握"),
    ("path.repro.cervix.cancer", "path.repro.cervix", "宫颈癌", "knowledge_outline", "掌握"),
    ("path.repro.uterus", "path.repro", "子宫体疾病", "syllabus", None),
    ("path.repro.uterus.endometriosis", "path.repro.uterus", "子宫内膜异位症/腺肌病", "knowledge_outline", None),
    ("path.repro.uterus.hyperplasia", "path.repro.uterus", "子宫内膜增生", "knowledge_outline", None),
    ("path.repro.uterus.cancer", "path.repro.uterus", "子宫内膜癌", "knowledge_outline", "了解"),
    ("path.repro.uterus.leiomyoma", "path.repro.uterus", "子宫平滑肌瘤", "knowledge_outline", "了解"),
    ("path.repro.gtd", "path.repro", "滋养层细胞疾病", "syllabus", "熟悉"),
    ("path.repro.gtd.mole", "path.repro.gtd", "葡萄胎", "knowledge_outline", None),
    ("path.repro.gtd.invasive", "path.repro.gtd", "侵袭性葡萄胎", "knowledge_outline", None),
    ("path.repro.gtd.chorio", "path.repro.gtd", "绒毛膜癌", "knowledge_outline", None),
    ("path.repro.ovary", "path.repro", "卵巢肿瘤", "knowledge_outline", "了解"),
    ("path.repro.prostate", "path.repro", "前列腺疾病", "knowledge_outline", "熟悉"),
    ("path.repro.breast", "path.repro", "乳腺", "syllabus", "掌握"),
    ("path.repro.breast.cancer", "path.repro.breast", "乳腺癌", "knowledge_outline", "掌握"),

    ("renal_function", "uro", "肾功能不全", "syllabus", None),
    ("renal_function.foundation", "renal_function", "肾功能基础", "note_ai", None),
    ("aki", "renal_function", "急性肾损伤 AKI", "syllabus", "掌握"),
    ("aki.concept", "aki", "概念与核心特征", "knowledge_outline", "掌握"),
    ("aki.concept.features", "aki.concept", "主要特点", "note_ai", None),
    ("aki.concept.naming", "aki.concept", "ARF与AKI命名", "note_ai", None),
    ("aki.etiology", "aki", "病因分类", "knowledge_outline", "掌握"),
    ("aki.etiology.prerenal", "aki.etiology", "肾前性", "knowledge_outline", None),
    ("aki.etiology.intrinsic", "aki.etiology", "肾性", "knowledge_outline", None),
    ("aki.etiology.intrinsic.atn", "aki.etiology.intrinsic", "急性肾小管坏死的原因", "note_ai", None),
    ("aki.etiology.postrenal", "aki.etiology", "肾后性", "knowledge_outline", None),
    ("aki.mechanism", "aki", "发病机制", "knowledge_outline", "掌握"),
    ("aki.mechanism.hemo", "aki.mechanism", "肾血管及血流动力学异常", "knowledge_outline", None),
    ("aki.mechanism.hemo.perfusion", "aki.mechanism.hemo", "肾灌注压与自身调节", "note_ai", None),
    ("aki.mechanism.hemo.vasoconstriction", "aki.mechanism.hemo", "肾血管收缩", "note_ai", None),
    ("aki.mechanism.hemo.endothelial", "aki.mechanism.hemo", "肾小球毛细血管内皮细胞肿胀", "note_ai", None),
    ("aki.mechanism.hemo.coagulation", "aki.mechanism.hemo", "肾血管内凝血", "note_ai", None),
    ("aki.mechanism.tubular", "aki.mechanism", "肾小管损伤", "knowledge_outline", None),
    ("aki.mechanism.tubular.cellinjury", "aki.mechanism.tubular", "肾小管上皮细胞损伤机制", "note_ai", None),
    ("aki.mechanism.obstruction", "aki.mechanism.tubular", "肾小管阻塞", "note_ai", None),
    ("aki.mechanism.backleak", "aki.mechanism.tubular", "原尿反漏", "note_ai", None),
    ("aki.mechanism.tgf", "aki.mechanism.tubular", "管球反馈异常", "note_ai", None),
    ("aki.mechanism.kf", "aki.mechanism", "肾小球滤过系数降低", "knowledge_outline", None),
    ("aki.clinical", "aki", "临床表现", "note_ai", None),
    ("aki.clinical.stages", "aki.clinical", "少尿型AKI分期", "note_ai", None),
    ("aki.oliguric", "aki.clinical", "少尿期", "knowledge_outline", "掌握"),
    ("aki.oliguric.urine", "aki.oliguric", "尿量变化", "note_ai", None),
    ("aki.oliguric.hematuria", "aki.oliguric", "血尿与血尿来源", "note_ai", None),
    ("aki.oliguric.proteinuria", "aki.oliguric", "蛋白尿", "note_ai", None),
    ("aki.oliguric.casts", "aki.oliguric", "管型尿", "note_ai", None),
    ("aki.oliguric.urine_indices", "aki.oliguric", "尿比重与尿钠", "note_ai", None),
    ("aki.oliguric.differential", "aki.oliguric", "肾前性与器质性鉴别", "note_ai", None),
    ("aki.oliguric.fena", "aki.oliguric", "FENa与功能性/器质性鉴别", "note_ai", None),
    ("aki.oliguric.water", "aki.oliguric", "水潴留", "note_ai", None),
    ("aki.oliguric.azotemia", "aki.oliguric", "氮质血症", "note_ai", None),
    ("aki.oliguric.hyperk", "aki.oliguric", "高钾血症及机制", "note_ai", None),
    ("aki.oliguric.acidosis", "aki.oliguric", "代谢性酸中毒及机制", "note_ai", None),
    ("aki.oliguric.summary", "aki.oliguric", "少尿期临床表现总结", "note_ai", None),
    ("aki.diuretic", "aki.clinical", "多尿期", "knowledge_outline", "掌握"),
    ("aki.diuretic.mechanism", "aki.diuretic", "多尿的机制", "note_ai", None),
    ("aki.diuretic.risk", "aki.diuretic", "多尿期风险", "note_ai", None),
    ("aki.recovery", "aki.clinical", "恢复期", "knowledge_outline", "掌握"),
    ("aki.nonoliguric", "aki.clinical", "非少尿型AKI", "note_ai", None),

    ("crf", "renal_function", "慢性肾功能不全", "syllabus", "掌握"),
    ("crf.mechanism", "crf", "发病机制", "knowledge_outline", "掌握"),
    ("crf.manifest", "crf", "功能与代谢变化", "knowledge_outline", "掌握"),
    ("uremia", "renal_function", "尿毒症", "knowledge_outline", None),

    ("pharm", "uro", "药理", "syllabus", None),
    ("pharm.diuretic", "pharm", "利尿药", "syllabus", "掌握"),
    ("pharm.diuretic.class", "pharm.diuretic", "分类/部位/靶点/排钾保钾", "knowledge_outline", "掌握"),
    ("pharm.diuretic.loop", "pharm.diuretic", "袢利尿药/呋塞米", "knowledge_outline", "掌握"),
    ("pharm.diuretic.thiazide", "pharm.diuretic", "噻嗪类/氢氯噻嗪", "knowledge_outline", "掌握"),
    ("pharm.diuretic.ksparing", "pharm.diuretic", "保钾利尿药", "knowledge_outline", "掌握"),
    ("pharm.diuretic.ca", "pharm.diuretic", "碳酸酐酶抑制剂", "knowledge_outline", "了解"),
    ("pharm.diuretic.osmotic", "pharm.diuretic", "渗透性利尿药/甘露醇", "knowledge_outline", "了解"),
    ("pharm.uterotonic", "pharm", "子宫平滑肌兴奋药", "knowledge_outline", "了解"),
    ("pharm.uterotonic.oxytocin", "pharm.uterotonic", "缩宫素", "knowledge_outline", None),
]

RELATIONS = [
    ("renal_function.foundation", "aki.mechanism", "prerequisite", 1.0, "理解GFR、滤过屏障和肾小管后再看AKI机制更顺"),
    ("aki.concept", "aki.etiology", "prerequisite", 0.8, "先建立AKI概念框架"),
    ("aki.etiology", "aki.mechanism", "prerequisite", 0.6, "病因是机制的上下文，但不是要求背完所有病因细节"),
    ("aki.oliguric", "aki.diuretic", "sequence", 1.0, "少尿型AKI病程自然顺序"),
    ("aki.diuretic", "aki.recovery", "sequence", 1.0, "少尿型AKI病程自然顺序"),
    ("pharm.diuretic.class", "pharm.diuretic.loop", "prerequisite", 0.7, "先有分类框架"),
    ("pharm.diuretic.class", "pharm.diuretic.thiazide", "prerequisite", 0.7, "先有分类框架"),
    ("pharm.diuretic.class", "pharm.diuretic.ksparing", "prerequisite", 0.7, "先有分类框架"),
]

AKI_MAP = [
    (r"急性肾功能衰竭概念导入|万能钥匙|急性肾衰的主要特点|ARF与AKI名称变化", "aki.concept"),
    (r"AKI的病因分类", "aki.etiology"),
    (r"肾前性AKI|功能性肾衰", "aki.etiology.prerenal"),
    (r"肾性AKI|急性肾小管坏死", "aki.etiology.intrinsic"),
    (r"肾后性AKI", "aki.etiology.postrenal"),
    (r"AKI发病机制总述|AKI发病机制总结", "aki.mechanism"),
    (r"肾血流动力学异常|肾灌注压|肾血管收缩|毛细血管内皮细胞肿胀|肾血管内凝血", "aki.mechanism.hemo"),
    (r"肾小管损伤机制导入|肾小管上皮细胞损伤机制", "aki.mechanism.tubular"),
    (r"肾小管阻塞|血红蛋白和肌红蛋白|药物结晶", "aki.mechanism.obstruction"),
    (r"原尿反漏", "aki.mechanism.backleak"),
    (r"管球反馈", "aki.mechanism.tgf"),
    (r"滤过系数下降", "aki.mechanism.kf"),
    (r"AKI临床表现|少尿型AKI的分期|少尿期临床表现", "aki.oliguric"),
    (r"少尿期：尿量变化|少尿期：尿液成分改变|血尿|蛋白尿|管型尿|尿比重和尿钠|红细胞形态", "aki.oliguric.urine"),
    (r"功能性肾衰与器质性肾衰的鉴别|FENa", "aki.oliguric.fena"),
    (r"少尿期：水潴留", "aki.oliguric.water"),
    (r"氮质血症", "aki.oliguric.azotemia"),
    (r"高钾血症", "aki.oliguric.hyperk"),
    (r"少尿期：代谢性酸中毒", "aki.oliguric.acidosis"),
    (r"多尿期为什么出现多尿|多尿期 diuretic phase|多尿期仍不能", "aki.diuretic.mechanism"),
    (r"恢复期 recovery phase", "aki.recovery"),
    (r"非少尿型AKI", "aki.nonoliguric"),
]

# AKI clean-room segmentation for the current experiment.  The ranges are
# inclusive and together cover L764-L2747 exactly once.  Non-knowledge class
# notices / attendance / research-method interludes are preserved as fragments
# with knowledge_node_id=NULL instead of being silently dropped.
AKI_PLAN = [
    (764, 780, "aki.concept", "knowledge"),
    (781, 782, None, "meta_session"),
    (783, 812, "aki.concept", "knowledge"),
    (813, 831, None, "meta_notice"),
    (832, 850, "aki.concept.features", "knowledge"),
    (851, 882, "aki.concept.naming", "knowledge"),
    (883, 898, "aki.etiology", "knowledge"),
    (899, 1021, "aki.etiology.prerenal", "knowledge"),
    (1022, 1042, "aki.etiology.prerenal", "knowledge"),
    (1043, 1061, "aki.etiology.intrinsic", "knowledge"),
    (1062, 1164, "aki.etiology.intrinsic.atn", "knowledge"),
    (1165, 1202, "aki.etiology.postrenal", "knowledge"),
    (1203, 1214, "aki.mechanism", "knowledge"),
    (1215, 1225, "aki.mechanism.hemo", "knowledge"),
    (1226, 1265, "aki.mechanism.hemo.perfusion", "knowledge"),
    (1266, 1343, "aki.mechanism.hemo.vasoconstriction", "knowledge"),
    (1344, 1407, "aki.mechanism.hemo.endothelial", "knowledge"),
    (1408, 1447, "aki.mechanism.hemo.coagulation", "knowledge"),
    (1448, 1484, None, "meta_extension"),
    (1485, 1510, "aki.mechanism.tubular", "knowledge"),
    (1511, 1529, None, "meta_notice"),
    (1530, 1578, "aki.mechanism.tubular.cellinjury", "knowledge"),
    (1579, 1598, "aki.mechanism.obstruction", "knowledge"),
    (1599, 1648, "aki.mechanism.obstruction", "knowledge"),
    (1649, 1665, None, "meta_notice"),
    (1666, 1683, "aki.mechanism.obstruction", "knowledge"),
    (1684, 1727, "aki.mechanism.obstruction", "knowledge"),
    (1728, 1750, "aki.mechanism.obstruction", "knowledge"),
    (1751, 1786, "aki.mechanism.backleak", "knowledge"),
    (1787, 1805, "aki.mechanism.backleak", "knowledge"),
    (1806, 1845, "aki.mechanism.backleak", "knowledge"),
    (1846, 1883, "aki.mechanism.backleak", "knowledge"),
    (1884, 1911, "aki.mechanism.tgf", "knowledge"),
    (1912, 1962, "aki.mechanism.kf", "knowledge"),
    (1963, 2008, "aki.mechanism", "knowledge"),
    (2009, 2025, "aki.clinical", "knowledge"),
    (2026, 2046, "aki.clinical.stages", "knowledge"),
    (2047, 2066, "aki.oliguric.urine", "knowledge"),
    (2067, 2092, "aki.oliguric.hematuria", "knowledge"),
    (2093, 2125, "aki.oliguric.hematuria", "knowledge"),
    (2126, 2133, "aki.oliguric.proteinuria", "knowledge"),
    (2134, 2167, "aki.oliguric.casts", "knowledge"),
    (2168, 2183, "aki.oliguric.urine_indices", "knowledge"),
    (2184, 2218, "aki.oliguric.differential", "knowledge"),
    (2219, 2276, "aki.oliguric.fena", "knowledge"),
    (2277, 2322, "aki.oliguric.water", "knowledge"),
    (2323, 2348, "aki.oliguric.azotemia", "knowledge"),
    (2349, 2421, "aki.oliguric.hyperk", "knowledge"),
    (2422, 2468, "aki.oliguric.acidosis", "knowledge"),
    (2469, 2487, "aki.oliguric.summary", "knowledge"),
    (2488, 2522, "aki.diuretic", "knowledge"),
    (2523, 2612, "aki.diuretic.mechanism", "knowledge"),
    (2613, 2653, "aki.diuretic.risk", "knowledge"),
    (2654, 2686, "aki.recovery", "knowledge"),
    (2687, 2747, "aki.nonoliguric", "knowledge"),
]


def heading_segments(text: str):
    lines = text.splitlines()
    headings = []
    stack = {}
    for i, line in enumerate(lines):
        m = H_RE.match(line)
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()
        for k in list(stack):
            if k >= level:
                del stack[k]
        stack[level] = title
        headings.append((i, level, title, " > ".join(stack[k] for k in sorted(stack))))
    result = []
    for ord_, (start, level, title, path) in enumerate(headings, 1):
        end = headings[ord_][0] - 1 if ord_ < len(headings) else len(lines) - 1
        seg = "\n".join(lines[start:end + 1]).rstrip() + "\n"
        result.append((ord_, start + 1, end + 1, level, title, path, seg))
    return result


def subtree_end(headings, idx, line_count):
    start, level, *_ = headings[idx]
    for j in range(idx + 1, len(headings)):
        if headings[j][1] <= level:
            return headings[j][0] - 1
    return line_count - 1


def node_paths(tree):
    by_id = {x[0]: x for x in tree}
    paths = {}

    def build(node_id):
        if node_id in paths:
            return paths[node_id]
        nid, parent, title, *_ = by_id[node_id]
        paths[node_id] = title if parent is None else build(parent) + " > " + title
        return paths[node_id]

    for node_id in by_id:
        build(node_id)
    return paths


def build():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA.read_text(encoding="utf-8-sig"))
    paths = node_paths(TREE)

    for nid, parent, title, origin, level in TREE:
        con.execute(
            "INSERT INTO knowledge_nodes(id,parent_id,title,canonical_path,origin,syllabus_level) VALUES(?,?,?,?,?,?)",
            (nid, parent, title, paths[nid], origin, level),
        )
    for row in RELATIONS:
        con.execute("INSERT INTO node_relations VALUES(?,?,?,?,?)", row)

    audit = []
    for fi, name in enumerate(NOTE_FILES, 1):
        p = NOTES / name
        raw = p.read_text(encoding="utf-8-sig")
        doc_id = f"note{fi}"
        con.execute(
            "INSERT INTO source_documents VALUES(?,?,?,?,?,?)",
            (doc_id, name, "classflow_note", str(p), sha(raw), raw),
        )
        segs = heading_segments(raw)
        for ord_, sline, eline, level, title, hpath, seg in segs:
            sid = f"{doc_id}.h{ord_:03d}"
            con.execute(
                "INSERT INTO candidate_segments VALUES(?,?,?,?,?,?,?,?,?,?)",
                (sid, doc_id, ord_, sline, eline, level, title, hpath, seg, sha(seg)),
            )
        list_items = sum(1 for line in raw.splitlines() if LIST_RE.match(line))
        audit.append((name, len(segs), list_items, len(segs) + list_items))

    doc_id = "note3"
    raw = con.execute("SELECT raw_text FROM source_documents WHERE id=?", (doc_id,)).fetchone()[0]
    lines = raw.splitlines()
    # The AKI demo is now an audited, exhaustive line plan.  Every line in the
    # AKI scope is owned exactly once, including meta/non-knowledge material.
    expected = 764
    for start, end, node_id, kind in AKI_PLAN:
        if start != expected:
            raise RuntimeError(f"AKI_PLAN gap/overlap before line {start}; expected {expected}")
        expected = end + 1
    if expected != 2748:
        raise RuntimeError(f"AKI_PLAN must end at 2747, got {expected-1}")

    for k, (start, end, node_id, kind) in enumerate(AKI_PLAN, 1):
        text = "\n".join(lines[start - 1:end]).rstrip() + "\n"
        fid = f"aki.clean.{k:03d}"
        is_knowledge = node_id is not None
        con.execute(
            "INSERT INTO fragments VALUES(?,?,?,?,?,?,?,?,?,?)",
            (fid, doc_id, node_id, start, end, text, sha(text),
             "manual_audit_v1", "confirmed" if is_knowledge else kind,
             "reviewed" if is_knowledge else "excluded"),
        )
        members = con.execute(
            "SELECT id FROM candidate_segments WHERE source_document_id=? AND start_line BETWEEN ? AND ? ORDER BY ordinal",
            (doc_id, start, end),
        ).fetchall()
        for mi, (sid,) in enumerate(members, 1):
            con.execute("INSERT INTO fragment_members VALUES(?,?,?)", (fid, sid, mi))

    demo_evidence = [
        ("aki", "syllabus", "肾功能不全章节", "direct", "掌握AKI病因、机制、三个时期功能代谢变化"),
        ("aki.mechanism", "knowledge_outline", "课程知识梳理p10", "direct", "列出三大发病机制"),
        ("aki.oliguric", "knowledge_outline", "课程知识梳理p10", "direct", "列出少尿期"),
        ("aki.diuretic", "knowledge_outline", "课程知识梳理p10", "direct", "列出多尿期"),
        ("aki.oliguric.hyperk", "classroom", "AKI课堂笔记", "direct", "三最之一/高钾危险"),
        ("aki.diuretic.mechanism", "classroom", "AKI课堂笔记", "direct", "老师明确提示可能考简答"),
        ("aki.oliguric.fena", "classroom", "AKI课堂笔记", "direct", "重点指标FENa"),
    ]
    for node, kind, locator, directness, signal in demo_evidence:
        con.execute(
            "INSERT INTO evidence(knowledge_node_id,source_kind,source_locator,directness,signal) VALUES(?,?,?,?,?)",
            (node, kind, locator, directness, signal),
        )

    con.execute(
        "INSERT INTO score_schemes VALUES(?,?,?)",
        ("unscored-v0", "未定权重占位方案",
         json.dumps({"status": "weights_not_final", "baseline": 50}, ensure_ascii=False)),
    )
    con.commit()
    write_docs(con, audit)
    con.close()


def write_docs(con, audit):
    total_heading = sum(x[1] for x in audit)
    total_list = sum(x[2] for x in audit)
    table_rows = "\n".join(f"| {n} | {h} | {li} | {alln} |" for n, h, li, alln in audit)

    (HERE / "00-模型与切分原则.md").write_text(
f"""# 复习编译器 v2：模型与切分原则

## 一句话模型

知识目录是一棵主树；原笔记被切成可追溯原文片段；一个知识坑位可以挂多个片段，但一个片段第一版只允许一个主坑位；额外的先修、因果、对比关系用树外边补丁。

## 目录从哪里来

1. 教学大纲提供必有的大目录，并保留掌握、熟悉、了解等正式要求。
2. 官方课程知识梳理继续细化大纲目录。
3. 课堂笔记只负责把原文片段映射进已有坑位；确实找不到时，才允许新建 note_ai 节点。
4. 后续再做同义坑位合并。

因此目录和正文是分开的：目录是课程知识模型，片段是原始学习材料。

## 为什么主树是合理简化

课程本身天然是“系统 → 章节 → 疾病/药物 → 子知识点”的层级结构。主树负责稳定导航和父子归属；树外只补少量 prerequisite、causal、contrast 等关系。严格说它不是纯树，而是“有主树骨架的有向图”。

## 一个坑位多个片段，一个片段一个坑位

同一知识点可能在正式授课、下一节课前复习、实验课串讲中多次出现。它们应该成为多个 fragment，但全部挂到同一个 knowledge node。重复出现本身可以成为后续评分证据。

第一版反过来不允许一个 fragment 同时进入多个坑位。遇到跨知识点原文，优先继续切分；实在不可分才留作异常审计，而不是默认多对多。

## 切分规则

Markdown 标题只负责产生“安全候选边界”，不直接等于知识原子。

AI 对局部标题树只做三种决策：

- KEEP：当前标题子树已经是一个完整复习问题，整块保留。
- DESCEND：当前块太粗，继续下钻到子标题。
- SPLIT_INLINE：没有子标题但正文混了多个独立知识点时，才允许在段落或列表组之间插 marker。

最终 marker 仍通过 apply-patch 写入原文副本，正文不重写。

## 原子性的定义

原子不是语法上最短，而是“能够独立回答一个复习问题，并且继续拆分会破坏这个问题完整性”的最小单元。

例如“高钾血症发生机制”下面的多条原因共同回答一个简答题，因此整体才是一个知识原子；不能因为每条原因都有编号就机械拆开。

## 评分暂时解耦

数据库已经预留 evidence、score_schemes、node_scores。以后可以随时换权重，不需要重新切片或重新建目录。
""", encoding="utf-8")

    (HERE / "01-切分审计.md").write_text(
f"""# 五篇笔记切分审计

## 机械切分结果

- 全部 Markdown 标题一刀切：**{total_heading} 个候选段**。
- 如果再把全部有序/无序列表项也当边界：额外 **{total_list} 个列表边界**，合计约 **{total_heading + total_list} 个机械段**。
- 这说明“拆到列表项”明显过碎；列表通常只是同一简答题下面的原因、步骤或表现。

| 笔记 | 标题候选段 | 列表项 | 若全部机械拆开 |
|---|---:|---:|---:|
{table_rows}

## v2 采用的两阶段切分

第一阶段：标题树机械解析，得到候选段，完全确定、可复现、可追溯。

第二阶段：AI只决定边界，不重写正文。它在局部标题树上做 KEEP / DESCEND / SPLIT_INLINE。

这样既保留 Markdown 的稳定结构，又避免不同老师、不同笔记的 H1/H2/H3 风格差异直接决定知识粒度。
""", encoding="utf-8")

    nodes = con.execute(
        """SELECT id, canonical_path, origin, COALESCE(syllabus_level,'')
           FROM knowledge_nodes
           WHERE id LIKE 'aki%' OR id='renal_function.foundation'
           ORDER BY canonical_path"""
    ).fetchall()
    frags = con.execute(
        """SELECT f.id, n.canonical_path, f.start_line, f.end_line,
                  substr(replace(f.text, char(10), ' '), 1, 150)
           FROM fragments f
           JOIN knowledge_nodes n ON n.id=f.knowledge_node_id
           WHERE f.source_document_id='note3'
           ORDER BY f.start_line"""
    ).fetchall()
    rels = con.execute(
        """SELECT a.title, b.title, r.relation_type, r.note
           FROM node_relations r
           JOIN knowledge_nodes a ON a.id=r.from_node_id
           JOIN knowledge_nodes b ON b.id=r.to_node_id
           WHERE a.id LIKE 'aki%' OR b.id LIKE 'aki%' OR a.id='renal_function.foundation'"""
    ).fetchall()

    node_lines = "\n".join(
        f"- {nid}｜{path}｜来源 {origin}｜大纲 {level or '—'}"
        for nid, path, origin, level in nodes
    )
    frag_lines = "\n".join(
        f"- {fid} → **{path}**｜L{start}-{end}｜{preview}…"
        for fid, path, start, end, preview in frags
    )
    rel_lines = "\n".join(
        f"- **{a}** → **{b}** [{kind}]：{note}"
        for a, b, kind, note in rels
    )

    (HERE / "02-AKI树与片段样例.md").write_text(
f"""# AKI：知识树、片段与依赖样例

这页只展示模型，不是重新生成一份复习笔记。

## AKI目录坑位

{node_lines}

## 当前 demo 原文片段

当前只把 AKI 这一课做成可查看样例。每个 fragment 都保留原始行号和原文，不做摘要。

{frag_lines}

## 树外依赖关系

{rel_lines}

## “同一个坑位多个片段”的意义

以后如果下一节课课前复习再次讲“高钾血症”，新片段仍归入同一个高钾节点，不创建第二个知识点。后续评分器可以把“被多节课重复提到”作为额外证据。

## 两种最终导出

- 纯分数榜：只回答考试价值谁高。
- 可学习顺序：以分数为主，但 prerequisite 未满足时先插入必要前置。

二者可以同时存在，不需要互相妥协。
""", encoding="utf-8")

    counts = {
        "source_documents": con.execute("SELECT count(*) FROM source_documents").fetchone()[0],
        "candidate_segments": con.execute("SELECT count(*) FROM candidate_segments").fetchone()[0],
        "knowledge_nodes": con.execute("SELECT count(*) FROM knowledge_nodes").fetchone()[0],
        "relations": con.execute("SELECT count(*) FROM node_relations").fetchone()[0],
        "fragments": con.execute("SELECT count(*) FROM fragments").fetchone()[0],
        "evidence": con.execute("SELECT count(*) FROM evidence").fetchone()[0],
    }
    (HERE / "03-数据库概览.md").write_text(
f"""# SQLite 数据库概览

数据库：study-prototype.sqlite

| 对象 | 当前数量 |
|---|---:|
| source_documents | {counts['source_documents']} |
| candidate_segments | {counts['candidate_segments']} |
| knowledge_nodes | {counts['knowledge_nodes']} |
| node_relations | {counts['relations']} |
| fragments（AKI demo） | {counts['fragments']} |
| evidence（示例） | {counts['evidence']} |

## 核心不变量

1. 原文存档并保存 SHA256。
2. 每个候选段有源文件、起止行、标题路径。
3. fragment 仍保存完整原文和行号。
4. fragment 第一版只有一个 knowledge_node_id。
5. knowledge node 可以拥有多个 fragment。
6. 评分与正文、切分解耦，换评分机制无需重新切片。

## 下一阶段

先把 797 个标题候选段全部跑一遍 KEEP / DESCEND / SPLIT_INLINE，得到全课程最终原子片段；再把每个片段映射到唯一知识坑位。权重在这两步稳定后再正式引入。
""", encoding="utf-8")

    # --- AKI audit: make the model inspectable for a human reviewer. ---
    direct_counts = dict(con.execute(
        "SELECT knowledge_node_id, count(*) FROM fragments WHERE knowledge_node_id IS NOT NULL GROUP BY knowledge_node_id"
    ).fetchall())
    children = {}
    title_by_id = {}
    for nid, parent, title, *_ in TREE:
        title_by_id[nid] = title
        children.setdefault(parent, []).append(nid)

    def subtree_count(nid):
        return direct_counts.get(nid, 0) + sum(subtree_count(c) for c in children.get(nid, []))

    tree_lines = []
    def emit_tree(nid, depth=0):
        if subtree_count(nid) == 0:
            return
        tree_lines.append(
            f"{'  ' * depth}- **{title_by_id[nid]}** — 直挂片段 {direct_counts.get(nid,0)}，子树合计 {subtree_count(nid)}"
        )
        for child in children.get(nid, []):
            if child.startswith("aki"):
                emit_tree(child, depth + 1)
    emit_tree("aki")

    meta_rows = con.execute(
        "SELECT id,start_line,end_line,review_status,text FROM fragments WHERE source_document_id='note3' AND knowledge_node_id IS NULL ORDER BY start_line"
    ).fetchall()
    meta_lines = []
    for fid, start, end, status, text in meta_rows:
        first = next((x.strip('# ').strip() for x in text.splitlines() if x.strip()), "")
        meta_lines.append(f"- L{start}–L{end}｜`{status}`｜{first}")

    rel_rows = con.execute(
        """SELECT a.title,b.title,r.relation_type,r.strength,r.note
           FROM node_relations r
           JOIN knowledge_nodes a ON a.id=r.from_node_id
           JOIN knowledge_nodes b ON b.id=r.to_node_id
           WHERE a.id LIKE 'aki%' OR b.id LIKE 'aki%' OR a.id='renal_function.foundation'
           ORDER BY r.relation_type,a.title,b.title"""
    ).fetchall()
    rel_lines2 = [f"- **{a}** → **{b}**｜`{kind}`｜{note}" for a,b,kind,strength,note in rel_rows]
    evidence_counts = dict(con.execute(
        "SELECT source_kind,count(*) FROM evidence GROUP BY source_kind"
    ).fetchall())
    node_score_count = con.execute("SELECT count(*) FROM node_scores").fetchone()[0]
    knowledge_line_count = con.execute(
        "SELECT sum(end_line-start_line+1) FROM fragments WHERE source_document_id='note3' AND knowledge_node_id IS NOT NULL"
    ).fetchone()[0]
    meta_line_count = con.execute(
        "SELECT sum(end_line-start_line+1) FROM fragments WHERE source_document_id='note3' AND knowledge_node_id IS NULL"
    ).fetchone()[0]
    knowledge_fragment_count = con.execute(
        "SELECT count(*) FROM fragments WHERE source_document_id='note3' AND knowledge_node_id IS NOT NULL"
    ).fetchone()[0]
    meta_fragment_count = len(meta_rows)

    (HERE / "04-AKI切分目录与关系审计.md").write_text(
f"""# AKI切分目录与关系审计

## 当前做到什么程度

本次只审计 AKI 段落：原笔记 `3-急性肾损伤机制与表现.md` 的 **L764–L2747**。

- 范围总计：**1984 行**。
- 知识正文：**{knowledge_line_count} 行 / {knowledge_fragment_count} 个知识片段**。
- 非知识但保留：**{meta_line_count} 行 / {meta_fragment_count} 个 meta 片段**。
- 覆盖率：**100%**。这 1984 行每一行都恰好属于一个 fragment，没有漏行、没有重叠。
- 空行没有“消失”：空行跟随所在 fragment 一起保存；源文档全文也另存于 `source_documents.raw_text`。

## 目录树与每个目录的片段数

这里的“直挂”指 fragment 直接归到这个坑位；“子树合计”包含所有子目录片段。

{chr(10).join(tree_lines)}

## 没有进入知识树、但仍保存的内容

{chr(10).join(meta_lines)}

这些内容不会参加知识点评分，但仍在数据库中，因此既不会丢字，也可以完整还原原笔记。

## 当前关系图

树本身已经表达“属于谁”，所以不再拿 prerequisite 重复画父子关系。目前 AKI 只保留真正需要的跨枝关系：

{chr(10).join(rel_lines2)}

可以把它读成：

```text
肾功能基础 ── prerequisite ──> AKI发病机制
AKI概念框架 ─ prerequisite ──> 病因分类 ── soft prerequisite ──> 发病机制

少尿期 ── sequence ──> 多尿期 ── sequence ──> 恢复期
```

同一节点允许多条入边和出边；这里只是当前 AKI 最小必要关系，不是“一个节点只能有一条关系”。

## 加权目前做到哪

**还没有正式开始算总分。**当前数据库只有示例 evidence，用来验证结构：

- syllabus：{evidence_counts.get('syllabus',0)} 条
- knowledge_outline：{evidence_counts.get('knowledge_outline',0)} 条
- classroom：{evidence_counts.get('classroom',0)} 条
- 串讲/往年题：0 条正式录入
- 题型适配：0 条正式录入
- `node_scores`：**{node_score_count} 条**

所以现在没有一个“看似精确但其实没审计完”的分数。下一阶段应当是逐节点灌证据，然后再选择评分 scheme 重算。
""", encoding="utf-8")

    # --- A reviewable export: source-order knowledge only, with explicit paths. ---
    review_rows = con.execute(
        """SELECT f.id,f.start_line,f.end_line,n.canonical_path,f.text
           FROM fragments f
           JOIN knowledge_nodes n ON n.id=f.knowledge_node_id
           WHERE f.source_document_id='note3'
           ORDER BY f.start_line"""
    ).fetchall()
    parts = [
        "# AKI复习导出 v0\n\n",
        "> 这是**切分/目录模型验收版**，不是最终评分版。正文全部来自原ClassFlow笔记；当前顺序按原课自然顺序，meta通知已移到文末，不重写正文。\n\n",
        "> 真正排序权重尚未定稿；现在先看‘一个片段是不是一个合理复习单元、目录坑位是不是合理’。\n\n",
    ]
    last_path = None
    signal_re = re.compile(r"【([^】]*(?:重点|考点|考试|简答|论述|掌握|三最)[^】]*)】")
    for fid, start, end, path, text in review_rows:
        if path != last_path:
            parts.append(f"\n---\n\n## {path}\n\n")
            last_path = path
        signals = []
        for s in signal_re.findall(text):
            if s not in signals:
                signals.append(s)
        extra = []
        if "很容易出论述题" in text:
            extra.append("很容易出论述题")
        if "可能考简答" in text or "特别适合出" in text:
            extra.append("简答题强信号")
        meta = f"> 原文 L{start}–L{end}｜片段 `{fid}`"
        if signals or extra:
            meta += "｜课堂显式信号：" + "、".join(signals + extra)
        parts.extend([meta + "\n\n", text.rstrip() + "\n\n"])

    parts.append("\n---\n\n## 保留但不参与知识排序的原文\n\n")
    for fid, start, end, status, text in meta_rows:
        parts.append(f"> L{start}–L{end}｜`{status}`｜`{fid}`\n\n{text.rstrip()}\n\n")
    (HERE / "05-AKI复习导出-v0.md").write_text("".join(parts), encoding="utf-8")


if __name__ == "__main__":
    build()
