#!/usr/bin/env python3
"""
Memory Monitor Task - 扫描 ~/.openclaw/workspace/memory/ 目录
检查文件完整性，统计文件数量，生成监控报告
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

def calculate_md5(filepath):
    """计算文件的 MD5 哈希值"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        return f"ERROR: {str(e)}"

def check_file_integrity(filepath):
    """检查文件完整性"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return {
                'readable': True,
                'size': len(content),
                'error': None
            }
    except Exception as e:
        return {
            'readable': False,
            'size': 0,
            'error': str(e)
        }

def main():
    memory_dir = Path.home() / '.openclaw/workspace/memory'
    learnings_dir = Path.home() / '.openclaw/workspace/.learnings'
    
    report = {
        'scan_time': datetime.now().isoformat(),
        'summary': {},
        'index_file': {},
        'memory_files': [],
        'learnings_files': [],
        'errors': []
    }
    
    print("=" * 60)
    print("内存监控系统扫描报告")
    print("=" * 60)
    print(f"扫描时间: {report['scan_time']}")
    print()
    
    # 1. 检查 index.json
    print("【1】检查索引文件 index.json")
    index_file = memory_dir / 'index.json'
    if index_file.exists():
        integrity = check_file_integrity(index_file)
        report['index_file'] = {
            'exists': True,
            'path': str(index_file),
            'readable': integrity['readable'],
            'size': integrity['size'],
            'error': integrity['error']
        }
        
        if integrity['readable']:
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    report['index_file']['total_memories'] = index_data.get('total_count', 0)
                    report['index_file']['last_updated'] = index_data.get('last_updated', 'unknown')
                    print(f"  ✓ 索引文件存在且可读")
                    print(f"  - 记录总数: {index_data.get('total_count', 0)}")
                    print(f"  - 最后更新: {index_data.get('last_updated', 'unknown')}")
            except json.JSONDecodeError as e:
                report['index_file']['error'] = f"JSON 解析错误: {str(e)}"
                report['errors'].append(f"index.json JSON 解析错误: {str(e)}")
                print(f"  ✗ JSON 解析错误: {str(e)}")
        else:
            report['errors'].append(f"index.json 读取错误: {integrity['error']}")
            print(f"  ✗ 读取错误: {integrity['error']}")
    else:
        report['index_file'] = {'exists': False, 'path': str(index_file)}
        report['errors'].append("index.json 不存在")
        print(f"  ✗ 索引文件不存在")
    print()
    
    # 2. 扫描记忆文件 (YYYY-MM-DD.md 格式)
    print("【2】扫描记忆文件 (YYYY-MM-DD*.md)")
    memory_files = []
    memory_pattern_files = list(memory_dir.glob('2026-*.md'))
    
    for filepath in memory_pattern_files:
        integrity = check_file_integrity(filepath)
        file_info = {
            'filename': filepath.name,
            'path': str(filepath),
            'size': filepath.stat().st_size,
            'modified': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
            'readable': integrity['readable'],
            'error': integrity['error']
        }
        memory_files.append(file_info)
        
        if not integrity['readable']:
            report['errors'].append(f"{filepath.name} 读取错误: {integrity['error']}")
    
    report['memory_files'] = memory_files
    print(f"  ✓ 找到 {len(memory_files)} 个记忆文件")
    
    # 统计损坏文件
    corrupted = [f for f in memory_files if not f['readable']]
    if corrupted:
        print(f"  ⚠ 发现 {len(corrupted)} 个损坏文件")
    else:
        print(f"  ✓ 所有记忆文件完整可读")
    print()
    
    # 3. 扫描学习记录文件
    print("【3】扫描学习记录文件 (.learnings/)")
    learnings_files = []
    
    if learnings_dir.exists():
        learnings_pattern_files = list(learnings_dir.glob('LEARN-*.md'))
        
        for filepath in learnings_pattern_files:
            integrity = check_file_integrity(filepath)
            file_info = {
                'filename': filepath.name,
                'path': str(filepath),
                'size': filepath.stat().st_size,
                'modified': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
                'readable': integrity['readable'],
                'error': integrity['error']
            }
            learnings_files.append(file_info)
            
            if not integrity['readable']:
                report['errors'].append(f".learnings/{filepath.name} 读取错误: {integrity['error']}")
        
        print(f"  ✓ 找到 {len(learnings_files)} 个学习记录文件")
        
        corrupted_learn = [f for f in learnings_files if not f['readable']]
        if corrupted_learn:
            print(f"  ⚠ 发现 {len(corrupted_learn)} 个损坏文件")
        else:
            print(f"  ✓ 所有学习记录文件完整可读")
    else:
        report['errors'].append(".learnings/ 目录不存在")
        print(f"  ✗ .learnings/ 目录不存在")
    
    report['learnings_files'] = learnings_files
    print()
    
    # 4. 生成汇总
    print("【4】扫描汇总")
    total_files = len(memory_files) + len(learnings_files)
    total_errors = len(report['errors'])
    
    report['summary'] = {
        'total_files_scanned': total_files,
        'memory_files_count': len(memory_files),
        'learnings_files_count': len(learnings_files),
        'corrupted_files': len([f for f in memory_files + learnings_files if not f['readable']]),
        'total_errors': total_errors,
        'status': 'HEALTHY' if total_errors == 0 else 'WARNING'
    }
    
    print(f"  扫描文件总数: {total_files}")
    print(f"  - 记忆文件: {len(memory_files)}")
    print(f"  - 学习记录: {len(learnings_files)}")
    print(f"  损坏文件数: {report['summary']['corrupted_files']}")
    print(f"  错误总数: {total_errors}")
    print(f"  系统状态: {'✓ 健康' if total_errors == 0 else '⚠ 警告'}")
    print()
    
    # 5. 输出错误详情
    if report['errors']:
        print("【5】错误详情")
        for error in report['errors']:
            print(f"  - {error}")
        print()
    
    # 6. 保存报告
    report_file = Path('/Users/zhangjianyong/project/OpenSpace/memory_monitor_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    report_md = Path('/Users/zhangjianyong/project/OpenSpace/memory_monitor_report.md')
    with open(report_md, 'w', encoding='utf-8') as f:
        f.write("# 内存监控系统扫描报告\n\n")
        f.write(f"**扫描时间**: {report['scan_time']}\n\n")
        
        f.write("## 扫描汇总\n\n")
        f.write(f"- **总文件数**: {total_files}\n")
        f.write(f"- **记忆文件**: {len(memory_files)}\n")
        f.write(f"- **学习记录**: {len(learnings_files)}\n")
        f.write(f"- **损坏文件**: {report['summary']['corrupted_files']}\n")
        f.write(f"- **错误总数**: {total_errors}\n")
        f.write(f"- **系统状态**: {'✓ 健康' if total_errors == 0 else '⚠ 警告'}\n\n")
        
        f.write("## 索引文件状态\n\n")
        if report['index_file'].get('exists'):
            f.write(f"- **状态**: ✓ 存在\n")
            f.write(f"- **路径**: {report['index_file']['path']}\n")
            f.write(f"- **可读性**: {'✓ 可读' if report['index_file']['readable'] else '✗ 不可读'}\n")
            if report['index_file'].get('total_memories'):
                f.write(f"- **记录总数**: {report['index_file']['total_memories']}\n")
            if report['index_file'].get('last_updated'):
                f.write(f"- **最后更新**: {report['index_file']['last_updated']}\n")
        else:
            f.write(f"- **状态**: ✗ 不存在\n")
        f.write("\n")
        
        if report['errors']:
            f.write("## 错误详情\n\n")
            for error in report['errors']:
                f.write(f"- {error}\n")
            f.write("\n")
        
        f.write("## 文件列表\n\n")
        f.write("### 记忆文件 (前10个)\n\n")
        for f_info in sorted(memory_files, key=lambda x: x['modified'], reverse=True)[:10]:
            status = "✓" if f_info['readable'] else "✗"
            f.write(f"- {status} `{f_info['filename']}` ({f_info['size']} bytes)\n")
        
        if learnings_files:
            f.write("\n### 学习记录文件\n\n")
            for f_info in sorted(learnings_files, key=lambda x: x['modified'], reverse=True):
                status = "✓" if f_info['readable'] else "✗"
                f.write(f"- {status} `{f_info['filename']}` ({f_info['size']} bytes)\n")
    
    print("=" * 60)
    print("报告已生成:")
    print(f"  - JSON: {report_file}")
    print(f"  - Markdown: {report_md}")
    print("=" * 60)
    
    return report

if __name__ == '__main__':
    main()
