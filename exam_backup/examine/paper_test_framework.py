#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文数据测试框架
用于执行论文所需的各种测试任务
"""

import os
import sys
import json
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple
import numpy as np

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model_handler import ModelHandler
from src.novel_generator import NovelGenerator
from src.utils import load_config

# BERT相关导入
try:
    from transformers import BertTokenizer, BertModel
    import torch
    BERT_AVAILABLE = True
except ImportError:
    BERT_AVAILABLE = False
    print("警告: 未安装BERT相关库，连贯性评估功能将不可用")

class PaperTestFramework:
    def __init__(self):
        """初始化测试框架"""
        self.config = load_config()
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'generation_tests': {},
            'coherence_tests': {},
            'quality_tests': {},
            'comparison_tests': {},
            'additional_tests': {},
            'novelcreator_comparison_tests': {}
        }
        
        # 初始化BERT模型（如果可用）
        self.bert_tokenizer = None
        self.bert_model = None
        if BERT_AVAILABLE:
            try:
                # 使用中文BERT模型
                # 增加重试机制
                for attempt in range(3):
                    try:
                        self.bert_tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
                        self.bert_model = BertModel.from_pretrained('bert-base-chinese')
                        self.bert_model.eval()
                        print("BERT模型加载成功")
                        break
                    except Exception as e:
                        print(f"BERT模型加载失败 (尝试 {attempt + 1}/3): {e}")
                        if attempt < 2:
                            import time
                            time.sleep(2 ** attempt)  # 指数退避
                        else:
                            raise
            except Exception as e:
                print(f"BERT模型加载最终失败: {e}")
        
    def run_all_tests(self):
        """运行所有测试"""
        print("开始执行论文数据测试...")
        print("=" * 60)
        
        # 1. 运行生成测试
        self.run_generation_tests()
        
        # 2. 运行质量评分测试
        self.run_quality_tests()
        
        # 3. 运行连贯性测试
        self.run_coherence_tests()
        
        # 4. 运行对比测试
        self.run_comparison_tests()
        
        # 5. 运行其他测定项目
        self.run_additional_tests()
        
        # 6. 运行novelcreator工具与简单提示词生成小说对比测试
        self.run_novelcreator_comparison_tests()
        
        # 7. 生成报告
        self.generate_report()
        
        return self.test_results
    
    def run_generation_tests(self):
        """运行生成测试"""
        print("\n1. 执行生成测试...")
        try:
            # 定义测试模型列表
            test_models = [
                "moonshotai/kimi-k2:free",
                "deepseek/deepseek-chat-v3.1:free",
                "deepseek/deepseek-r1-0528:free",
                "qwen/qwen3-14b:free"
            ]
            
            # 存储测试结果
            generation_results = {}
            
            # 为每个模型执行生成测试
            for model_name in test_models:
                print(f"\n  测试模型: {model_name}")
                
                # 创建模型处理器
                handler = ModelHandler()
                
                # 设置API密钥和端点
                handler._model_cache["openai"] = {
                    "api_key": "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",
                    "base_url": "https://openrouter.ai/api/v1",
                    "model": model_name
                }
                
                # 准备测试提示
                test_prompt = "请写一个关于未来科技的短篇科幻故事，字数在1000字左右。"
                
                # 记录开始时间
                start_time = time.time()
                
                # 生成文本
                try:
                    generated_text = handler.generate_text(test_prompt, model_type="openai")
                    end_time = time.time()
                    
                    # 计算生成时间和其他指标
                    generation_time = end_time - start_time
                    text_length = len(generated_text)
                    chars_per_second = text_length / generation_time if generation_time > 0 else 0
                    
                    generation_results[model_name] = {
                        'generation_time': generation_time,
                        'text_length': text_length,
                        'chars_per_second': chars_per_second,
                        'status': 'success'
                    }
                    
                    print(f"    生成时间: {generation_time:.2f} 秒")
                    print(f"    文本长度: {text_length} 字符")
                    print(f"    生成速度: {chars_per_second:.2f} 字符/秒")
                    
                except Exception as e:
                    end_time = time.time()
                    generation_time = end_time - start_time
                    
                    generation_results[model_name] = {
                        'generation_time': generation_time,
                        'error': str(e),
                        'status': 'failed'
                    }
                    print(f"    测试失败: {e}")
            
            self.test_results['generation_tests'] = {
                'status': 'completed',
                'results': generation_results
            }
            print("✓ 生成测试完成")
        except Exception as e:
            print(f"✗ 生成测试失败: {e}")
            self.test_results['generation_tests'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    
    def run_quality_tests(self):
        """运行质量评分测试"""
        print("\n3. 执行质量评分测试...")
        try:
            # 定义评分模型列表
            scoring_models = [
                "moonshotai/kimi-k2:free",
                "deepseek/deepseek-r1-0528:free"
            ]
            
            # 存储测试结果
            quality_results = {}
            
            # 准备测试文本
            test_text = "今天天气很好。阳光明媚，鸟语花香。我决定去公园散步。公园里有很多人在锻炼身体。我也加入了他们，感觉非常愉快。这是一个美好的一天。"
            
            # 为每个模型执行质量评分测试
            for model_name in scoring_models:
                print(f"\n  使用模型 {model_name} 进行评分...")
                
                # 创建模型处理器
                handler = ModelHandler()
                
                # 设置API密钥和端点
                handler._model_cache["openai"] = {
                    "api_key": "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",
                    "base_url": "https://openrouter.ai/api/v1",
                    "model": model_name
                }
                
                # 进行5次评分
                scores = []
                for i in range(5):
                    try:
                        # 构造评分提示
                        prompt = f"""你是一位专业的文本质量评估专家。请对以下文本进行质量评分，满分5分。

