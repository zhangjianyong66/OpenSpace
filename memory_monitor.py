#!/usr/bin/env python3
"""
记忆监控系统 - 扫描记忆文件，检查完整性，更新索引
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

# 配置
MEMORY_DIR = Path.home() / ".openclaw" / "workspace" / "memory"
INDEX_FILE = MEMORY_DIR / "index.json"
EXCLUDE_DIRS = {"archive", "etf_analysis", "qmd", "knowledge-base"}
REPORT_DIR = Path("/Users/zhangjianyong/project/OpenSpace")

def scan_md_files():
    """扫描所有 .md 文件"""
    md_files = []
    errors = []
    
    if not MEMORY_DIR.exists():
        return [], [f"记忆目录不存在: {MEMORY_DIR}"]
    
    for item in MEMORY_DIR.iterdir():
        if item.is_file() and item.suffix == ".md":
            md_files.append(item)
        elif item.is_dir() and item.name not in EXCLUDE_DIRS:
            # 扫描子目录中的 .md 文件
            for sub_item in item.rglob("*.md"):
                md_files.append(sub_item)
    
    return md_files, errors

def check_file_integrity(file_path):
    """检查文件完整性"""
    try:
        stat = file_path.stat()
        if stat.st_size == 0:
            return False, "文件为空"
        
        # 尝试读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 计算文件哈希
        file_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        return True, {
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "hash": file_hash,
            "content": content
        }
    except UnicodeDecodeError:
        return False, "文件编码错误"
    except PermissionError:
        return False, "权限不足"
    except Exception as e:
        return False, f"读取错误: {str(e)}"

def extract_memory_entry(file_path, integrity_result):
    """提取记忆条目"""
    content = integrity_result["content"]
    lines = content.split('\n')
    
    # 提取标题（第一行非空行）
    title = ""
    for line in lines:
        line = line.strip()
        if line:
            title = line.lstrip('#').strip()
            break
    
    if not title:
        title = file_path.stem
    
    # 限制标题预览长度
    title_preview = title[:50] + "..." if len(title) > 50 else title
    
    # 从文件名提取日期
    filename = file_path.name
    date_str = None
    if filename.startswith("2026-03-") or filename.startswith("2025-"):
        date_str = filename[:10]
    
    return {
        "file": filename,
        "path": str(file_path.relative_to(MEMORY_DIR)),
        "title_preview": title_preview,
        "date": date_str,
        "size": integrity_result["size"],
        "modified": integrity_result["modified"],
        "hash": integrity_result["hash"]
    }

def load_existing_index():
    """加载现有索引"""
    if INDEX_FILE.exists():
        try:
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"警告: 无法加载现有索引: {e}")
            return {"version": "1.0", "memories": []}
    return {"version": "1.0", "memories": []}

def update_index(current_memories, existing_index):
    """更新索引，返回新增和更新的记忆"""
    existing_memories = {m.get("file", m.get("path", "")): m for m in existing_index.get("memories", [])}
    
    new_memories = []
    updated_memories = []
    unchanged_memories = []
    
    now = datetime.now().isoformat()
    
    for mem in current_memories:
        file_key = mem["file"]
        
        if file_key not in existing_memories:
            # 新增记忆
            mem["indexed_at"] = now
            mem["status"] = "new"
            new_memories.append(mem)
        else:
            existing = existing_memories[file_key]
            if existing.get("hash") != mem["hash"]:
                # 更新的记忆
                mem["indexed_at"] = now
                mem["status"] = "updated"
                mem["previous_hash"] = existing.get("hash")
                updated_memories.append(mem)
            else:
                # 未变化的记忆
                mem["indexed_at"] = existing.get("indexed_at", now)
                mem["status"] = "unchanged"
                unchanged_memories.append(mem)
    
    # 合并所有记忆
    all_memories = new_memories + updated_memories + unchanged_memories
    
    # 按日期排序
    all_memories.sort(key=lambda x: (x.get("date") or "", x.get("file", "")), reverse=True)
    
    return {
        "version": "1.0",
        "generated_at": now,
        "total_memories": len(all_memories),
        "memories": all_memories
    }, new_memories, updated_memories

def save_index(index_data):
    """保存索引文件"""
    try:
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        return True, None
    except Exception as e:
        return False, str(e)

def generate_report(scan_stats, new_memories, updated_memories, errors):
    """生成监控报告"""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    
    # JSON 报告
    report_data = {
        "scan_time": now.isoformat(),
        "statistics": scan_stats,
        "new_memories": [
            {"file": m["file"], "title": m["title_preview"], "date": m.get("date")}
            for m in new_memories
        ],
        "updated_memories": [
            {"file": m["file"], "title": m["title_preview"], "date": m.get("date")}
            for m in updated_memories
        ],
        "errors": errors
    }
    
    json_report_path = REPORT_DIR / f"memory_monitor_report_{timestamp}.json"
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    # Markdown 报告
    md_report = f"""# 记忆监控报告

