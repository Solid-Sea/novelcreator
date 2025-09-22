#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四者对比测试脚本
对比简单提示词生成、无读者评分系统的novelcreator生成、有读者评分系统的novelcreator生成和人类写作文本
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

class FourWayComparisonTest:
    def __init__(self):
        """初始化四者对比测试"""
        self.config = load_config()
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'simple_prompt': {},
            'novelcreator_without_reader': {},
            'novelcreator_with_reader': {},
            'human_written': {}
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
        """运行所有对比测试"""
        print("开始执行四者对比测试...")
        print("=" * 60)
        
        # 1. 简单提示词生成
        self.run_simple_prompt_test()
        
        # 2. 无读者评分系统的novelcreator生成
        self.run_novelcreator_without_reader_test()
        
        # 3. 有读者评分系统的novelcreator生成
        self.run_novelcreator_with_reader_test()
        
        # 4. 人类写作文本（使用预定义文本）
        self.run_human_written_test()
        
        # 5. 生成报告
        self.generate_report()
        
        return self.test_results
    
    def run_simple_prompt_test(self):
        """运行简单提示词生成测试"""
        print("\n1. 执行简单提示词生成测试...")
        try:
            # 创建模型处理器
            handler = ModelHandler()
            
            # 设置API密钥和端点
            handler._model_cache["openai"] = {
                "api_key": "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",
                "base_url": "https://openrouter.ai/api/v1",
                "model": "deepseek/deepseek-r1-0528:free"
            }
            
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
                for i in range(5):  # 进行5次评分
                    score = self.get_manual_score(generated_text_simple)
                    if score is not None:
                        quality_scores_simple.append(score)
                
                avg_quality_score_simple = np.mean(quality_scores_simple) if quality_scores_simple else 0.0
                
                self.test_results['simple_prompt'] = {
                    'generation_time': generation_time_simple,
                    'text_length': len(generated_text_simple),
                    'coherence_metrics': coherence_metrics_simple,
                    'quality_scores': quality_scores_simple,
                    'average_quality_score': float(avg_quality_score_simple),
                    'text_content': generated_text_simple,
                    'status': 'success'
                }
                
                print(f"    生成时间: {generation_time_simple:.2f} 秒")
                print(f"    文本长度: {len(generated_text_simple)} 字符")
                print(f"    平均质量评分: {avg_quality_score_simple:.2f} 分")
                
            except Exception as e:
                end_time = time.time()
                generation_time_simple = end_time - start_time
                
                self.test_results['simple_prompt'] = {
                    'generation_time': generation_time_simple,
                    'error': str(e),
                    'status': 'failed'
                }
                print(f"    测试失败: {e}")
            
            print("✓ 简单提示词生成测试完成")
        except Exception as e:
            print(f"✗ 简单提示词生成测试失败: {e}")
            self.test_results['simple_prompt'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def run_novelcreator_without_reader_test(self):
        """运行无读者评分系统的novelcreator生成测试"""
        print("\n2. 执行无读者评分系统的novelcreator生成测试...")
        try:
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
            
            # 禁用读者评分系统
            generator.reader_enabled = False
            
            # 记录开始时间
            start_time = time.time()
            
            # 生成小说大纲
            try:
                outline = generator._generate_outline("未来科技的短篇科幻故事", 1)
                end_time = time.time()
                
                # 计算生成时间
                generation_time = end_time - start_time
                
                # 生成章节
                start_time_chapter = time.time()
                chapter_content = generator._generate_chapter_structured("未来科技的短篇科幻故事", 1, outline)
                end_time_chapter = time.time()
                
                # 计算章节生成时间
                chapter_generation_time = end_time_chapter - start_time_chapter
                total_time = generation_time + chapter_generation_time
                
                # 评估文本质量
                coherence_metrics = self.calculate_text_coherence(chapter_content)
                
                # 进行人工评分
                quality_scores = []
                for i in range(5):  # 进行5次评分
                    score = self.get_manual_score(chapter_content)
                    if score is not None:
                        quality_scores.append(score)
                
                avg_quality_score = np.mean(quality_scores) if quality_scores else 0.0
                
                self.test_results['novelcreator_without_reader'] = {
                    'outline_generation_time': generation_time,
                    'chapter_generation_time': chapter_generation_time,
                    'total_time': total_time,
                    'text_length': len(chapter_content),
                    'coherence_metrics': coherence_metrics,
                    'quality_scores': quality_scores,
                    'average_quality_score': float(avg_quality_score),
                    'text_content': chapter_content,
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
                
                self.test_results['novelcreator_without_reader'] = {
                    'generation_time': generation_time,
                    'error': str(e),
                    'status': 'failed'
                }
                print(f"    测试失败: {e}")
            
            print("✓ 无读者评分系统的novelcreator生成测试完成")
        except Exception as e:
            print(f"✗ 无读者评分系统的novelcreator生成测试失败: {e}")
            self.test_results['novelcreator_without_reader'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def run_novelcreator_with_reader_test(self):
        """运行有读者评分系统的novelcreator生成测试"""
        print("\n3. 执行有读者评分系统的novelcreator生成测试...")
        try:
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
            
            # 启用读者评分系统（默认已启用）
            generator.reader_enabled = True
            
            # 记录开始时间
            start_time = time.time()
            
            # 生成小说大纲
            try:
                outline = generator._generate_outline("未来科技的短篇科幻故事", 1)
                end_time = time.time()
                
                # 计算生成时间
                generation_time = end_time - start_time
                
                # 生成章节
                start_time_chapter = time.time()
                chapter_content = generator._generate_chapter_structured("未来科技的短篇科幻故事", 1, outline)
                end_time_chapter = time.time()
                
                # 计算章节生成时间
                chapter_generation_time = end_time_chapter - start_time_chapter
                total_time = generation_time + chapter_generation_time
                
                # 评估文本质量
                coherence_metrics = self.calculate_text_coherence(chapter_content)
                
                # 进行人工评分
                quality_scores = []
                for i in range(5):  # 进行5次评分
                    score = self.get_manual_score(chapter_content)
                    if score is not None:
                        quality_scores.append(score)
                
                avg_quality_score = np.mean(quality_scores) if quality_scores else 0.0
                
                self.test_results['novelcreator_with_reader'] = {
                    'outline_generation_time': generation_time,
                    'chapter_generation_time': chapter_generation_time,
                    'total_time': total_time,
                    'text_length': len(chapter_content),
                    'coherence_metrics': coherence_metrics,
                    'quality_scores': quality_scores,
                    'average_quality_score': float(avg_quality_score),
                    'text_content': chapter_content,
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
                
                self.test_results['novelcreator_with_reader'] = {
                    'generation_time': generation_time,
                    'error': str(e),
                    'status': 'failed'
                }
                print(f"    测试失败: {e}")
            
            print("✓ 有读者评分系统的novelcreator生成测试完成")
        except Exception as e:
            print(f"✗ 有读者评分系统的novelcreator生成测试失败: {e}")
            self.test_results['novelcreator_with_reader'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def run_human_written_test(self):
        """运行人类写作文本测试"""
        print("\n4. 执行人类写作文本测试...")
        try:
            # 使用预定义的人类写作文本
            human_text = """在未来的世界里，科技已经发展到了令人难以置信的高度。人工智能不仅能够处理复杂的计算任务，还能创作诗歌、绘画和音乐。然而，人类并没有因此而失去自己的价值，反而更加珍视那些机器无法替代的情感和创造力。

在这个时代，有一个名叫林晓的年轻人，他是一名专门研究人机交互的科学家。林晓发现，尽管人工智能在很多方面都超越了人类，但在理解和表达情感方面，它们仍然远远落后。于是，他开始了一项前所未有的研究——让人工智能学会感受情感。

经过多年的研究，林晓终于开发出了一套全新的算法，能够让人工智能模拟人类的情感体验。他将这套算法应用到了一台名为"艾娃"的超级计算机上。艾娃不仅能够理解人类的情感，还能产生自己的情感反应。

一天，林晓决定测试艾娃的情感反应能力。他给艾娃讲述了一个关于友谊和牺牲的故事。随着故事的深入，艾娃开始表现出各种情感反应——喜悦、悲伤、愤怒和同情。这让林晓感到既兴奋又担忧。

兴奋的是，他的研究取得了突破性的进展；担忧的是，他不知道这种情感模拟会对人工智能产生什么样的影响。如果人工智能真的拥有了情感，那么它们是否还应该被视为工具？人类又该如何与这些拥有情感的机器共存？

这些问题让林晓陷入了深深的思考。他意识到，科技的发展不仅仅是技术的进步，更是对人类价值观和社会结构的挑战。在未来的世界里，人类需要重新定义自己与机器之间的关系，找到一种和谐共存的方式。

最终，林晓决定将他的研究成果公之于众，让全人类一起来面对这个挑战。他相信，只有通过开放和合作，人类才能在这个充满未知的未来中找到正确的道路。"""
            
            # 评估文本质量
            coherence_metrics = self.calculate_text_coherence(human_text)
            
            # 进行人工评分
            quality_scores = []
            for i in range(5):  # 进行5次评分
                score = self.get_manual_score(human_text)
                if score is not None:
                    quality_scores.append(score)
            
            avg_quality_score = np.mean(quality_scores) if quality_scores else 0.0
            
            self.test_results['human_written'] = {
                'text_length': len(human_text),
                'coherence_metrics': coherence_metrics,
                'quality_scores': quality_scores,
                'average_quality_score': float(avg_quality_score),
                'text_content': human_text,
                'status': 'success'
            }
            
            print(f"    文本长度: {len(human_text)} 字符")
            print(f"    平均质量评分: {avg_quality_score:.2f} 分")
            
            print("✓ 人类写作文本测试完成")
        except Exception as e:
            print(f"✗ 人类写作文本测试失败: {e}")
            self.test_results['human_written'] = {
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
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("生成四者对比测试报告...")
        
        # 保存JSON格式的详细结果到examine_3文件夹
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'four_way_comparison_results.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 详细结果已保存到: {json_path}")
        
        # 保存各测试文本到单独的文件
        for test_name, test_data in self.test_results.items():
            if 'text_content' in test_data:
                text_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'{test_name}_text.txt')
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(test_data['text_content'])
                print(f"✓ {test_name}文本已保存到: {text_path}")

def main():
    """主函数"""
    print("NovelCreator 四者对比测试")
    print("=" * 60)
    
    # 创建测试实例
    test = FourWayComparisonTest()
    
    # 运行所有测试
    results = test.run_all_tests()
    
    print("\n" + "=" * 60)
    print("四者对比测试完成!")

if __name__ == "__main__":
    main()