文本内容：
{test_text}

评分标准：
1. 内容质量（逻辑性、连贯性）
2. 语言表达（流畅性、准确性）
3. 创意性（新颖性、吸引力）
4. 情感表达（感染力、共鸣性）

请直接给出一个1-5之间的分数，不需要解释。

分数：
"""
                        
                        # 获取评分
                        response = handler.generate_text(prompt, model_type="openai", temperature=0.7)
                        
                        # 提取分数
                        score = self.extract_score_from_response(response)
                        if score is not None:
                            scores.append(score)
                            print(f"    第{i+1}次评分: {score}分")
                        else:
                            print(f"    第{i+1}次评分: 无法提取分数")
                    
                    except Exception as e:
                        print(f"    第{i+1}次评分失败: {e}")
                
                # 计算平均分
                if scores:
                    avg_score = np.mean(scores)
                    print(f"    平均分: {avg_score:.2f}分")
                    
                    quality_results[model_name] = {
                        'scores': scores,
                        'average_score': float(avg_score),
                        'status': 'success'
                    }
                else:
                    quality_results[model_name] = {
                        'scores': [],
                        'average_score': 0.0,
                        'status': 'failed'
                    }
            
            self.test_results['quality_tests'] = {
                'status': 'completed',
                'results': quality_results,
                'test_text': test_text
            }
            print("✓ 质量评分测试完成")
        except Exception as e:
            print(f"✗ 质量评分测试失败: {e}")
            self.test_results['quality_tests'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def extract_score_from_response(self, response: str) -> float:
        """从响应中提取分数"""
        try:
            # 使用正则表达式提取数字
            numbers = re.findall(r'\d+\.?\d*', response)
            if numbers:
                score = float(numbers[0])
                # 确保分数在1-5之间
                if 1 <= score <= 5:
                    return score
            return None
        except Exception:
            return None
    
    def run_comparison_tests(self):
        """运行对比测试"""
        print("\n4. 执行对比测试...")
        try:
            # 存储测试结果
            comparison_results = {
                'with_reader': {},
                'without_reader': {}
            }
            
            # 准备测试小说标题和章节数
            test_title = "未来科技的短篇科幻故事"
            test_chapters = 1
            
            # 1. 测试有读者评分系统的生成效果
            print("\n  测试有读者评分系统的生成效果...")
            
            # 创建带有读者评分系统的小说生成器
            handler_with_reader = ModelHandler()
            
            # 设置API密钥和端点
            handler_with_reader._model_cache["openai"] = {
                "api_key": "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",
                "base_url": "https://openrouter.ai/api/v1",
                "model": "deepseek/deepseek-r1-0528:free"
            }
            
            # 创建启用读者评分系统的小说生成器
            generator_with_reader = NovelGenerator(handler_with_reader, model_type="openai")
            
            # 记录开始时间
            start_time = time.time()
            
            # 生成小说（使用读者评分系统）
            try:
                # 生成大纲
                outline_with_reader = generator_with_reader._generate_outline(test_title, test_chapters)
                
                # 生成章节
                chapter_content_with_reader = generator_with_reader._generate_chapter_structured(test_title, 1, outline_with_reader)
                
                end_time = time.time()
                
                # 计算生成时间和其他指标
                generation_time_with_reader = end_time - start_time
                text_length_with_reader = len(chapter_content_with_reader)
                chars_per_second_with_reader = text_length_with_reader / generation_time_with_reader if generation_time_with_reader > 0 else 0
                
                # 评估文本质量
                coherence_metrics = self.calculate_text_coherence(chapter_content_with_reader)
                
                # 进行人工评分
                quality_scores = []
                for i in range(5):  # 进行5次评分以提高准确性
                    score = self.get_manual_score(chapter_content_with_reader)
                    if score is not None:
                        quality_scores.append(score)
                
                avg_quality_score = np.mean(quality_scores) if quality_scores else 0.0
                
                comparison_results['with_reader'] = {
                    'generation_time': generation_time_with_reader,
                    'text_length': text_length_with_reader,
                    'chars_per_second': chars_per_second_with_reader,
                    'coherence_metrics': coherence_metrics,
                    'quality_scores': quality_scores,
                    'average_quality_score': float(avg_quality_score),
                    'status': 'success'
                }
                
                print(f"    生成时间: {generation_time_with_reader:.2f} 秒")
                print(f"    文本长度: {text_length_with_reader} 字符")
                print(f"    生成速度: {chars_per_second_with_reader:.2f} 字符/秒")
                print(f"    平均质量评分: {avg_quality_score:.2f} 分")
                
            except Exception as e:
                end_time = time.time()
                generation_time_with_reader = end_time - start_time
                
                comparison_results['with_reader'] = {
                    'generation_time': generation_time_with_reader,
                    'error': str(e),
                    'status': 'failed'
                }
                print(f"    测试失败: {e}")
            
            # 2. 测试无读者评分系统的生成效果
            print("\n  测试无读者评分系统的生成效果...")
            
            # 创建不带读者评分系统的模型处理器
            handler_without_reader = ModelHandler()
            
            # 设置API密钥和端点
            handler_without_reader._model_cache["openai"] = {
                "api_key": "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",
                "base_url": "https://openrouter.ai/api/v1",
                "model": "deepseek/deepseek-r1-0528:free"
            }
            
            # 创建禁用读者评分系统的小说生成器
            # 首先创建一个启用读者评分系统的生成器
            generator_without_reader = NovelGenerator(handler_without_reader, model_type="openai")
            # 然后禁用读者评分系统
            generator_without_reader.reader_enabled = False
            
            # 记录开始时间
            start_time = time.time()
            
            # 生成小说（不使用读者评分系统）
            try:
                # 生成大纲
                outline_without_reader = generator_without_reader._generate_outline(test_title, test_chapters)
                
                # 生成章节
                chapter_content_without_reader = generator_without_reader._generate_chapter_structured(test_title, 1, outline_without_reader)
                
                end_time = time.time()
                
                # 计算生成时间和其他指标
                generation_time_without_reader = end_time - start_time
                text_length_without_reader = len(chapter_content_without_reader)
                chars_per_second_without_reader = text_length_without_reader / generation_time_without_reader if generation_time_without_reader > 0 else 0
                
                # 评估文本质量
                coherence_metrics = self.calculate_text_coherence(chapter_content_without_reader)
                
                # 进行人工评分
                quality_scores = []
                for i in range(5):  # 进行5次评分以提高准确性
                    score = self.get_manual_score(chapter_content_without_reader)
                    if score is not None:
                        quality_scores.append(score)
                
                avg_quality_score = np.mean(quality_scores) if quality_scores else 0.0
                
                comparison_results['without_reader'] = {
                    'generation_time': generation_time_without_reader,
                    'text_length': text_length_without_reader,
                    'chars_per_second': chars_per_second_without_reader,
                    'coherence_metrics': coherence_metrics,
                    'quality_scores': quality_scores,
                    'average_quality_score': float(avg_quality_score),
                    'status': 'success'
                }
                
                print(f"    生成时间: {generation_time_without_reader:.2f} 秒")
                print(f"    文本长度: {text_length_without_reader} 字符")
                print(f"    生成速度: {chars_per_second_without_reader:.2f} 字符/秒")
                print(f"    平均质量评分: {avg_quality_score:.2f} 分")
                
            except Exception as e:
                end_time = time.time()
                generation_time_without_reader = end_time - start_time
                
                comparison_results['without_reader'] = {
                    'generation_time': generation_time_without_reader,
                    'error': str(e),
                    'status': 'failed'
                }
                print(f"    测试失败: {e}")
            
            self.test_results['comparison_tests'] = {
                'status': 'completed',
                'results': comparison_results
            }
            print("✓ 对比测试完成")
        except Exception as e:
            print(f"✗ 对比测试失败: {e}")
            self.test_results['comparison_tests'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def get_manual_score(self, text: str) -> float:
        """获取人工评分（模拟）"""
        try:
            # 在实际应用中，这里会调用人工评分或使用预训练的评分模型
            # 为了简化，我们使用一个基于文本特征的简单评分算法
            
            # 文本长度评分（1000-2000字符为最佳）
            length_score = min(5.0, max(1.0, len(text) / 1000))
            
            # 句子数量评分（10-20句为最佳）
            sentence_count = len(re.split(r'[。！？.!?]', text))
            sentence_score = min(5.0, max(1.0, sentence_count / 2))
            
            # 词汇丰富度评分（基于唯一词比例）
            words = re.findall(r'[\w]+', text)
            unique_words = set(words)
            vocabulary_score = min(5.0, max(1.0, len(unique_words) / len(words) * 10)) if words else 1.0
            
            # 综合评分
            avg_score = (length_score + sentence_score + vocabulary_score) / 3
            
            return avg_score
        except Exception:
            return 3.0  # 默认评分
    
    def run_additional_tests(self):
        """运行其他测定项目"""
        print("\n5. 执行其他测定项目...")
        try:
            # 准备测试文本
            test_text = "今天天气很好。阳光明媚，鸟语花香。我决定去公园散步。公园里有很多人在锻炼身体。我也加入了他们，感觉非常愉快。这是一个美好的一天。科技的发展日新月异，人工智能技术正在改变我们的生活。未来的世界将更加智能化和便捷化。"
            
            # 计算各种文本指标
            additional_metrics = {
                'vocabulary_richness': self.calculate_vocabulary_richness(test_text),
                'sentence_complexity': self.calculate_sentence_complexity(test_text),
                'pos_distribution': self.calculate_pos_distribution(test_text),
                'readability_score': self.calculate_readability_score(test_text)
            }
            
            self.test_results['additional_tests'] = {
                'status': 'completed',
                'results': additional_metrics,
                'test_text': test_text
            }
            print("✓ 其他测定项目完成")
        except Exception as e:
            print(f"✗ 其他测定项目失败: {e}")
            self.test_results['additional_tests'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def run_novelcreator_comparison_tests(self):
        """运行novelcreator工具与简单提示词生成小说对比测试"""
        print("\n6. 执行novelcreator工具与简单提示词生成小说对比测试...")
        try:
            # 存储测试结果
            comparison_results = {
                'novelcreator': {},
                'simple_prompt': {}
            }
            
            # 1. 使用novelcreator工具生成小说
            print("\n  使用novelcreator工具生成小说...")
            
            # 创建模型处理器
            handler = ModelHandler()
            
            # 设置API密钥和端点
            handler._model_cache["openai"] = {
                "api_key": "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",
                "base_url": "https://openrouter.ai/api/v1",
                "model": "deepseek/deepseek-r1-0528:free"
            }
            
            # 创建小说生成器
            generator = NovelGenerator(handler, model_type="openai")
            
            # 记录开始时间
            start_time = time.time()
            
            # 生成小说大纲
            try:
                outline = generator._generate_outline("测试小说", 3)
                end_time = time.time()
                
                # 计算生成时间
                generation_time = end_time - start_time
                
                # 生成章节
                start_time_chapter = time.time()
                chapter_content = generator._generate_chapter_structured("测试小说", 1, outline)
                end_time_chapter = time.time()
                
                # 计算章节生成时间
                chapter_generation_time = end_time_chapter - start_time_chapter
                total_time = generation_time + chapter_generation_time
                
                # 评估文本质量
                coherence_metrics = self.calculate_text_coherence(chapter_content)
                
                # 进行人工评分
                quality_scores = []
                for i in range(3):  # 进行3次评分
                    score = self.get_manual_score(chapter_content)
                    if score is not None:
                        quality_scores.append(score)
                
                avg_quality_score = np.mean(quality_scores) if quality_scores else 0.0
                
                comparison_results['novelcreator'] = {
                    'outline_generation_time': generation_time,
                    'chapter_generation_time': chapter_generation_time,
                    'total_time': total_time,
                    'text_length': len(chapter_content),
                    'coherence_metrics': coherence_metrics,
                    'quality_scores': quality_scores,
                    'average_quality_score': float(avg_quality_score),
                    'status': 'success'
                }
                
                print(f"    大纲生成时间: {generation_time:.2f} 秒")
                print(f"    章节生成时间: {chapter_generation_time:.2f} 秒")
                print(f"    总时间: {total_time:.2f} 秒")
                print(f"    文本长度: {len(chapter_content)} 字符")
                print(f"    平均质量评分: {avg_quality_score:.2f} 分")
                
            except Exception as e:
                end_time = time.time()
                generation_time = end_time - start_time
                
                comparison_results['novelcreator'] = {
                    'generation_time': generation_time,
                    'error': str(e),
                    'status': 'failed'
                }
                print(f"    测试失败: {e}")
            
            # 2. 使用简单提示词生成小说
            print("\n  使用简单提示词生成小说...")
            
            # 记录开始时间
            start_time = time.time()
            
            # 生成文本（使用简单提示词）
            try:
                simple_prompt = "请写一个关于未来科技的短篇科幻故事，字数在1000字左右。"
                generated_text_simple = handler.generate_text(simple_prompt, model_type="openai")
                end_time = time.time()
                
                # 计算生成时间
                generation_time_simple = end_time - start_time
                
                # 评估文本质量
                coherence_metrics_simple = self.calculate_text_coherence(generated_text_simple)
                
                # 进行人工评分
                quality_scores_simple = []
                for i in range(3):  # 进行3次评分
                    score = self.get_manual_score(generated_text_simple)
                    if score is not None:
                        quality_scores_simple.append(score)
                
                avg_quality_score_simple = np.mean(quality_scores_simple) if quality_scores_simple else 0.0
                
                comparison_results['simple_prompt'] = {
                    'generation_time': generation_time_simple,
                    'text_length': len(generated_text_simple),
                    'coherence_metrics': coherence_metrics_simple,
                    'quality_scores': quality_scores_simple,
                    'average_quality_score': float(avg_quality_score_simple),
                    'status': 'success'
                }
                
                print(f"    生成时间: {generation_time_simple:.2f} 秒")
                print(f"    文本长度: {len(generated_text_simple)} 字符")
                print(f"    平均质量评分: {avg_quality_score_simple:.2f} 分")
                
            except Exception as e:
                end_time = time.time()
                generation_time_simple = end_time - start_time
                
                comparison_results['simple_prompt'] = {
                    'generation_time': generation_time_simple,
                    'error': str(e),
                    'status': 'failed'
                }
                print(f"    测试失败: {e}")
            
            self.test_results['novelcreator_comparison_tests'] = {
                'status': 'completed',
                'results': comparison_results
            }
            print("✓ novelcreator工具与简单提示词生成小说对比测试完成")
        except Exception as e:
            print(f"✗ novelcreator工具与简单提示词生成小说对比测试失败: {e}")
            self.test_results['novelcreator_comparison_tests'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def calculate_vocabulary_richness(self, text: str) -> Dict[str, float]:
        """计算词汇丰富度"""
        try:
            # 提取词汇
            words = re.findall(r'[\w]+', text)
            unique_words = set(words)
            
            if not words:
                return {
                    'type_token_ratio': 0.0,
                    'unique_words_count': 0,
                    'total_words_count': 0,
                    'status': 'no_words'
                }
            
            # 类型符比率 (TTR)
            ttr = len(unique_words) / len(words)
            
            return {
                'type_token_ratio': ttr,
                'unique_words_count': len(unique_words),
                'total_words_count': len(words),
                'status': 'success'
            }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def calculate_sentence_complexity(self, text: str) -> Dict[str, float]:
        """计算句子复杂度"""
        try:
            # 分割句子
            sentences = re.split(r'[。！？.!?]', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                return {
                    'avg_sentence_length': 0.0,
                    'avg_words_per_sentence': 0.0,
                    'sentence_count': 0,
                    'status': 'no_sentences'
                }
            
            # 计算平均句子长度（字符）
            avg_sentence_length = np.mean([len(s) for s in sentences])
            
            # 计算平均每句词数
            words_per_sentence = []
            for sentence in sentences:
                words = re.findall(r'[\w]+', sentence)
                words_per_sentence.append(len(words))
            
            avg_words_per_sentence = np.mean(words_per_sentence) if words_per_sentence else 0.0
            
            return {
                'avg_sentence_length': float(avg_sentence_length),
                'avg_words_per_sentence': float(avg_words_per_sentence),
                'sentence_count': len(sentences),
                'status': 'success'
            }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def calculate_pos_distribution(self, text: str) -> Dict[str, Any]:
        """计算词性分布（简化版）"""
        try:
            # 简化的词性分析（基于规则）
            words = re.findall(r'[\w]+', text)
            
            if not words:
                return {
                    'noun_ratio': 0.0,
                    'verb_ratio': 0.0,
                    'adjective_ratio': 0.0,
                    'adverb_ratio': 0.0,
                    'status': 'no_words'
                }
            
            # 简化的词性识别（基于词尾）
            nouns = [w for w in words if re.search(r'(者|性|化|点|力|感|度|性|化|点|力|感|度)$', w)]
            verbs = [w for w in words if re.search(r'(了|着|过|起来|下去|上来|下去)$', w)]
            adjectives = [w for w in words if re.search(r'(的|好|大|小|高|低|长|短|快|慢|美|丑|新|旧)$', w)]
            adverbs = [w for w in words if re.search(r'(地|很|非常|特别|十分|极其|相当|比较|稍微|略微)$', w)]
            
            total_words = len(words)
            
            return {
                'noun_ratio': len(nouns) / total_words if total_words > 0 else 0.0,
                'verb_ratio': len(verbs) / total_words if total_words > 0 else 0.0,
                'adjective_ratio': len(adjectives) / total_words if total_words > 0 else 0.0,
                'adverb_ratio': len(adverbs) / total_words if total_words > 0 else 0.0,
                'status': 'success'
            }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def calculate_readability_score(self, text: str) -> Dict[str, float]:
        """计算可读性分数"""
        try:
            # 分割句子
            sentences = re.split(r'[。！？.!?]', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # 提取词汇
            words = re.findall(r'[\w]+', text)
            
            if not sentences or not words:
                return {
                    'readability_score': 0.0,
                    'status': 'no_content'
                }
            
            # 计算平均句子长度
            avg_sentence_length = len(words) / len(sentences)
            
            # 计算平均词长
            avg_word_length = np.mean([len(w) for w in words]) if words else 0.0
            
            # 简化的可读性分数计算（基于平均句子长度和平均词长）
            # 这里使用一个简化的公式，实际应用中可以使用更复杂的可读性公式
            readability_score = 100 - (avg_sentence_length * 1.5 + avg_word_length * 10)
            readability_score = max(0, min(100, readability_score))  # 限制在0-100之间
            
            return {
                'readability_score': readability_score,
                'avg_sentence_length': avg_sentence_length,
                'avg_word_length': float(avg_word_length),
                'status': 'success'
            }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("生成测试报告...")
        
        # 保存JSON格式的详细结果到examine_3文件夹
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'examine_3', f'paper_test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        # 确保examine_3文件夹存在
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 详细结果已保存到: {json_path}")
        
    def calculate_text_coherence(self, text: str) -> Dict[str, float]:
        """计算文本连贯性"""
        if not BERT_AVAILABLE or self.bert_tokenizer is None or self.bert_model is None:
            return {
                'sentence_coherence': 0.0,
                'topic_coherence': 0.0,
                'overall_coherence': 0.0,
                'status': 'bert_unavailable'
            }
        
        try:
            # 将文本分割成句子
            sentences = re.split(r'[。！？.!?]', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) < 2:
                return {
                    'sentence_coherence': 0.0,
                    'topic_coherence': 0.0,
                    'overall_coherence': 0.0,
                    'status': 'insufficient_sentences'
                }
            
            # 计算相邻句子连贯性
            sentence_similarities = []
            for i in range(len(sentences) - 1):
                sim = self.calculate_sentence_similarity(sentences[i], sentences[i+1])
                sentence_similarities.append(sim)
            
            avg_sentence_coherence = np.mean(sentence_similarities) if sentence_similarities else 0.0
            
            # 计算主题连贯性（整个文本的一致性）
            topic_coherence = self.calculate_topic_coherence(sentences)
            
            # 综合连贯性得分
            overall_coherence = (avg_sentence_coherence + topic_coherence) / 2
            
            return {
                'sentence_coherence': float(avg_sentence_coherence),
                'topic_coherence': float(topic_coherence),
                'overall_coherence': float(overall_coherence),
                'status': 'success'
            }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def calculate_sentence_similarity(self, sentence1: str, sentence2: str) -> float:
        """计算两个句子的相似度"""
        try:
            # 对句子进行编码
            inputs1 = self.bert_tokenizer(sentence1, return_tensors='pt', truncation=True, max_length=512)
            inputs2 = self.bert_tokenizer(sentence2, return_tensors='pt', truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs1 = self.bert_model(**inputs1)
                outputs2 = self.bert_model(**inputs2)
                
                # 使用CLS标记的嵌入向量
                embedding1 = outputs1.last_hidden_state[:, 0, :].squeeze()
                embedding2 = outputs2.last_hidden_state[:, 0, :].squeeze()
                
                # 计算余弦相似度
                similarity = torch.cosine_similarity(embedding1, embedding2, dim=0)
                return float(similarity)
        except Exception as e:
            print(f"句子相似度计算失败: {e}")
            return 0.0
    
    def calculate_topic_coherence(self, sentences: List[str]) -> float:
        """计算主题连贯性"""
        try:
            if len(sentences) < 2:
                return 0.0
            
            # 计算所有句子的嵌入向量
            embeddings = []
            for sentence in sentences:
                inputs = self.bert_tokenizer(sentence, return_tensors='pt', truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = self.bert_model(**inputs)
                    embedding = outputs.last_hidden_state[:, 0, :].squeeze()
                    embeddings.append(embedding)
            
            # 计算所有句子嵌入向量的平均值（主题中心）
            topic_center = torch.mean(torch.stack(embeddings), dim=0)
            
            # 计算每个句子与主题中心的相似度
            similarities = []
            for embedding in embeddings:
                similarity = torch.cosine_similarity(embedding, topic_center, dim=0)
                similarities.append(float(similarity))
            
            # 返回平均相似度作为主题连贯性
            return np.mean(similarities) if similarities else 0.0
        except Exception as e:
            print(f"主题连贯性计算失败: {e}")
            return 0.0

    def run_coherence_tests(self):
        """运行连贯性测试"""
        print("\n2. 执行连贯性测试...")
        try:
            # 准备测试文本
            test_texts = {
                "连贯文本": "今天天气很好。阳光明媚，鸟语花香。我决定去公园散步。公园里有很多人在锻炼身体。我也加入了他们，感觉非常愉快。",
                "不连贯文本": "今天天气很好。计算机编程是一门复杂的学科。公园里有很多人在锻炼身体。量子力学是现代物理学的重要分支。我也加入了他们，感觉非常愉快。"
            }
            
            # 存储测试结果
            coherence_results = {}
            
            # 对每个测试文本进行连贯性评估
            for text_name, text_content in test_texts.items():
                print(f"\n  评估{text_name}...")
                
                coherence_metrics = self.calculate_text_coherence(text_content)
                coherence_results[text_name] = coherence_metrics
                
                if coherence_metrics['status'] == 'success':
                    print(f"    相邻句子连贯性: {coherence_metrics['sentence_coherence']:.4f}")
                    print(f"    主题连贯性: {coherence_metrics['topic_coherence']:.4f}")
                    print(f"    综合连贯性: {coherence_metrics['overall_coherence']:.4f}")
                else:
                    print(f"    评估失败: {coherence_metrics.get('error', coherence_metrics['status'])}")
            
            self.test_results['coherence_tests'] = {
                'status': 'completed',
                'results': coherence_results
            }
            print("✓ 连贯性测试完成")
        except Exception as e:
            print(f"✗ 连贯性测试失败: {e}")
            self.test_results['coherence_tests'] = {
                'status': 'failed',
                'error': str(e)
            }

def main():
    """主函数"""
    print("NovelCreator 论文数据测试框架")
    print("=" * 60)
    
    # 创建测试框架实例
    framework = PaperTestFramework()
    
    # 运行所有测试
    results = framework.run_all_tests()
    
    print("\n" + "=" * 60)
    print("论文数据测试完成!")

if __name__ == "__main__":
    main()