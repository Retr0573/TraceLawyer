#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版批量公司测试脚本
快速测试data/档案3下的所有公司
"""

import os
import glob
import time
from datetime import datetime
from auto_test import AutoTestRunner

def find_company_folders(root_path="data/档案3"):
    """查找所有公司文件夹"""
    company_folders = []
    
    if not os.path.exists(root_path):
        print(f"❌ 路径不存在: {root_path}")
        return company_folders
    
    for item in os.listdir(root_path):
        if item.startswith('.'):
            continue
            
        item_path = os.path.join(root_path, item)
        if os.path.isdir(item_path):
            # 检查是否有PDF文件
            pdf_pattern = os.path.join(item_path, "**", "*.pdf")
            pdf_files = glob.glob(pdf_pattern, recursive=True)
            
            if pdf_files:
                company_folders.append((item, item_path, len(pdf_files)))
                print(f"📁 {item} - {len(pdf_files)} 个PDF文件")
            else:
                print(f"⚠️  {item} - 无PDF文件，跳过")
    
    return company_folders

def test_all_companies():
    """测试所有公司"""
    print("🚀 开始批量公司测试...")
    print("-" * 60)
    
    # 查找公司文件夹
    companies = find_company_folders()
    
    if not companies:
        print("❌ 未找到任何公司文件夹")
        return
    
    print(f"\n📋 找到 {len(companies)} 个公司，开始测试...")
    
    # 测试结果统计
    results = []
    start_time = time.time()
    
    for i, (company_name, folder_path, pdf_count) in enumerate(companies, 1):
        print(f"\n{'='*50}")
        print(f"📍 进度: {i}/{len(companies)}")
        print(f"🏢 公司: {company_name}")
        print(f"📄 PDF数量: {pdf_count}")
        print(f"{'='*50}")
        
        test_start = time.time()
        
        try:
            # 创建输出目录
            output_dir = f"quick_test_results/{company_name}"
            os.makedirs(output_dir, exist_ok=True)
            
            # 运行测试
            runner = AutoTestRunner(
                base_url="http://localhost:5500",
                output_dir=output_dir
            )
            
            success = runner.run_full_test(
                pdf_path=folder_path,
                k_pages=10
            )
            
            test_duration = time.time() - test_start
            
            result = {
                "company": company_name,
                "success": success,
                "pdf_count": pdf_count,
                "duration": round(test_duration, 2),
                "errors": len(runner.test_results.get("errors", []))
            }
            
            results.append(result)
            
            if success:
                print(f"✅ {company_name} 测试成功! 耗时: {test_duration:.2f}秒")
            else:
                print(f"❌ {company_name} 测试失败!")
        
        except Exception as e:
            print(f"❌ {company_name} 测试异常: {e}")
            results.append({
                "company": company_name,
                "success": False,
                "pdf_count": pdf_count,
                "duration": time.time() - test_start,
                "errors": 1,
                "exception": str(e)
            })
        
        # 测试间隔
        if i < len(companies):
            print("⏸️  等待 10 秒...")
            time.sleep(10)
    
    # 生成总结报告
    total_duration = time.time() - start_time
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"\n{'='*60}")
    print("🎉 批量测试完成!")
    print(f"{'='*60}")
    print(f"📊 测试统计:")
    print(f"  🏢 总公司数: {len(results)}")
    print(f"  ✅ 成功: {len(successful)} 个")
    print(f"  ❌ 失败: {len(failed)} 个")
    print(f"  📈 成功率: {len(successful)/len(results)*100:.1f}%")
    print(f"  ⏱️  总耗时: {total_duration/60:.1f} 分钟")
    print(f"  📄 总PDF: {sum(r['pdf_count'] for r in results)} 个")
    
    # 详细结果
    print(f"\n📋 详细结果:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {result['company']} - {result['pdf_count']}个PDF - {result['duration']:.1f}秒")
    
    if failed:
        print(f"\n❌ 失败的公司:")
        for result in failed:
            print(f"  - {result['company']}: {result.get('exception', '测试失败')}")
    
    # 保存简单报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"quick_batch_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"批量公司测试报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"="*60 + "\n\n")
        
        f.write(f"测试统计:\n")
        f.write(f"  总公司数: {len(results)}\n")
        f.write(f"  成功: {len(successful)} 个\n")
        f.write(f"  失败: {len(failed)} 个\n")
        f.write(f"  成功率: {len(successful)/len(results)*100:.1f}%\n")
        f.write(f"  总耗时: {total_duration/60:.1f} 分钟\n")
        f.write(f"  总PDF: {sum(r['pdf_count'] for r in results)} 个\n\n")
        
        f.write(f"详细结果:\n")
        for result in results:
            status = "成功" if result["success"] else "失败"
            f.write(f"  {result['company']}: {status} - {result['pdf_count']}个PDF - {result['duration']:.1f}秒\n")
    
    print(f"\n📄 报告已保存到: {report_file}")

if __name__ == "__main__":
    test_all_companies()
