"""Create small reading attachments from the original project; never edit sources."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import statistics
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
REPORT = "任务调查报告_Benchmark_数据集_Scope与优化路线.md"


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2)


def portable_links(text):
    def replace(match):
        target = match.group(2).strip("<>")
        marker = "/数字人综合情感陪伴对话模型/"
        path = target.split(marker, 1)[-1]
        return f"{match.group(1)}（源文件：{path}）"
    return re.sub(r"\[([^\]]+)\]\((<?C:/[^\n]+?)\)", replace, text)


def quantiles(values):
    values = sorted(values)
    return {"min": min(values), "median": statistics.median(values),
            "p95": values[max(0, (95 * len(values) + 99) // 100 - 1)],
            "max": max(values)}


def main():
    report_text = portable_links((ROOT / REPORT).read_text(encoding="utf-8"))
    (OUT / "01_任务调查报告.txt").write_text(
        "这是既有助手调查报告的上传副本，不是官方比赛规则。\n"
        "本机文件链接已转换成源文件路径和行号；对应原始内容见附件 02 或公开仓库。\n\n"
        + report_text, encoding="utf-8")

    source_files = ["README.md", "participant/README.md", "participant/run_inference.py",
                    "participant/start.sh", "participant/requirements.txt",
                    "participant/configs/inference_config.json",
                    "participant/templates/submission_schema.json",
                    "participant/templates/submission_template.json",
                    "训练-验证-数据集/train/train_public.schema.json",
                    "训练-验证-数据集/val/val_public.schema.json",
                    "test_inference_data.jsonl"]
    source_parts = ["原始说明与完整代码\n每个 FILE 段保留全文；L0001 等标记是原文件行号，不属于源代码。\n"]
    for name in source_files:
        raw = (ROOT / name).read_bytes()
        lines = raw.decode("utf-8").splitlines()
        source_parts.append(f"\n===== FILE: {name} =====\nSHA256: {hashlib.sha256(raw).hexdigest()}\n"
                            + "\n".join(f"L{i:04d} | {line}" for i, line in enumerate(lines, 1))
                            + f"\n===== END FILE: {name} =====\n")
    docx = ROOT / "咪咕仝学平台实例创建demo V1.docx"
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(docx) as archive:
        xml = ET.fromstring(archive.read("word/document.xml"))
        paragraphs = []
        for i, para in enumerate(xml.findall(".//w:p", ns), 1):
            text = "".join(t.text or "" for t in para.findall(".//w:t", ns))
            if text.strip():
                paragraphs.append(f"P{i}: {text}")
    source_parts.append("\n===== DOCX 正文摘录（不包含内嵌截图） =====\n"
                        + docx.name + "\n" + "\n".join(paragraphs)
                        + "\n截图中的硬件示例不能当作正式比赛资源约定。\n")
    (OUT / "02_原始说明与完整代码.txt").write_text("\n".join(source_parts), encoding="utf-8")

    stats = {}
    samples = {}
    records = {}
    anomaly_evidence = []
    for split in ("train", "val"):
        relative = f"训练-验证-数据集/{split}/{split}_public.jsonl"
        path = ROOT / relative
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        records[split] = rows
        points = []
        emotions = Counter()
        profile_counts = {k: Counter() for k in ("personality_traits", "interests", "style")}
        empty_profiles = Counter()
        for line, row in enumerate(rows, 1):
            for index, point in enumerate(row["prediction_points"]):
                uid = point["target_user_turn_id"]
                aid = point["assistant_response_turn_id"]
                history = [turn for turn in row["turns"] if turn["turn_id"] <= uid]
                target = point["target"]
                emotions[target["emotion_label"]] += 1
                for key, values in target["user_profile"].items():
                    profile_counts[key].update(values)
                    if not values:
                        empty_profiles[key] += 1
                points.append({"source_file": relative, "source_line": line,
                               "conversation_id": row["conversation_id"],
                               "prediction_point_index_zero_based": index,
                               "target_user_turn_id": uid,
                               "assistant_response_turn_id": aid,
                               "history": history, "target": target})
                if aid != uid + 1:
                    anomaly_evidence.append({"source_file": relative, "source_line": line,
                        "conversation_id": row["conversation_id"], "prediction_point": point,
                        "note": "以下只摘录目标附近消息供核查，不是完整历史。此异常没有被自动修复。",
                        "nearby_turns": [t for t in row["turns"] if min(uid, aid)-1 <= t["turn_id"] <= max(uid, aid)+1]})
        samples[split] = points
        stats[split] = {"source_file": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "file_bytes": path.stat().st_size, "conversations": len(rows),
            "messages": sum(len(r["turns"]) for r in rows), "prediction_points": len(points),
            "emotion_counts": dict(emotions), "profile_label_counts": profile_counts,
            "empty_profile_counts": dict(empty_profiles),
            "history_content_characters": quantiles([sum(len(t["content"]) for t in p["history"]) for p in points]),
            "reference_reply_characters": quantiles([len(p["target"]["response_text"]) for p in points])}

    selected = []
    def select(pool, reason):
        used = {(p["source_file"], p["source_line"], p["prediction_point_index_zero_based"]) for p in selected}
        pool = [p for p in pool if p["assistant_response_turn_id"] == p["target_user_turn_id"] + 1
                and (p["source_file"], p["source_line"], p["prediction_point_index_zero_based"]) not in used]
        chosen = min(pool, key=lambda p: (abs(sum(len(t["content"]) for t in p["history"])-800)
                                         + abs(len(p["target"]["response_text"])-180), p["source_line"]))
        selected.append({"selection_reason": reason, **chosen})

    for emotion in sorted(stats["train"]["emotion_counts"]):
        select([p for p in samples["train"] if p["target"]["emotion_label"] == emotion], f"训练集中 {emotion} 类的可阅读案例；按接近中等历史/回复长度确定性选择")
    for style in ("brief", "detailed"):
        select([p for p in samples["val"] if style in p["target"]["user_profile"]["style"]], f"验证集风格标签 {style} 案例")
    select([p for p in samples["val"] if not any(p["target"]["user_profile"].values())], "验证集全部画像为空的案例")
    p95 = stats["val"]["history_content_characters"]["p95"]
    select([p for p in samples["val"] if sum(len(t["content"]) for t in p["history"]) >= p95], "验证集历史长度达到 P95 的案例；完整历史未截断")

    parts = ["数据概况与代表样本\n整理日期：2026-09-30\n"
             "全量统计来自本机原始两个 JSONL 文件。字符数是 content 的 Python len()，不是 token 数。\n"
             "下面是定向阅读样本，不是无偏抽样，不能据此推断总体类别比例或报告模型成绩。\n"
             "原始目标包括 memory_refs；当前推理提示词要求 []。此附件不改写原始标注，也不是训练就绪文件。\n"
             "本文件包含 2 条完整原始对话记录、20 个正常预测点阅读样本、4 个异常预测点证据。\n\n"
             "===== 全量程序统计 =====\n" + dump(stats)]
    for split in ("train", "val"):
        parts.append(f"\n===== 完整原始记录：{split}，原文件第 1 行 =====\n" + dump(records[split][0]))
    for i, sample in enumerate(selected, 1):
        parts.append(f"\n===== 正常预测点阅读样本 {i:02d} =====\n" + dump(sample))
    for i, evidence in enumerate(anomaly_evidence, 1):
        parts.append(f"\n===== 错位预测点证据 {i:02d} =====\n" + dump(evidence))
    (OUT / "03_数据概况与代表样本.txt").write_text("\n".join(parts) + "\n", encoding="utf-8")
    assert len(selected) == 20 and len(anomaly_evidence) == 4
    for path in sorted(OUT.glob("0[123]_*.txt")):
        print(json.dumps({"file": path.name, "bytes": path.stat().st_size}, ensure_ascii=False))


if __name__ == "__main__":
    main()
