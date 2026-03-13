#!/usr/bin/env python3
"""
生成热点趋势数据的脚本
Generate trending data for hot keywords

功能说明 / Features:
- 读取最近 N 天的 JSONL 数据文件 / Read JSONL data files from recent N days
- 统计关键词在标题和摘要中的出现次数 / Count keyword occurrences in titles and summaries
- 计算趋势变化和类型 / Calculate trend changes and types
- 生成静态 JSON 文件供前端展示 / Generate static JSON file for frontend display
"""

import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from pathlib import Path


def parse_args():
    """解析命令行参数 / Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate trending data for hot keywords'
    )
    parser.add_argument(
        '--keywords',
        type=str,
        default='agent,diffusion,transformer,llm',
        help='Comma-separated list of keywords to track (default: agent,diffusion,transformer,llm)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to analyze (default: 7)'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='../data',
        help='Directory containing JSONL data files (default: ../data)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='../assets/trending-data.json',
        help='Output JSON file path (default: ../assets/trending-data.json)'
    )
    parser.add_argument(
        '--language',
        type=str,
        default='Chinese',
        help='Language for AI enhanced files (default: Chinese)'
    )
    return parser.parse_args()


def get_available_dates(data_dir: str, days: int, language: str) -> List[str]:
    """
    获取可用的数据文件日期列表
    Get list of available data file dates
    
    Args:
        data_dir: 数据目录路径 / Data directory path
        days: 要查找的天数 / Number of days to look for
        language: 语言标识 / Language identifier
        
    Returns:
        可用日期列表（降序）/ List of available dates (descending)
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"警告：数据目录不存在 / Warning: Data directory does not exist: {data_dir}", file=sys.stderr)
        return []
    
    available_dates = []
    today = datetime.now()
    
    # 向前查找最近 N 天的数据文件
    for i in range(days):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        
        # 检查 AI 增强文件是否存在
        ai_file = data_path / f"{date_str}_AI_enhanced_{language}.jsonl"
        if ai_file.exists():
            available_dates.append(date_str)
    
    return sorted(available_dates, reverse=True)


def load_papers_from_file(file_path: str) -> List[Dict]:
    """
    从 JSONL 文件加载论文数据
    Load paper data from JSONL file
    
    Args:
        file_path: JSONL 文件路径 / JSONL file path
        
    Returns:
        论文数据列表 / List of paper data
    """
    papers = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        paper = json.loads(line)
                        papers.append(paper)
                    except json.JSONDecodeError as e:
                        print(f"警告：解析 JSON 行失败 / Warning: Failed to parse JSON line: {e}", file=sys.stderr)
                        continue
    except Exception as e:
        print(f"错误：读取文件失败 / Error: Failed to read file {file_path}: {e}", file=sys.stderr)
    
    return papers


def count_keyword_in_papers(papers: List[Dict], keyword: str) -> int:
    """
    统计关键词在论文列表中的出现次数
    Count keyword occurrences in paper list
    
    Args:
        papers: 论文数据列表 / List of paper data
        keyword: 要统计的关键词 / Keyword to count
        
    Returns:
        出现次数 / Occurrence count
    """
    count = 0
    keyword_lower = keyword.lower()
    
    for paper in papers:
        title = paper.get('title', '').lower()
        summary = paper.get('summary', '')
        
        # 优先使用 AI 生成的 tldr，如果没有则使用原始 summary
        if 'AI' in paper and isinstance(paper['AI'], dict):
            tldr = paper['AI'].get('tldr', '')
            if tldr and tldr != 'Summary generation failed':
                summary = tldr
        
        summary_lower = summary.lower()
        
        # 检查关键词是否出现在标题或摘要中
        if keyword_lower in title or keyword_lower in summary_lower:
            count += 1
    
    return count


def calculate_trend_type(daily_counts: List[int]) -> Tuple[str, float]:
    """
    计算趋势类型和变化百分比
    Calculate trend type and change percentage
    
    Args:
        daily_counts: 每日计数列表 / List of daily counts
        
    Returns:
        (趋势类型, 变化百分比) / (trend type, change percentage)
    """
    if len(daily_counts) < 4:
        return 'stable', 0.0
    
    # 计算最近 3 天的平均值
    recent_avg = sum(daily_counts[-3:]) / 3
    
    # 计算之前几天的平均值
    older_avg = sum(daily_counts[:-3]) / (len(daily_counts) - 3)
    
    # 计算变化百分比
    if older_avg > 0:
        change_percent = ((recent_avg - older_avg) / older_avg) * 100
    else:
        change_percent = 0.0
    
    # 确定趋势类型
    if change_percent > 20:
        trend_type = 'rising'
    elif change_percent < -20:
        trend_type = 'falling'
    else:
        trend_type = 'stable'
    
    return trend_type, round(change_percent, 1)


