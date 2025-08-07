#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量公司文件夹测试脚本
对data/档案3下的每个公司文件夹进行自动化测试
"""

import os
import glob
import json
import time
import requests
from datetime import datetime
import argparse
import sys
from auto_test import AutoTestRunner

class CompanyBatchTester:
    """批量公司测试器"""
    
    def __init__(self, base_url="http://localhost:5500", output_dir="company_test_results"):
        """
        初始化批量测试器
        
        Args:
            base_url (str): Web应用的基础URL
            output_dir (str): 测试结果输出目录
        """
        self.base_url = base_url
        self.output_dir = output_dir
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 批量测试结果存储
        self.batch_results = {
            "test_info": {
                "start_time": datetime.now().isoformat(),
                "base_url": base_url,
                "output_dir": output_dir
            },
            "companies": [],
            "summary": {},
            "errors": []
        }
    
    def find_company_folders(self, root_path):
        """
        查找所有公司文件夹
        
        Args:
            root_path (str): 根目录路径
            
        Returns:
            list: 公司文件夹路径列表
        """
        company_folders = []
        
        if not os.path.exists(root_path):
            print(f"❌ 路径不存在: {root_path}")
            return company_folders
        
        # 获取所有子文件夹
        for item in os.listdir(root_path):
            item_path = os.path.join(root_path, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                # 检查文件夹内是否有PDF文件
                pdf_files = self.find_pdf_files_in_folder(item_path)
                if pdf_files:
                    company_folders.append(item_path)
                    print(f"📁 找到公司文件夹: {item} (包含{len(pdf_files)}个PDF)")
                else:
                    print(f"⚠️  跳过空文件夹: {item} (无PDF文件)")
        
        return company_folders
    
    def find_pdf_files_in_folder(self, folder_path):
        """查找文件夹内的所有PDF文件"""
        pdf_files = []
        try:
            pattern = os.path.join(folder_path, "**", "*.pdf")
            pdf_files = glob.glob(pattern, recursive=True)
        except Exception as e:
            print(f"⚠️  扫描文件夹出错 {folder_path}: {e}")
        return pdf_files
    
    def test_single_company(self, company_folder, k_pages=10):
        """
        测试单个公司文件夹
        
        Args:
            company_folder (str): 公司文件夹路径
            k_pages (int): 每K页合并为一个分析单元
            
        Returns:
            dict: 测试结果
        """
        company_name = os.path.basename(company_folder)
        print(f"\n{'='*80}")
        print(f"🏢 开始测试公司: {company_name}")
        print(f"📂 文件夹路径: {company_folder}")
        print(f"{'='*80}")
        
        test_start_time = time.time()
        
        # 创建公司专用的输出目录
        company_output_dir = os.path.join(self.output_dir, company_name)
        os.makedirs(company_output_dir, exist_ok=True)
        
        # 创建测试运行器
        runner = AutoTestRunner(base_url=self.base_url, output_dir=company_output_dir)
        
        # 查找PDF文件
        pdf_files = self.find_pdf_files_in_folder(company_folder)
        
        company_result = {
            "company_name": company_name,
            "folder_path": company_folder,
            "pdf_count": len(pdf_files),
            "pdf_files": [os.path.basename(f) for f in pdf_files],
            "test_start_time": datetime.now().isoformat(),
            "k_pages": k_pages,
            "success": False,
            "errors": [],
            "ocr_results": [],
            "analysis_results": {},
            "test_duration": 0
        }
        
        try:
            if not pdf_files:
                error_msg = f"公司 {company_name} 文件夹内无PDF文件"
                print(f"⚠️  {error_msg}")
                company_result["errors"].append(error_msg)
                return company_result
            
            # 运行测试
            success = runner.run_full_test(
                pdf_path=company_folder,
                k_pages=k_pages
            )
            
            # 收集测试结果
            company_result["success"] = success
            company_result["ocr_results"] = runner.test_results.get("ocr_results", [])
            company_result["analysis_results"] = runner.test_results.get("analysis_results", {})
            company_result["errors"] = runner.test_results.get("errors", [])
            
            test_end_time = time.time()
            company_result["test_duration"] = round(test_end_time - test_start_time, 2)
            company_result["test_end_time"] = datetime.now().isoformat()
            
            if success:
                print(f"✅ 公司 {company_name} 测试成功! 耗时: {company_result['test_duration']} 秒")
            else:
                print(f"❌ 公司 {company_name} 测试失败!")
                
        except Exception as e:
            error_msg = f"公司 {company_name} 测试异常: {str(e)}"
            print(f"❌ {error_msg}")
            company_result["errors"].append(error_msg)
            test_end_time = time.time()
            company_result["test_duration"] = round(test_end_time - test_start_time, 2)
        
        return company_result
    
    def run_batch_test(self, root_path="data/档案3", k_pages=10, delay_between_tests=10):
        """
        运行批量测试
        
        Args:
            root_path (str): 档案根目录
            k_pages (int): 每K页合并为一个分析单元
            delay_between_tests (int): 测试间隔时间（秒）
            
        Returns:
            bool: 是否所有测试都成功
        """
        print("🚀 开始批量公司测试...")
        print(f"📂 档案目录: {root_path}")
        print(f"📊 分析单元: 每{k_pages}页")
        print(f"⏱️  测试间隔: {delay_between_tests}秒")
        print("-" * 80)
        
        # 查找所有公司文件夹
        company_folders = self.find_company_folders(root_path)
        
        if not company_folders:
            print("❌ 未找到任何包含PDF的公司文件夹")
            return False
        
        print(f"\n📋 找到 {len(company_folders)} 个公司文件夹，即将开始测试...")
        
        # 逐个测试公司
        all_success = True
        for i, company_folder in enumerate(company_folders, 1):
            print(f"\n📍 进度: {i}/{len(company_folders)}")
            
            # 测试单个公司
            company_result = self.test_single_company(company_folder, k_pages)
            self.batch_results["companies"].append(company_result)
            
            if not company_result["success"]:
                all_success = False
            
            # 测试间隔（除了最后一个）
            if i < len(company_folders):
                print(f"⏸️  等待 {delay_between_tests} 秒后进行下一个测试...")
                time.sleep(delay_between_tests)
        
        # 生成总结报告
        self.generate_batch_summary()
        self.save_batch_results()
        
        return all_success
    
    def generate_batch_summary(self):
        """生成批量测试总结"""
        companies = self.batch_results["companies"]
        
        if not companies:
            return
        
        successful_companies = [c for c in companies if c["success"]]
        failed_companies = [c for c in companies if not c["success"]]
        
        total_pdfs = sum(c["pdf_count"] for c in companies)
        total_duration = sum(c["test_duration"] for c in companies)
        avg_duration = total_duration / len(companies) if companies else 0
        
        self.batch_results["summary"] = {
            "total_companies": len(companies),
            "successful_companies": len(successful_companies),
            "failed_companies": len(failed_companies),
            "success_rate": round(len(successful_companies) / len(companies) * 100, 2),
            "total_pdfs": total_pdfs,
            "total_duration": round(total_duration, 2),
            "average_duration": round(avg_duration, 2),
            "fastest_company": min(companies, key=lambda x: x["test_duration"])["company_name"] if companies else None,
            "slowest_company": max(companies, key=lambda x: x["test_duration"])["company_name"] if companies else None,
            "most_pdfs_company": max(companies, key=lambda x: x["pdf_count"])["company_name"] if companies else None
        }
    
    def save_batch_results(self):
        """保存批量测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON结果
        json_filename = f"batch_company_test_{timestamp}.json"
        json_path = os.path.join(self.output_dir, json_filename)
        
        self.batch_results["test_info"]["end_time"] = datetime.now().isoformat()
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.batch_results, f, ensure_ascii=False, indent=2)
        
        # 生成可读报告
        txt_filename = f"batch_company_report_{timestamp}.txt"
        txt_path = os.path.join(self.output_dir, txt_filename)
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("批量公司测试报告\n")
            f.write("="*80 + "\n\n")
            
            # 基本信息
            test_info = self.batch_results["test_info"]
            f.write("测试信息:\n")
            f.write(f"  开始时间: {test_info['start_time']}\n")
            f.write(f"  结束时间: {test_info['end_time']}\n")
            f.write(f"  服务器地址: {test_info['base_url']}\n")
            f.write(f"  结果目录: {test_info['output_dir']}\n\n")
            
            # 总结
            summary = self.batch_results["summary"]
            f.write("测试总结:\n")
            f.write(f"  总公司数: {summary['total_companies']}\n")
            f.write(f"  成功公司数: {summary['successful_companies']}\n")
            f.write(f"  失败公司数: {summary['failed_companies']}\n")
            f.write(f"  成功率: {summary['success_rate']}%\n")
            f.write(f"  总PDF数: {summary['total_pdfs']}\n")
            f.write(f"  总耗时: {summary['total_duration']} 秒\n")
            f.write(f"  平均耗时: {summary['average_duration']} 秒\n")
            f.write(f"  最快公司: {summary['fastest_company']}\n")
            f.write(f"  最慢公司: {summary['slowest_company']}\n")
            f.write(f"  PDF最多公司: {summary['most_pdfs_company']}\n\n")
            
            # 详细结果
            f.write("详细测试结果:\n")
            f.write("-"*80 + "\n")
            
            for i, company in enumerate(self.batch_results["companies"], 1):
                f.write(f"{i}. {company['company_name']}\n")
                f.write(f"   状态: {'✅ 成功' if company['success'] else '❌ 失败'}\n")
                f.write(f"   PDF数量: {company['pdf_count']}\n")
                f.write(f"   测试耗时: {company['test_duration']} 秒\n")
                f.write(f"   分析单元: 每{company['k_pages']}页\n")
                
                if company['analysis_results']:
                    if 'stream' in company['analysis_results']:
                        stream_result = company['analysis_results']['stream']
                        f.write(f"   内容块数: {stream_result.get('chunks_count', 0)}\n")
                        if stream_result.get('word_document'):
                            f.write(f"   Word文档: {stream_result['word_document']['filename']}\n")
                
                if company['errors']:
                    f.write(f"   错误: {len(company['errors'])} 个\n")
                    for error in company['errors'][:3]:  # 只显示前3个错误
                        f.write(f"     - {error}\n")
                
                f.write(f"   文件夹: {company['folder_path']}\n")
                f.write("\n")
        
        print(f"\n📋 批量测试结果已保存:")
        print(f"  📄 JSON文件: {json_path}")
        print(f"  📊 报告文件: {txt_path}")
        
        # 输出总结
        summary = self.batch_results["summary"]
        print(f"\n🎉 批量测试完成!")
        print(f"📊 测试统计:")
        print(f"  🏢 总公司数: {summary['total_companies']}")
        print(f"  ✅ 成功: {summary['successful_companies']} 个")
        print(f"  ❌ 失败: {summary['failed_companies']} 个")
        print(f"  📈 成功率: {summary['success_rate']}%")
        print(f"  📄 总PDF: {summary['total_pdfs']} 个")
        print(f"  ⏱️  总耗时: {summary['total_duration']} 秒")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='批量公司PDF测试工具')
    parser.add_argument('--root-path', default='data/档案3', help='档案根目录（默认: data/档案3）')
    parser.add_argument('--url', default='http://localhost:5500', help='Web应用URL（默认: http://localhost:5500）')
    parser.add_argument('--output', default='company_test_results', help='输出目录（默认: company_test_results）')
    parser.add_argument('--k-pages', type=int, default=10, help='每K页合并为一个分析单元（默认: 10）')
    parser.add_argument('--delay', type=int, default=10, help='测试间隔时间秒数（默认: 10）')
    parser.add_argument('--no-delay', action='store_true', help='不设置测试间隔')
    
    args = parser.parse_args()
    
    # 检查根目录是否存在
    if not os.path.exists(args.root_path):
        print(f"❌ 根目录不存在: {args.root_path}")
        sys.exit(1)
    
    delay = 0 if args.no_delay else args.delay
    
    print("即将开始批量公司测试:")
    print(f"  📂 档案目录: {args.root_path}")
    print(f"  🌐 服务器URL: {args.url}")
    print(f"  📊 分析单元: 每{args.k_pages}页")
    print(f"  ⏱️  测试间隔: {delay}秒")
    print(f"  📁 输出目录: {args.output}")
    
    # 确认继续
    try:
        confirm = input("\n是否继续进行批量测试? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("测试已取消")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n测试已取消")
        sys.exit(0)
    
    # 创建批量测试器
    tester = CompanyBatchTester(base_url=args.url, output_dir=args.output)
    
    # 运行批量测试
    success = tester.run_batch_test(
        root_path=args.root_path,
        k_pages=args.k_pages,
        delay_between_tests=delay
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