**扫描时间**: {now.strftime("%Y-%m-%d %H:%M:%S")}

## 统计信息

| 指标 | 数值 |
|------|------|
| 扫描文件数 | {scan_stats['total_scanned']} |
| 成功读取 | {scan_stats['successful_reads']} |
| 读取失败 | {scan_stats['failed_reads']} |
| 新增记忆 | {scan_stats['new_count']} |
| 更新记忆 | {scan_stats['updated_count']} |

## 新增记忆 ({len(new_memories)})

"""
    
    for mem in new_memories[:10]:  # 只显示前10个
        md_report += f"- **{mem['file']}**: {mem['title_preview']}\n"
    
    if len(new_memories) > 10:
        md_report += f"- ... 还有 {len(new_memories) - 10} 个新增记忆\n"
    
    md_report += f"""
## 更新记忆 ({len(updated_memories)})

"""
    
    for mem in updated_memories[:10]:
        md_report += f"- **{mem['file']}**: {mem['title_preview']}\n"
    
    if len(updated_memories) > 10:
        md_report += f"- ... 还有 {len(updated_memories) - 10} 个更新记忆\n"
    
    if errors:
        md_report += """
## 异常报告

"""
        for error in errors:
            md_report += f"- ⚠️ {error}\n"
    else:
        md_report += """
## 异常报告

✅ 未发现异常
"""
    
    md_report_path = REPORT_DIR / f"memory_monitor_report_{timestamp}.md"
    with open(md_report_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    
    return json_report_path, md_report_path

def main():
    print("=" * 60)
    print("记忆监控系统启动")
    print("=" * 60)
    
    # 1. 扫描文件
    print("\n[1/5] 扫描 .md 文件...")
    md_files, scan_errors = scan_md_files()
    print(f"  发现 {len(md_files)} 个 .md 文件")
    
    # 2. 检查完整性
    print("\n[2/5] 检查文件完整性...")
    valid_memories = []
    integrity_errors = []
    
    for file_path in md_files:
        success, result = check_file_integrity(file_path)
        if success:
            entry = extract_memory_entry(file_path, result)
            valid_memories.append(entry)
        else:
            integrity_errors.append(f"{file_path.name}: {result}")
    
    print(f"  成功读取: {len(valid_memories)}")
    print(f"  读取失败: {len(integrity_errors)}")
    
    # 3. 加载现有索引
    print("\n[3/5] 加载现有索引...")
    existing_index = load_existing_index()
    existing_count = len(existing_index.get("memories", []))
    print(f"  现有记忆条目: {existing_count}")
    
    # 4. 更新索引
    print("\n[4/5] 更新索引...")
    new_index, new_memories, updated_memories = update_index(valid_memories, existing_index)
    
    # 5. 保存索引
    print("\n[5/5] 保存索引...")
    success, error = save_index(new_index)
    if success:
        print(f"  ✅ 索引已更新: {INDEX_FILE}")
    else:
        print(f"  ❌ 索引保存失败: {error}")
        integrity_errors.append(f"索引保存失败: {error}")
    
    # 6. 生成报告
    print("\n[6/5] 生成监控报告...")
    scan_stats = {
        "total_scanned": len(md_files),
        "successful_reads": len(valid_memories),
        "failed_reads": len(integrity_errors),
        "new_count": len(new_memories),
        "updated_count": len(updated_memories)
    }
    
    json_path, md_path = generate_report(scan_stats, new_memories, updated_memories, integrity_errors)
    print(f"  JSON 报告: {json_path}")
    print(f"  Markdown 报告: {md_path}")
    
    # 输出摘要
    print("\n" + "=" * 60)
    print("扫描完成摘要")
    print("=" * 60)
    print(f"扫描文件数: {scan_stats['total_scanned']}")
    print(f"新增记忆数: {scan_stats['new_count']}")
    print(f"更新记忆数: {scan_stats['updated_count']}")
    print(f"异常数: {len(integrity_errors)}")
    print(f"索引条目总数: {new_index['total_memories']}")
    
    if new_memories:
        print("\n新增记忆示例:")
        for mem in new_memories[:5]:
            print(f"  - {mem['file']}: {mem['title_preview']}")
    
    if integrity_errors:
        print("\n异常:")
        for err in integrity_errors[:5]:
            print(f"  ⚠️ {err}")

if __name__ == "__main__":
    main()