def generate_trending_data(keywords: List[str], dates: List[str], data_dir: str, language: str) -> Dict:
    """
    生成热点趋势数据
    Generate trending data
    
    Args:
        keywords: 关键词列表 / List of keywords
        dates: 日期列表 / List of dates
        data_dir: 数据目录路径 / Data directory path
        language: 语言标识 / Language identifier
        
    Returns:
        趋势数据字典 / Trending data dictionary
    """
    data_path = Path(data_dir)
    trending_keywords = []
    
    for keyword in keywords:
        keyword = keyword.strip()
        if not keyword:
            continue
        
        daily_counts = []
        keyword_dates = []
        total_count = 0
        
        # 按日期顺序处理（从旧到新）
        for date in reversed(dates):
            file_path = data_path / f"{date}_AI_enhanced_{language}.jsonl"
            
            if not file_path.exists():
                continue
            
            papers = load_papers_from_file(str(file_path))
            count = count_keyword_in_papers(papers, keyword)
            
            daily_counts.append(count)
            keyword_dates.append(date)
            total_count += count
        
        # 计算趋势类型和变化百分比
        trend_type, change_percent = calculate_trend_type(daily_counts)
        
        trending_keywords.append({
            'keyword': keyword,
            'totalCount': total_count,
            'dailyCounts': daily_counts,
            'dates': keyword_dates,
            'changePercent': change_percent,
            'trendType': trend_type
        })
        
        print(f"✓ 关键词 '{keyword}': {total_count} 篇论文, 趋势: {trend_type} ({change_percent:+.1f}%)", file=sys.stderr)
    
    return {
        'keywords': trending_keywords,
        'generatedAt': datetime.utcnow().isoformat() + 'Z',
        'daysAnalyzed': len(dates)
    }


def save_trending_data(data: Dict, output_path: str):
    """
    保存趋势数据到 JSON 文件
    Save trending data to JSON file
    
    Args:
        data: 趋势数据 / Trending data
        output_path: 输出文件路径 / Output file path
    """
    output_file = Path(output_path)
    
    # 确保输出目录存在
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 趋势数据已保存到 / Trending data saved to: {output_path}", file=sys.stderr)
    except Exception as e:
        print(f"❌ 保存文件失败 / Failed to save file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """主函数 / Main function"""
    args = parse_args()
    
    print("=" * 60, file=sys.stderr)
    print("🔥 生成热点趋势数据 / Generating Trending Data", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # 解析关键词列表
    keywords = [k.strip() for k in args.keywords.split(',') if k.strip()]
    print(f"📊 关键词 / Keywords: {', '.join(keywords)}", file=sys.stderr)
    print(f"📅 分析天数 / Days to analyze: {args.days}", file=sys.stderr)
    print(f"📁 数据目录 / Data directory: {args.data_dir}", file=sys.stderr)
    print(f"🌐 语言 / Language: {args.language}", file=sys.stderr)
    print(f"💾 输出文件 / Output file: {args.output}", file=sys.stderr)
    print("-" * 60, file=sys.stderr)
    
    # 获取可用日期
    available_dates = get_available_dates(args.data_dir, args.days, args.language)
    
    if not available_dates:
        print("⚠️  警告：未找到可用的数据文件 / Warning: No available data files found", file=sys.stderr)
        # 生成空数据
        empty_data = {
            'keywords': [],
            'generatedAt': datetime.utcnow().isoformat() + 'Z',
            'daysAnalyzed': 0
        }
        save_trending_data(empty_data, args.output)
        return
    
    print(f"✓ 找到 {len(available_dates)} 天的数据 / Found {len(available_dates)} days of data", file=sys.stderr)
    print(f"  日期范围 / Date range: {available_dates[-1]} 至 / to {available_dates[0]}", file=sys.stderr)
    print("-" * 60, file=sys.stderr)
    
    # 生成趋势数据
    trending_data = generate_trending_data(keywords, available_dates, args.data_dir, args.language)
    
    # 保存到文件
    save_trending_data(trending_data, args.output)
    
    print("=" * 60, file=sys.stderr)
    print("✅ 完成 / Done!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == '__main__':
    main()

