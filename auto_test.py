#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试脚本
用于批量测试PDF文件的OCR识别和工作流分析
"""

import os
import glob
import json
import time
import requests
import shutil
from datetime import datetime
from pathlib import Path
import argparse
import sys

class AutoTestRunner:
    """自动化测试运行器"""
    
    def __init__(self, base_url="http://localhost:5000", output_dir="test_results"):
        """
        初始化测试运行器
        
        Args:
            base_url (str): Web应用的基础URL
            output_dir (str): 测试结果输出目录
        """
        self.base_url = base_url
        self.output_dir = output_dir
        self.session = requests.Session()
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 测试结果存储
        self.test_results = {
            "test_info": {
                "start_time": datetime.now().isoformat(),
                "base_url": base_url,
                "output_dir": output_dir
            },
            "pdf_files": [],
            "ocr_results": {},
            "analysis_results": {},
            "errors": [],
            "summary": {}
        }
    
    def find_pdf_files(self, pdf_path):
        """
        查找指定路径下的所有PDF文件
        
        Args:
            pdf_path (str): PDF文件路径，可以是文件夹或单个文件
            
        Returns:
            list: PDF文件路径列表
        """
        pdf_files = []
        
        if os.path.isfile(pdf_path):
            if pdf_path.lower().endswith('.pdf'):
                pdf_files.append(pdf_path)
        elif os.path.isdir(pdf_path):
            # 递归查找所有PDF文件
            pattern = os.path.join(pdf_path, "**", "*.pdf")
            pdf_files = glob.glob(pattern, recursive=True)
        
        print(f"找到 {len(pdf_files)} 个PDF文件")
        for pdf_file in pdf_files:
            print(f"  - {pdf_file}")
        
        return pdf_files
    
    def check_server_status(self):
        """检查服务器状态"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                print("✅ 服务器连接正常")
                return True
            else:
                print(f"❌ 服务器响应异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 无法连接到服务器: {e}")
            return False
    
    def upload_pdf_files(self, pdf_files):
        """
        上传PDF文件到服务器（支持分批上传）
        
        Args:
            pdf_files (list): PDF文件路径列表
            
        Returns:
            str: 任务ID，如果失败返回None
        """
        # 检查文件大小并决定是否分批上传
        total_size = sum(os.path.getsize(f) for f in pdf_files)
        max_size = 80 * 1024 * 1024  # 80MB，留一些余量
        
        print(f"📊 文件总大小: {total_size / 1024 / 1024:.2f} MB")
        
        # if total_size > max_size:
        #     print(f"⚠️  文件总大小超过限制，将进行分批上传...")
        #     return self._upload_files_in_batches(pdf_files, max_size)
        # else:
        #     return self._upload_files_single_batch(pdf_files)
        return self._upload_files_single_batch(pdf_files)
    
    def _upload_files_single_batch(self, pdf_files):
        """单批上传文件"""
        try:
            files = []
            for pdf_file in pdf_files:
                files.append(('files', (os.path.basename(pdf_file), open(pdf_file, 'rb'), 'application/pdf')))
            
            print(f"📤 开始上传 {len(pdf_files)} 个PDF文件...")
            response = self.session.post(f"{self.base_url}/upload", files=files)
            
            # 关闭文件句柄
            for _, (_, file_obj, _) in files:
                file_obj.close()
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                print(f"✅ 文件上传成功，任务ID: {task_id}")
                
                # 记录上传的文件信息
                self.test_results["pdf_files"] = [os.path.basename(f) for f in pdf_files]
                self.test_results["task_id"] = task_id
                
                return task_id
            else:
                error_msg = f"上传失败: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                self.test_results["errors"].append(error_msg)
                return None
                
        except Exception as e:
            error_msg = f"上传异常: {str(e)}"
            print(f"❌ {error_msg}")
            self.test_results["errors"].append(error_msg)
            return None
    
    def _upload_files_in_batches(self, pdf_files, max_batch_size):
        """分批上传文件"""
        # 按文件大小分组
        batches = []
        current_batch = []
        current_size = 0
        
        for pdf_file in pdf_files:
            file_size = os.path.getsize(pdf_file)
            
            # 如果单个文件就超过限制，跳过
            if file_size > max_batch_size:
                print(f"⚠️  文件 {os.path.basename(pdf_file)} 太大({file_size/1024/1024:.2f}MB)，跳过")
                continue
            
            # 如果添加这个文件会超过批次限制，开始新批次
            if current_size + file_size > max_batch_size and current_batch:
                batches.append(current_batch)
                current_batch = []
                current_size = 0
            
            current_batch.append(pdf_file)
            current_size += file_size
        
        # 添加最后一个批次
        if current_batch:
            batches.append(current_batch)
        
        print(f"📦 将分 {len(batches)} 批上传")
        
        # 逐批上传
        all_task_ids = []
        for i, batch in enumerate(batches, 1):
            print(f"\n🔄 第 {i}/{len(batches)} 批 - {len(batch)} 个文件")
            task_id = self._upload_files_single_batch(batch)
            if task_id:
                all_task_ids.append(task_id)
                # 等待这批处理完成再上传下一批
                if i < len(batches):
                    print("⏳ 等待当前批次处理完成...")
                    ocr_results = self.wait_for_ocr_completion(task_id)
                    if not ocr_results:
                        print(f"❌ 第 {i} 批处理失败")
                        return None
            else:
                print(f"❌ 第 {i} 批上传失败")
                return None
        
        # 返回最后一个task_id（用于最终分析）
        return all_task_ids[-1] if all_task_ids else None
    
    def wait_for_ocr_completion(self, task_id, timeout=3600):
        """
        等待OCR处理完成
        
        Args:
            task_id (str): 任务ID
            timeout (int): 超时时间（秒）
            
        Returns:
            dict: OCR结果，如果失败返回None
        """
        print("⏳ 等待OCR处理完成...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(f"{self.base_url}/status/{task_id}")
                
                if response.status_code == 200:
                    status = response.json()
                    
                    if status.get('status') == 'processing':
                        progress = status.get('progress', 0)
                        total = status.get('total', 0)
                        print(f"📋 处理进度: {progress}/{total}")
                        
                    elif status.get('status') == 'completed':
                        print("✅ OCR处理完成")
                        ocr_results = status.get('results', [])
                        self.test_results["ocr_results"] = ocr_results
                        return ocr_results
                        
                    elif status.get('status') == 'error':
                        error_msg = f"OCR处理失败: {status.get('error', '未知错误')}"
                        print(f"❌ {error_msg}")
                        self.test_results["errors"].append(error_msg)
                        return None
                
                time.sleep(5)  # 等待5秒后重新检查
                
            except Exception as e:
                error_msg = f"检查状态异常: {str(e)}"
                print(f"❌ {error_msg}")
                self.test_results["errors"].append(error_msg)
                time.sleep(5)
        
        error_msg = f"OCR处理超时（{timeout}秒）"
        print(f"❌ {error_msg}")
        self.test_results["errors"].append(error_msg)
        return None
    
    def run_analysis(self, task_id, k_pages=5):
        """
        运行AI分析
        
        Args:
            task_id (str): 任务ID
            k_pages (int): 每K页合并为一个分析单元
            
        Returns:
            dict: 分析结果
        """
        try:
            print(f"🤖 开始AI分析（每{k_pages}页为一个单元）...")
            
            data = {
                "task_id": task_id,
                "k_pages": k_pages
            }
            
            response = self.session.post(
                f"{self.base_url}/analyze",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ AI分析完成")
                
                analysis_result = {
                    "k_pages": k_pages,
                    "chunks_count": result.get('chunks_count', 0),
                    "analysis_content": result.get('analysis_result', ''),
                    "word_document": result.get('word_document', None),
                    "timestamp": datetime.now().isoformat()
                }
                
                self.test_results["analysis_results"]["standard"] = analysis_result
                return analysis_result
                
            else:
                error_msg = f"AI分析失败: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                self.test_results["errors"].append(error_msg)
                return None
                
        except Exception as e:
            error_msg = f"AI分析异常: {str(e)}"
            print(f"❌ {error_msg}")
            self.test_results["errors"].append(error_msg)
            return None
    
    def run_stream_analysis(self, task_id, k_pages=5):
        """
        运行流式AI分析
        
        Args:
            task_id (str): 任务ID
            k_pages (int): 每K页合并为一个分析单元
            
        Returns:
            dict: 流式分析结果
        """
        try:
            print(f"🚀 开始流式AI分析（每{k_pages}页为一个单元）...")
            
            data = {
                "task_id": task_id,
                "k_pages": k_pages
            }
            
            response = self.session.post(
                f"{self.base_url}/analyze_stream",
                json=data,
                headers={'Content-Type': 'application/json'},
                stream=True
            )
            
            if response.status_code == 200:
                stream_content = []
                chunks_count = 0
                word_document = None
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                data_chunk = json.loads(line_str[6:])
                                
                                if data_chunk.get('type') == 'init':
                                    chunks_count = data_chunk.get('chunks_count', 0)
                                    print(f"📊 流式分析开始，共{chunks_count}个内容块")
                                    
                                elif data_chunk.get('type') == 'content':
                                    content = data_chunk.get('data', '')
                                    stream_content.append(content)
                                    print(".", end="", flush=True)
                                    
                                elif data_chunk.get('type') == 'word_generated':
                                    word_document = {
                                        'filename': data_chunk.get('filename'),
                                        'download_url': data_chunk.get('download_url')
                                    }
                                    print(f"\n📄 Word文档已生成: {word_document['filename']}")
                                    
                                elif data_chunk.get('type') == 'done':
                                    print("\n✅ 流式分析完成")
                                    
                                elif data_chunk.get('type') == 'error':
                                    error_msg = f"流式分析失败: {data_chunk.get('error')}"
                                    print(f"\n❌ {error_msg}")
                                    self.test_results["errors"].append(error_msg)
                                    return None
                                    
                            except json.JSONDecodeError:
                                continue
                
                stream_result = {
                    "k_pages": k_pages,
                    "chunks_count": chunks_count,
                    "stream_content": ''.join(stream_content),
                    "word_document": word_document,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.test_results["analysis_results"]["stream"] = stream_result
                return stream_result
                
            else:
                error_msg = f"流式分析失败: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                self.test_results["errors"].append(error_msg)
                return None
                
        except Exception as e:
            error_msg = f"流式分析异常: {str(e)}"
            print(f"❌ {error_msg}")
            self.test_results["errors"].append(error_msg)
            return None
    
    def save_results(self, filename_prefix="auto_test"):
        """
        保存测试结果到文件
        
        Args:
            filename_prefix (str): 文件名前缀
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 添加测试总结
        self.test_results["test_info"]["end_time"] = datetime.now().isoformat()
        self.test_results["summary"] = {
            "total_pdfs": len(self.test_results["pdf_files"]),
            "ocr_success": len(self.test_results["ocr_results"]),
            "analysis_completed": len(self.test_results["analysis_results"]),
            "total_errors": len(self.test_results["errors"])
        }
        
        # 保存JSON结果
        json_filename = f"{filename_prefix}_{timestamp}.json"
        json_path = os.path.join(self.output_dir, json_filename)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"📋 测试结果已保存到: {json_path}")
        
        # 保存可读的文本报告
        txt_filename = f"{filename_prefix}_{timestamp}_report.txt"
        txt_path = os.path.join(self.output_dir, txt_filename)
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("自动化测试报告\n")
            f.write("="*80 + "\n\n")
            
            # 基本信息
            f.write("测试信息:\n")
            f.write(f"  开始时间: {self.test_results['test_info']['start_time']}\n")
            f.write(f"  结束时间: {self.test_results['test_info']['end_time']}\n")
            f.write(f"  服务器地址: {self.test_results['test_info']['base_url']}\n")
            f.write(f"  结果目录: {self.test_results['test_info']['output_dir']}\n\n")
            
            # 测试总结
            summary = self.test_results["summary"]
            f.write("测试总结:\n")
            f.write(f"  PDF文件总数: {summary['total_pdfs']}\n")
            f.write(f"  OCR成功数量: {summary['ocr_success']}\n")
            f.write(f"  分析完成数量: {summary['analysis_completed']}\n")
            f.write(f"  错误总数: {summary['total_errors']}\n\n")
            
            # PDF文件列表
            f.write("处理的PDF文件:\n")
            for pdf_file in self.test_results["pdf_files"]:
                f.write(f"  - {pdf_file}\n")
            f.write("\n")
            
            # OCR结果
            if self.test_results["ocr_results"]:
                f.write("OCR识别结果:\n")
                for result in self.test_results["ocr_results"]:
                    f.write(f"  文件: {result.get('filename', 'Unknown')}\n")
                    if 'error' in result:
                        f.write(f"    错误: {result['error']}\n")
                    else:
                        pages = result.get('pages', [])
                        f.write(f"    识别页数: {len(pages)}\n")
                        f.write(f"    时间戳: {result.get('timestamp', 'Unknown')}\n")
                f.write("\n")
            
            # 分析结果
            if self.test_results["analysis_results"]:
                f.write("AI分析结果:\n")
                
                # 标准分析
                if "standard" in self.test_results["analysis_results"]:
                    std_result = self.test_results["analysis_results"]["standard"]
                    f.write("  标准分析:\n")
                    f.write(f"    分析单元: 每{std_result['k_pages']}页\n")
                    f.write(f"    内容块数: {std_result['chunks_count']}\n")
                    f.write(f"    分析时间: {std_result['timestamp']}\n")
                    if std_result.get('word_document'):
                        f.write(f"    Word文档: {std_result['word_document']['filename']}\n")
                    f.write("\n")
                
                # 流式分析
                if "stream" in self.test_results["analysis_results"]:
                    stream_result = self.test_results["analysis_results"]["stream"]
                    f.write("  流式分析:\n")
                    f.write(f"    分析单元: 每{stream_result['k_pages']}页\n")
                    f.write(f"    内容块数: {stream_result['chunks_count']}\n")
                    f.write(f"    分析时间: {stream_result['timestamp']}\n")
                    if stream_result.get('word_document'):
                        f.write(f"    Word文档: {stream_result['word_document']['filename']}\n")
                    f.write("\n")
            
            # 错误信息
            if self.test_results["errors"]:
                f.write("错误记录:\n")
                for i, error in enumerate(self.test_results["errors"], 1):
                    f.write(f"  {i}. {error}\n")
                f.write("\n")
            
            # 分析内容（如果有的话）
            if self.test_results["analysis_results"]:
                f.write("\n" + "="*80 + "\n")
                f.write("详细分析内容\n")
                f.write("="*80 + "\n\n")
                
                if "standard" in self.test_results["analysis_results"]:
                    f.write("标准分析内容:\n")
                    f.write("-"*60 + "\n")
                    f.write(self.test_results["analysis_results"]["standard"]["analysis_content"])
                    f.write("\n\n")
                
                if "stream" in self.test_results["analysis_results"]:
                    f.write("流式分析内容:\n")
                    f.write("-"*60 + "\n")
                    f.write(self.test_results["analysis_results"]["stream"]["stream_content"])
                    f.write("\n\n")
        
        print(f"📄 测试报告已保存到: {txt_path}")
        
        return json_path, txt_path
    
    def run_full_test(self, pdf_path, k_pages=5):
        """
        运行完整的自动化测试
        
        Args:
            pdf_path (str): PDF文件路径
            k_pages (int): 每K页合并为一个分析单元
            
        Returns:
            bool: 测试是否成功
        """
        print("🚀 开始自动化测试...")
        print(f"📂 PDF路径: {pdf_path}")
        print(f"📊 分析单元: 每{k_pages}页")
        print("-" * 80)
        
        # 1. 检查服务器状态
        if not self.check_server_status():
            return False
        
        # 2. 查找PDF文件
        pdf_files = self.find_pdf_files(pdf_path)
        if not pdf_files:
            print("❌ 未找到PDF文件")
            return False
        
        # 3. 上传PDF文件
        task_id = self.upload_pdf_files(pdf_files)
        if not task_id:
            return False
        
        # 4. 等待OCR完成
        ocr_results = self.wait_for_ocr_completion(task_id)
        if not ocr_results:
            return False
        
        # 5. 运行AI分析
        analysis_success = False
        
        # # 标准分析
        # print("\n" + "="*50)
        # analysis_result = self.run_analysis(task_id, k_pages)
        # if analysis_result:
        #     analysis_success = True
        
        print("\n" + "="*50)
        stream_result = self.run_stream_analysis(task_id, k_pages)
        if stream_result:
            analysis_success = True
        
        # 6. 保存结果
        print("\n" + "="*50)
        json_path, txt_path = self.save_results()
        
        # 输出最终总结
        print("\n" + "="*80)
        print("🎉 自动化测试完成!")
        print(f"📋 处理PDF: {len(pdf_files)} 个")
        print(f"✅ OCR成功: {len(ocr_results)} 个")
        print(f"🤖 分析完成: {len(self.test_results['analysis_results'])} 个")
        print(f"❌ 错误数量: {len(self.test_results['errors'])} 个")
        print(f"📄 结果文件: {json_path}")
        print(f"📊 测试报告: {txt_path}")
        
        return analysis_success


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PDF自动化测试工具')
    parser.add_argument('--pdf_path', default = "data/档案3/杭州全顺纺织有限公司  1", help='PDF文件路径（文件或文件夹）')
    parser.add_argument('--url', default='http://localhost:5500', help='Web应用URL（默认: http://localhost:5000）')
    parser.add_argument('--output', default='test_results', help='输出目录（默认: test_results）')
    parser.add_argument('--k-pages', type=int, default=30, help='每K页合并为一个分析单元（默认: 25）')

    args = parser.parse_args()
    # 检查PDF路径是否存在
    if not os.path.exists(args.pdf_path):
        print(f"❌ 路径不存在: {args.pdf_path}")
        sys.exit(1)
    
    # 创建测试运行器
    runner = AutoTestRunner(base_url=args.url, output_dir=args.output)
    
    # 运行测试
    success = runner.run_full_test(
        pdf_path=args.pdf_path,
        k_pages=args.k_pages,
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
