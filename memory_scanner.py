#!/usr/bin/env python3
"""
记忆监控系统 - 扫描 ~/.openclaw/workspace/memory/ 目录
统计文件数量，提取记忆数量，检查文件损坏情况
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path.home() / ".openclaw" / "workspace" / "memory"

def scan_memory_directory():
    """扫描记忆目录，返回详细统计信息"""
    
    stats = {
        "scan_time": datetime.now().isoformat(),
        "total_files": 0,
        "total_dirs": 0,
        "file_types": {},
        "md_files": [],
        "json_files": [],
        "corrupted_files": [],
        "read_errors": [],
        "memory_entries": [],
        "new_memories": 0,
        "updated_memories": 0,
        "total_memories": 0
    }
    
    if not MEMORY_DIR.exists():
        return {"error": f"Directory {MEMORY_DIR} does not exist"}
    
    # 遍历所有文件
    for item in MEMORY_DIR.rglob("*"):
        if item.is_dir():
            stats["total_dirs"] += 1
            continue
            
        stats["total_files"] += 1
        
        # 统计文件类型
        ext = item.suffix.lower()
        stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
        
        # 处理 Markdown 文件
        if ext == ".md":
            stats["md_files"].append(str(item.relative_to(MEMORY_DIR)))
            analyze_markdown_file(item, stats)
            
        # 处理 JSON 文件
        elif ext == ".json":
            stats["json_files"].append(str(item.relative_to(MEMORY_DIR)))
            analyze_json_file(item, stats)
    
    return stats

def analyze_markdown_file(filepath, stats):
    """分析 Markdown 文件，提取记忆条目"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查文件是否为空
        if not content.strip():
            stats["corrupted_files"].append(f"{filepath}: Empty file")
            return
            
        # 从 Markdown 提取记忆条目
        # 通常以 ## 或 ### 开头的部分代表一个记忆条目
        memory_count = len(re.findall(r'^#{2,3}\s+', content, re.MULTILINE))
        
        # 如果没有标题格式，检查是否有结构化内容
        if memory_count == 0:
            # 检查是否有列表项或其他结构化内容
            if re.search(r'^[-*]\s+|^\d+\.\s+', content, re.MULTILINE):
                memory_count = len(re.findall(r'(?:^[-*]\s+|^\d+\.\s+).+', content, re.MULTILINE))
            else:
                # 如果内容有意义（超过100字符），算作1个记忆
                if len(content) > 100:
                    memory_count = 1
        
        # 提取日期信息（从文件名）
        filename = filepath.name
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        
        memory_entry = {
            "file": str(filepath.relative_to(MEMORY_DIR)),
            "type": "markdown",
            "memory_count": max(1, memory_count),
            "file_size": filepath.stat().st_size,
            "date": date_match.group(1) if date_match else None
        }
        
        stats["memory_entries"].append(memory_entry)
        stats["total_memories"] += memory_entry["memory_count"]
        
        # 判断是新增还是更新（基于文件修改时间）
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        today = datetime.now().date()
        if mtime.date() == today:
            stats["new_memories"] += memory_entry["memory_count"]
        elif (today - mtime.date()).days <= 7:
            stats["updated_memories"] += memory_entry["memory_count"]
            
    except Exception as e:
        stats["read_errors"].append(f"{filepath}: {str(e)}")

def analyze_json_file(filepath, stats):
    """分析 JSON 文件，提取记忆条目"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 尝试解析 JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            stats["corrupted_files"].append(f"{filepath}: Invalid JSON - {str(e)}")
            return
            
        # 计算记忆条目数
        memory_count = 0
        if isinstance(data, list):
            memory_count = len(data)
        elif isinstance(data, dict):
            # 检查是否是记忆条目对象
            if any(key in data for key in ['memories', 'entries', 'data', 'items']):
                for key in ['memories', 'entries', 'data', 'items']:
                    if key in data and isinstance(data[key], list):
                        memory_count = len(data[key])
                        break
            else:
                # 单个记忆条目
                memory_count = 1
        
        memory_entry = {
            "file": str(filepath.relative_to(MEMORY_DIR)),
            "type": "json",
            "memory_count": memory_count,
            "file_size": filepath.stat().st_size
        }
        
        stats["memory_entries"].append(memory_entry)
        stats["total_memories"] += memory_count
        
        # 判断是新增还是更新
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        today = datetime.now().date()
        if mtime.date() == today:
            stats["new_memories"] += memory_count
        elif (today - mtime.date()).days <= 7:
            stats["updated_memories"] += memory_count
            
    except Exception as e:
        stats["read_errors"].append(f"{filepath}: {str(e)}")

def generate_report(stats):
    """生成监控报告"""
    report = []
    report.append("=" * 60)
    report.append("记忆监控系统报告")
    report.append("=" * 60)
    report.append(f"扫描时间: {stats.get('scan_time', 'N/A')}")
    report.append(f"扫描目录: {MEMORY_DIR}")
    report.append("")
    report.append("【文件统计】")
    report.append(f"  - 扫描文件总数: {stats['total_files']}")
    report.append(f"  - 目录数量: {stats['total_dirs']}")
    report.append(f"  - Markdown文件: {len(stats['md_files'])}")
    report.append(f"  - JSON文件: {len(stats['json_files'])}")
    report.append("")
    report.append("【文件类型分布】")
    for ext, count in sorted(stats['file_types'].items(), key=lambda x: x[1], reverse=True):
        report.append(f"  - {ext if ext else '(无扩展名)'}: {count}")
    report.append("")
    report.append("【记忆统计】")
    report.append(f"  - 记忆条目总数: {stats['total_memories']}")
    report.append(f"  - 新增记忆数: {stats['new_memories']}")
    report.append(f"  - 更新记忆数: {stats['updated_memories']}")
    report.append("")
    report.append("【异常情况】")
    if stats['corrupted_files']:
        report.append(f"  - 损坏文件: {len(stats['corrupted_files'])}")
        for f in stats['corrupted_files'][:5]:  # 只显示前5个
            report.append(f"    * {f}")
        if len(stats['corrupted_files']) > 5:
            report.append(f"    ... 还有 {len(stats['corrupted_files']) - 5} 个")
    else:
        report.append("  - 损坏文件: 0")
        
    if stats['read_errors']:
        report.append(f"  - 读取错误: {len(stats['read_errors'])}")
        for e in stats['read_errors'][:5]:
            report.append(f"    * {e}")
        if len(stats['read_errors']) > 5:
            report.append(f"    ... 还有 {len(stats['read_errors']) - 5} 个")
    else:
        report.append("  - 读取错误: 0")
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)

if __name__ == "__main__":
    print("开始扫描记忆目录...")
    stats = scan_memory_directory()
    
    # 生成并打印报告
    report = generate_report(stats)
    print(report)
    
    # 保存详细报告到 JSON
    output_file = Path("/Users/zhangjianyong/project/OpenSpace/memory_monitor_report.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n详细报告已保存到: {output_file}")
