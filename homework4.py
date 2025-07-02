import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import time
import warnings
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import seaborn as sns
from collections import Counter
import random
import re
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class DLTSpider:
    def __init__(self):
        self.base_url = "https://www.zhcw.com/kjxx/dlt/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def get_page_data(self):
        """获取指定页面的数据"""
        try:
            print("尝试从网络获取数据...")
            # 如果网络不可用，直接使用本地文件
            with open("wangye.html", "r", encoding='utf-8') as f:
                return [f.read()]
        except FileNotFoundError:
            print("本地HTML文件不存在")
            return None

    def parse_lottery_data(self, html_content_list):
        """解析开奖数据"""
        all_data = []

        # 如果传入的是单个HTML内容，转换为列表
        if isinstance(html_content_list, str):
            html_content_list = [html_content_list]

        for page_num, html_content in enumerate(html_content_list, 1):
            print(f"正在解析第 {page_num} 页数据...")

            soup = BeautifulSoup(html_content, 'html.parser')

            # 查找包含开奖数据的表格
            table = soup.find('table')

            if not table:
                print(f"第 {page_num} 页未找到数据表格")
                continue

            # 查找表格的tbody部分
            tbody = table.find('tbody')
            if not tbody:
                print(f"第 {page_num} 页未找到表格数据")
                continue

            # 解析每一行数据
            rows = tbody.find_all('tr')

            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 14:  # 确保有足够的列
                        continue

                    # 提取期号
                    period = cells[0].get_text(strip=True)

                    # 提取开奖日期
                    date_text = cells[1].get_text(strip=True)
                    # 提取日期部分，去掉星期信息
                    date_match = date_text.split('（')[0] if '（' in date_text else date_text

                    # 提取前区号码
                    front_numbers = []
                    front_spans = cells[2].find_all('span', class_='jqh')
                    for span in front_spans:
                        front_numbers.append(span.get_text(strip=True))

                    # 提取后区号码
                    back_numbers = []
                    back_spans = cells[3].find_all('span', class_='jql')
                    for span in back_spans:
                        back_numbers.append(span.get_text(strip=True))

                    # 提取销售额
                    sales_amount = cells[4].get_text(strip=True)

                    # 提取一等奖信息
                    first_prize_count = cells[5].get_text(strip=True)
                    first_prize_amount = cells[6].get_text(strip=True)
                    first_prize_plus_count = cells[7].get_text(strip=True)
                    first_prize_plus_amount = cells[8].get_text(strip=True)

                    # 提取二等奖信息
                    second_prize_count = cells[9].get_text(strip=True)
                    second_prize_amount = cells[10].get_text(strip=True)
                    second_prize_plus_count = cells[11].get_text(strip=True)
                    second_prize_plus_amount = cells[12].get_text(strip=True)

                    # 提取奖池金额
                    prize_pool = cells[13].get_text(strip=True)

                    # 组装数据
                    lottery_data = {
                        '期号': period,
                        '开奖日期': date_match,
                        '前区号码': ' '.join(front_numbers),
                        '后区号码': ' '.join(back_numbers),
                        '销售额': sales_amount,
                        '一等奖注数': first_prize_count,
                        '一等奖单注奖金': first_prize_amount,
                        '一等奖追加注数': first_prize_plus_count,
                        '一等奖追加单注奖金': first_prize_plus_amount,
                        '二等奖注数': second_prize_count,
                        '二等奖单注奖金': second_prize_amount,
                        '二等奖追加注数': second_prize_plus_count,
                        '二等奖追加单注奖金': second_prize_plus_amount,
                        '奖池金额': prize_pool
                    }

                    all_data.append(lottery_data)

                except Exception as e:
                    print(f"解析行数据时出错: {e}")
                    continue

            print(f"第 {page_num} 页解析完成，获得 {len(rows)} 条数据")

        # 按期号排序，确保数据顺序正确
        if all_data:
            all_data.sort(key=lambda x: int(x['期号']), reverse=True)

        return all_data

    def crawl_lottery_data(self, target_periods=100):
        """爬取指定期数的开奖数据"""
        print("开始获取大乐透开奖数据...")

        # 获取HTML内容
        html_content_list = self.get_page_data()

        if not html_content_list:
            print("未能获取到数据")
            return []

        # 解析所有页面的数据
        all_data = self.parse_lottery_data(html_content_list)

        if not all_data:
            print("未能解析到开奖数据")
            return []

        print(f"总共解析到 {len(all_data)} 条开奖数据")

        # 过滤2025年7月1日之前的数据
        cutoff_date = datetime(2025, 7, 1)
        filtered_data = []

        for data in all_data:
            try:
                # 解析日期
                date_obj = datetime.strptime(data['开奖日期'], '%Y-%m-%d')
                if date_obj < cutoff_date:
                    filtered_data.append(data)
            except Exception as e:
                print(f"日期解析错误: {data['开奖日期']} - {e}")
                continue

        print(f"过滤后获得 {len(filtered_data)} 条2025年7月1日之前的数据")

        # 如果需要限制期数，取最新的target_periods期
        if len(filtered_data) > target_periods:
            filtered_data = filtered_data[:target_periods]
            print(f"按需求限制为最新 {target_periods} 期数据")

        return filtered_data

class DLTAnalyzer:
    def __init__(self, data):
        self.df = pd.DataFrame(data)
        self.prepare_data()
    
    def prepare_data(self):
        """数据预处理"""
        if self.df.empty:
            print("数据为空，无法进行分析")
            return
        
        # 转换日期格式
        self.df['开奖日期'] = pd.to_datetime(self.df['开奖日期'], errors='coerce')
        
        # 清理销售额数据
        self.df['销售额'] = self.df['销售额'].astype(str).str.replace(',', '').str.replace('元', '')
        self.df['销售额'] = pd.to_numeric(self.df['销售额'], errors='coerce').fillna(0)
        
        # 按日期排序
        self.df = self.df.sort_values('开奖日期').reset_index(drop=True)
        
        # 过滤掉2025年7月1日之后的数据
        cutoff_date = datetime(2025, 7, 1)
        self.df = self.df[self.df['开奖日期'] < cutoff_date]
        
        # 添加星期几列
        self.df['星期几'] = self.df['开奖日期'].dt.day_name()
        self.df['中文星期'] = self.df['开奖日期'].dt.dayofweek.map({
            0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'
        })

        print(f"数据预处理完成，共{len(self.df)}条有效数据")
        print(f"日期范围：{self.df['开奖日期'].min()} 到 {self.df['开奖日期'].max()}")
    
    def analyze_sales_trend(self):
        """分析销售额变化趋势并预测"""
        if self.df.empty or self.df['销售额'].sum() == 0:
            print("销售额数据不足，无法进行趋势分析")
            return
        
        # 创建图表
        plt.figure(figsize=(15, 10))
        
        # 子图1：销售额时间序列
        plt.subplot(2, 2, 1)
        plt.plot(self.df['开奖日期'], self.df['销售额'], marker='o', markersize=3, linewidth=1)
        plt.title('大乐透销售额变化趋势')
        plt.xlabel('开奖日期')
        plt.ylabel('销售额（元）')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        # 子图2：销售额分布直方图
        plt.subplot(2, 2, 2)
        plt.hist(self.df['销售额'], bins=20, alpha=0.7, edgecolor='black')
        plt.title('销售额分布')
        plt.xlabel('销售额（元）')
        plt.ylabel('频次')
        plt.grid(True, alpha=0.3)
        
        # 子图3：移动平均线
        plt.subplot(2, 2, 3)
        window = min(10, len(self.df) // 4)
        if window >= 2:
            moving_avg = self.df['销售额'].rolling(window=window).mean()
            plt.plot(self.df['开奖日期'], self.df['销售额'], alpha=0.5, label='原始数据')
            plt.plot(self.df['开奖日期'], moving_avg, color='red', linewidth=2, label=f'{window}期移动平均')
            plt.title('销售额移动平均线')
            plt.xlabel('开奖日期')
            plt.ylabel('销售额（元）')
            plt.legend()
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
        
        # 子图4：预测结果
        plt.subplot(2, 2, 4)
        recent_data = self.df['销售额'].tail(10)
        predicted_sales = recent_data.mean()

        plt.plot(range(len(recent_data)), recent_data, 'b-o', markersize=5, label='最近10期销售额')
        plt.axhline(y=predicted_sales, color='red', linestyle='--', label=f'预测销售额: {predicted_sales:.0f}元')
        plt.title('销售额预测')
        plt.xlabel('期数')
        plt.ylabel('销售额（元）')
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()
        
        # 打印详细统计信息
        print("\n=== 销售额统计分析 ===")
        print(f"数据期间：{self.df['开奖日期'].min().strftime('%Y-%m-%d')} 至 {self.df['开奖日期'].max().strftime('%Y-%m-%d')}")
        print(f"总期数：{len(self.df)}期")
        print(f"平均销售额：{self.df['销售额'].mean():.2f}元")
        print(f"销售额中位数：{self.df['销售额'].median():.2f}元")
        print(f"最高销售额：{self.df['销售额'].max():.2f}元")
        print(f"最低销售额：{self.df['销售额'].min():.2f}元")
        print(f"标准差：{self.df['销售额'].std():.2f}元")
        print(f"\n预测2025年7月1日后最近一期销售额：{predicted_sales:.0f}元")

        return predicted_sales

    def analyze_number_frequency(self, top_n=10):
        """分析号码出现频率"""
        if self.df.empty:
            print("数据为空，无法进行号码频率分析")
            return

        # 提取所有前区和后区号码
        all_front_numbers = []
        all_back_numbers = []

        for _, row in self.df.iterrows():
            front_numbers = row['前区号码'].split()
            back_numbers = row['后区号码'].split()

            all_front_numbers.extend([int(num) for num in front_numbers])
            all_back_numbers.extend([int(num) for num in back_numbers])

        # 计算号码频率
        front_number_freq = Counter(all_front_numbers)
        back_number_freq = Counter(all_back_numbers)

        # 创建完整的前区和后区号码频率统计
        front_freq_complete = {i: front_number_freq.get(i, 0) for i in range(1, 36)}
        back_freq_complete = {i: back_number_freq.get(i, 0) for i in range(1, 13)}

        # 创建可视化
        plt.figure(figsize=(20, 12))

        # 前区号码频率热力图
        plt.subplot(2, 2, 1)
        front_matrix = np.array(list(front_freq_complete.values())).reshape(7, 5)
        front_labels = np.array(list(front_freq_complete.keys())).reshape(7, 5)

        sns.heatmap(front_matrix, annot=front_labels, fmt='d', cmap='YlOrRd',
                   cbar_kws={'label': '出现次数'})
        plt.title('前区号码出现频率热力图（1-35）')

        # 后区号码频率热力图
        plt.subplot(2, 2, 2)
        back_matrix = np.array(list(back_freq_complete.values())).reshape(3, 4)
        back_labels = np.array(list(back_freq_complete.keys())).reshape(3, 4)

        sns.heatmap(back_matrix, annot=back_labels, fmt='d', cmap='YlOrRd',
                   cbar_kws={'label': '出现次数'})
        plt.title('后区号码出现频率热力图（1-12）')

        # 前区Top号码柱状图
        plt.subplot(2, 2, 3)
        common_front = front_number_freq.most_common(top_n)
        front_numbers, front_counts = zip(*common_front)
        plt.bar([str(num) for num in front_numbers], front_counts, color='skyblue')
        plt.title(f'前区号码出现频率Top {top_n}')
        plt.xlabel('号码')
        plt.ylabel('出现次数')
        plt.grid(axis='y', alpha=0.3)

        # 后区Top号码柱状图
        plt.subplot(2, 2, 4)
        common_back = back_number_freq.most_common(top_n)
        back_numbers, back_counts = zip(*common_back)
        plt.bar([str(num) for num in back_numbers], back_counts, color='lightcoral')
        plt.title(f'后区号码出现频率Top {top_n}')
        plt.xlabel('号码')
        plt.ylabel('出现次数')
        plt.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.show()

        # 分析热号和冷号
        print(f"\n=== 号码出现频率分析 ===")
        print(f"分析期数：{len(self.df)}期")

        # 前区热号和冷号
        front_hot_numbers = [num for num, _ in front_number_freq.most_common(10)]
        front_cold_numbers = [num for num in range(1, 36) if front_number_freq.get(num, 0) <= 2]

        print(f"\n前区热号（Top 10）：{', '.join(map(str, front_hot_numbers))}")
        print(f"前区冷号（出现≤2次）：{', '.join(map(str, sorted(front_cold_numbers)))}")

        # 后区热号和冷号
        back_hot_numbers = [num for num, _ in back_number_freq.most_common(6)]
        back_cold_numbers = [num for num in range(1, 13) if back_number_freq.get(num, 0) <= 1]

        print(f"\n后区热号（Top 6）：{', '.join(map(str, back_hot_numbers))}")
        print(f"后区冷号（出现≤1次）：{', '.join(map(str, sorted(back_cold_numbers)))}")

        return front_number_freq, back_number_freq

    def predict_lottery_numbers(self):
        """预测大乐透号码"""
        if self.df.empty:
            print("数据为空，无法进行号码预测")
            return None, None

        print("\n=== 智能号码预测 ===")

        # 获取历史频率
        front_freq, back_freq = self.analyze_number_frequency(top_n=15)

        # 最近20期趋势分析
        recent_df = self.df.tail(20)
        recent_front_numbers = []
        recent_back_numbers = []

        for _, row in recent_df.iterrows():
            front_numbers = row['前区号码'].split()
            back_numbers = row['后区号码'].split()
            recent_front_numbers.extend([int(num) for num in front_numbers])
            recent_back_numbers.extend([int(num) for num in back_numbers])

        recent_front_freq = Counter(recent_front_numbers)
        recent_back_freq = Counter(recent_back_numbers)

        # 综合评分算法
        def calculate_score(num, all_freq, recent_freq, is_front=True):
            max_num = 35 if is_front else 12

            # 历史频率权重 (40%)
            total_appearances = sum(all_freq.values())
            historical_score = (all_freq.get(num, 0) / total_appearances) * 40 if total_appearances > 0 else 0

            # 最近趋势权重 (30%)
            recent_total = sum(recent_freq.values())
            recent_score = (recent_freq.get(num, 0) / recent_total) * 30 if recent_total > 0 else 0

            # 平衡性权重 (20%)
            avg_freq = total_appearances / max_num if total_appearances > 0 else 0
            current_freq = all_freq.get(num, 0)
            balance_score = 20 - abs(current_freq - avg_freq) * 2
            balance_score = max(0, balance_score)

            # 随机因子 (10%)
            random_score = random.uniform(0, 10)

            return historical_score + recent_score + balance_score + random_score

        # 计算前区号码得分
        front_scores = {}
        for num in range(1, 36):
            score = calculate_score(num, front_freq, recent_front_freq, True)
            front_scores[num] = score

        # 计算后区号码得分
        back_scores = {}
        for num in range(1, 13):
            score = calculate_score(num, back_freq, recent_back_freq, False)
            back_scores[num] = score

        # 选择前区号码（确保奇偶和大小号平衡）
        sorted_front = sorted(front_scores.items(), key=lambda x: x[1], reverse=True)

        predicted_front = []
        odd_count = 0
        even_count = 0
        small_count = 0
        big_count = 0

        for num, score in sorted_front:
            if len(predicted_front) >= 5:
                break

            is_odd = num % 2 == 1
            is_small = num <= 17

            # 控制奇偶比例（建议2-3个奇数）
            if is_odd and odd_count >= 3:
                continue
            if not is_odd and even_count >= 3:
                continue

            # 控制大小号比例（建议2-3个小号）
            if is_small and small_count >= 3:
                continue
            if not is_small and big_count >= 3:
                continue

            predicted_front.append(num)
            if is_odd:
                odd_count += 1
            else:
                even_count += 1
            if is_small:
                small_count += 1
            else:
                big_count += 1

        # 如果没有足够的号码，补充最高分的号码
        if len(predicted_front) < 5:
            for num, score in sorted_front:
                if num not in predicted_front:
                    predicted_front.append(num)
                    if len(predicted_front) >= 5:
                        break

        # 选择后区号码
        sorted_back = sorted(back_scores.items(), key=lambda x: x[1], reverse=True)
        predicted_back = [num for num, score in sorted_back[:2]]

        # 格式化输出
        predicted_front_str = [f"{num:02d}" for num in sorted(predicted_front)]
        predicted_back_str = [f"{num:02d}" for num in sorted(predicted_back)]

        print("推荐号码组合：")
        print(f"前区：{' '.join(predicted_front_str)}")
        print(f"后区：{' '.join(predicted_back_str)}")

        # 分析推荐号码的特征
        odd_count = sum(1 for num in predicted_front if num % 2 == 1)
        small_count = sum(1 for num in predicted_front if num <= 17)

        print(f"\n号码特征分析：")
        print(f"奇偶比例：{odd_count}奇{5-odd_count}偶")
        print(f"大小比例：{small_count}小{5-small_count}大")

        # 生成多组备选号码
        print(f"\n=== 备选号码组合 ===")
        for i in range(3):
            # 基于智能预测生成备选组合
            backup_front = random.sample([num for num, _ in sorted_front[:15]], 5)
            backup_back = random.sample([num for num, _ in sorted_back[:8]], 2)

            front_str = [f"{num:02d}" for num in sorted(backup_front)]
            back_str = [f"{num:02d}" for num in sorted(backup_back)]

            print(f"备选{i+1}：前区 {' '.join(front_str)} | 后区 {' '.join(back_str)}")

        return predicted_front, predicted_back

    def analyze_weekday_patterns(self):
        """分析不同开奖日的号码分布和销售额特征"""
        if self.df.empty:
            print("数据为空，无法进行分析")
            return

        print("\n=== 不同开奖日分析 ===")

        # 筛选周一、周三、周六的数据
        target_days = ['周一', '周三', '周六']
        weekday_data = {}

        for day in target_days:
            day_df = self.df[self.df['中文星期'] == day]
            if not day_df.empty:
                weekday_data[day] = day_df

        if not weekday_data:
            print("没有找到周一、周三、周六的开奖数据")
            return

        # 创建可视化
        plt.figure(figsize=(20, 12))

        # 销售额对比
        plt.subplot(2, 3, 1)
        sales_by_day = []
        day_labels = []
        for day, data in weekday_data.items():
            sales_by_day.append(data['销售额'].tolist())
            day_labels.append(f"{day}({len(data)}期)")

        plt.boxplot(sales_by_day, labels=day_labels)
        plt.title('不同开奖日销售额分布对比')
        plt.ylabel('销售额（元）')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)

        # 前区号码频率对比
        plt.subplot(2, 3, 2)
        front_freq_by_day = {}
        for day, data in weekday_data.items():
            all_front = []
            for _, row in data.iterrows():
                front_numbers = row['前区号码'].split()
                all_front.extend([int(num) for num in front_numbers])
            front_freq_by_day[day] = Counter(all_front)

        # 计算每个号码在不同日期的出现频率
        all_front_numbers = list(range(1, 36))
        freq_matrix = []
        for num in all_front_numbers[:15]:  # 只显示前15个号码
            freq_row = []
            for day in target_days:
                if day in front_freq_by_day:
                    freq_row.append(front_freq_by_day[day].get(num, 0))
                else:
                    freq_row.append(0)
            freq_matrix.append(freq_row)

        freq_matrix = np.array(freq_matrix)
        sns.heatmap(freq_matrix,
                   xticklabels=[f"{day}({len(weekday_data.get(day, []))}期)" for day in target_days],
                   yticklabels=[f"{num:02d}" for num in all_front_numbers[:15]],
                   annot=True, fmt='d', cmap='Blues')
        plt.title('前区号码频率对比（前15个号码）')

        # 后区号码频率对比
        plt.subplot(2, 3, 3)
        back_freq_by_day = {}
        for day, data in weekday_data.items():
            all_back = []
            for _, row in data.iterrows():
                back_numbers = row['后区号码'].split()
                all_back.extend([int(num) for num in back_numbers])
            back_freq_by_day[day] = Counter(all_back)

        # 计算后区号码频率矩阵
        all_back_numbers = list(range(1, 13))
        back_freq_matrix = []
        for num in all_back_numbers:
            freq_row = []
            for day in target_days:
                if day in back_freq_by_day:
                    freq_row.append(back_freq_by_day[day].get(num, 0))
                else:
                    freq_row.append(0)
            back_freq_matrix.append(freq_row)

        back_freq_matrix = np.array(back_freq_matrix)
        sns.heatmap(back_freq_matrix,
                   xticklabels=[f"{day}({len(weekday_data.get(day, []))}期)" for day in target_days],
                   yticklabels=[f"{num:02d}" for num in all_back_numbers],
                   annot=True, fmt='d', cmap='Reds')
        plt.title('后区号码频率对比')

        # 奇偶比例分析
        plt.subplot(2, 3, 4)
        odd_even_patterns = {}
        for day, data in weekday_data.items():
            patterns = []
            for _, row in data.iterrows():
                front_numbers = [int(num) for num in row['前区号码'].split()]
                odd_count = sum(1 for num in front_numbers if num % 2 == 1)
                patterns.append(f"{odd_count}奇{5-odd_count}偶")
            odd_even_patterns[day] = Counter(patterns)

        # 绘制奇偶比例分布
        pattern_types = ['1奇4偶', '2奇3偶', '3奇2偶', '4奇1偶', '5奇0偶']
        x_pos = np.arange(len(pattern_types))
        bar_width = 0.25

        for i, (day, patterns) in enumerate(odd_even_patterns.items()):
            counts = [patterns.get(pattern, 0) for pattern in pattern_types]
            plt.bar(x_pos + i * bar_width, counts, bar_width, label=day)

        plt.xlabel('奇偶比例')
        plt.ylabel('出现次数')
        plt.title('不同开奖日奇偶比例分布')
        plt.xticks(x_pos + bar_width, pattern_types, rotation=45)
        plt.legend()
        plt.grid(axis='y', alpha=0.3)

        # 大小号比例分析
        plt.subplot(2, 3, 5)
        size_patterns = {}
        for day, data in weekday_data.items():
            patterns = []
            for _, row in data.iterrows():
                front_numbers = [int(num) for num in row['前区号码'].split()]
                small_count = sum(1 for num in front_numbers if num <= 17)
                patterns.append(f"{small_count}小{5-small_count}大")
            size_patterns[day] = Counter(patterns)

        # 绘制大小号比例分布
        size_types = ['1小4大', '2小3大', '3小2大', '4小1大', '5小0大']
        x_pos = np.arange(len(size_types))

        for i, (day, patterns) in enumerate(size_patterns.items()):
            counts = [patterns.get(pattern, 0) for pattern in size_types]
            plt.bar(x_pos + i * bar_width, counts, bar_width, label=day)

        plt.xlabel('大小号比例')
        plt.ylabel('出现次数')
        plt.title('不同开奖日大小号比例分布')
        plt.xticks(x_pos + bar_width, size_types, rotation=45)
        plt.legend()
        plt.grid(axis='y', alpha=0.3)

        # 统计信息对比
        plt.subplot(2, 3, 6)
        stats_text = ""
        for day, data in weekday_data.items():
            avg_sales = data['销售额'].mean()
            period_count = len(data)
            stats_text += f"{day}开奖统计：\n"
            stats_text += f"  期数：{period_count}期\n"
            stats_text += f"  平均销售额：{avg_sales:.0f}元\n\n"

        plt.text(0.1, 0.5, stats_text, fontsize=12, verticalalignment='center')
        plt.axis('off')
        plt.title('统计信息对比')

        plt.tight_layout()
        plt.show()

        # 打印详细统计信息
        print("=== 不同开奖日统计对比 ===")
        for day, data in weekday_data.items():
            print(f"\n{day}开奖（{len(data)}期）：")
            print(f"  平均销售额：{data['销售额'].mean():.2f}元")
            print(f"  销售额标准差：{data['销售额'].std():.2f}元")

            # 前区热门号码
            all_front = []
            for _, row in data.iterrows():
                front_numbers = row['前区号码'].split()
                all_front.extend([int(num) for num in front_numbers])
            front_freq = Counter(all_front)
            hot_front = [str(num) for num, _ in front_freq.most_common(5)]
            print(f"  前区热门号码：{', '.join(hot_front)}")

            # 后区热门号码
            all_back = []
            for _, row in data.iterrows():
                back_numbers = row['后区号码'].split()
                all_back.extend([int(num) for num in back_numbers])
            back_freq = Counter(all_back)
            hot_back = [str(num) for num, _ in back_freq.most_common(3)]
            print(f"  后区热门号码：{', '.join(hot_back)}")

    def analyze_expert_data(self):
        """分析真实专家数据"""
        print("\n=== 专家数据分析 ===")

        # 创建专家爬虫实例
        expert_spider = ExpertSpider()

        # 获取专家数据（30位专家）
        experts_data = expert_spider.crawl_experts(target_count=30)

        if not experts_data:
            print("未能获取专家数据")
            return None

        # 转换为DataFrame
        expert_df = pd.DataFrame(experts_data)

        print(f"成功获取{len(expert_df)}位专家数据")

        # 创建详细的可视化分析
        plt.figure(figsize=(20, 15))

        # 1. 专家彩龄分布
        plt.subplot(3, 3, 1)
        plt.hist(expert_df['彩龄'], bins=15, alpha=0.7, edgecolor='black', color='skyblue')
        plt.title('专家彩龄分布')
        plt.xlabel('彩龄（年）')
        plt.ylabel('专家数量')
        plt.grid(axis='y', alpha=0.3)

        # 2. 文章数量分布
        plt.subplot(3, 3, 2)
        plt.hist(expert_df['文章数量'], bins=15, alpha=0.7, edgecolor='black', color='orange')
        plt.title('专家发文量分布')
        plt.xlabel('文章数量（篇）')
        plt.ylabel('专家数量')
        plt.grid(axis='y', alpha=0.3)

        # 3. 专家等级分布
        plt.subplot(3, 3, 3)
        level_counts = expert_df['等级'].value_counts()
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
        plt.pie(level_counts.values, labels=level_counts.index, autopct='%1.1f%%', colors=colors)
        plt.title('专家等级分布')

        # 4. 大乐透一等奖分布
        plt.subplot(3, 3, 4)
        first_prize_counts = expert_df['大乐透一等奖'].value_counts().sort_index()
        plt.bar(first_prize_counts.index, first_prize_counts.values, alpha=0.7, color='gold')
        plt.title('大乐透一等奖中奖次数分布')
        plt.xlabel('一等奖次数')
        plt.ylabel('专家数量')
        plt.grid(axis='y', alpha=0.3)

        # 5. 彩龄与中奖率关系
        plt.subplot(3, 3, 5)
        plt.scatter(expert_df['彩龄'], expert_df['中奖率'], alpha=0.7, s=60)
        plt.xlabel('彩龄（年）')
        plt.ylabel('中奖率（%）')
        plt.title('彩龄与中奖率关系')
        plt.grid(True, alpha=0.3)

        # 计算相关系数
        correlation_age = expert_df['彩龄'].corr(expert_df['中奖率'])
        plt.text(0.05, 0.95, f'相关系数: {correlation_age:.3f}', transform=plt.gca().transAxes,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        # 6. 发文量与中奖率关系
        plt.subplot(3, 3, 6)
        plt.scatter(expert_df['文章数量'], expert_df['中奖率'], alpha=0.7, color='red', s=60)
        plt.xlabel('文章数量（篇）')
        plt.ylabel('中奖率（%）')
        plt.title('发文量与中奖率关系')
        plt.grid(True, alpha=0.3)

        # 计算相关系数
        correlation_articles = expert_df['文章数量'].corr(expert_df['中奖率'])
        plt.text(0.05, 0.95, f'相关系数: {correlation_articles:.3f}', transform=plt.gca().transAxes,
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

        # 7. 不同等级专家中奖率对比
        plt.subplot(3, 3, 7)
        level_win_rates = []
        level_labels = []
        for level in expert_df['等级'].unique():
            level_data = expert_df[expert_df['等级'] == level]['中奖率']
            if not level_data.empty:
                level_win_rates.append(level_data.tolist())
                level_labels.append(f"{level}({len(level_data)}人)")

        if level_win_rates:
            plt.boxplot(level_win_rates, labels=level_labels)
            plt.ylabel('中奖率（%）')
            plt.title('不同等级专家中奖率分布')
            plt.xticks(rotation=45)
            plt.grid(axis='y', alpha=0.3)

        # 8. 总中奖次数分布
        plt.subplot(3, 3, 8)
        plt.hist(expert_df['总中奖次数'], bins=20, alpha=0.7, edgecolor='black', color='lightgreen')
        plt.title('专家总中奖次数分布')
        plt.xlabel('总中奖次数')
        plt.ylabel('专家数量')
        plt.grid(axis='y', alpha=0.3)

        # 9. 中奖率分布
        plt.subplot(3, 3, 9)
        plt.hist(expert_df['中奖率'], bins=15, alpha=0.7, edgecolor='black', color='purple')
        plt.title('专家中奖率分布')
        plt.xlabel('中奖率（%）')
        plt.ylabel('专家数量')
        plt.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.show()

        # 创建专家中奖情况详细分析
        plt.figure(figsize=(15, 10))

        # 各等级奖项分布热力图
        plt.subplot(2, 2, 1)
        prize_data = expert_df.groupby('等级')[['大乐透一等奖', '大乐透二等奖', '大乐透三等奖']].sum()
        sns.heatmap(prize_data.T, annot=True, fmt='d', cmap='Reds', cbar_kws={'label': '中奖次数'})
        plt.title('不同等级专家各奖项中奖次数')
        plt.xlabel('专家等级')
        plt.ylabel('奖项类型')

        # 彩龄vs总中奖次数散点图
        plt.subplot(2, 2, 2)
        colors = expert_df['等级'].map({'初级': 'blue', '中级': 'green', '高级': 'red', '特级': 'purple'})
        plt.scatter(expert_df['彩龄'], expert_df['总中奖次数'], c=colors, alpha=0.7, s=80)
        plt.xlabel('彩龄（年）')
        plt.ylabel('总中奖次数')
        plt.title('彩龄与总中奖次数关系（按等级分色）')
        plt.grid(True, alpha=0.3)

        # 创建图例
        for level, color in [('初级', 'blue'), ('中级', 'green'), ('高级', 'red'), ('特级', 'purple')]:
            plt.scatter([], [], c=color, alpha=0.7, s=80, label=level)
        plt.legend()

        # 文章数量vs中奖率散点图（按彩龄分色）
        plt.subplot(2, 2, 3)
        scatter = plt.scatter(expert_df['文章数量'], expert_df['中奖率'],
                            c=expert_df['彩龄'], cmap='viridis', alpha=0.7, s=80)
        plt.xlabel('文章数量（篇）')
        plt.ylabel('中奖率（%）')
        plt.title('文章数量与中奖率关系（彩龄着色）')
        plt.colorbar(scatter, label='彩龄（年）')
        plt.grid(True, alpha=0.3)

        # 专家综合实力评分
        plt.subplot(2, 2, 4)
        # 计算综合评分：彩龄权重30% + 中奖率权重40% + 文章数量权重20% + 等级权重10%
        level_score = expert_df['等级'].map({'初级': 1, '中级': 2, '高级': 3, '特级': 4})

        expert_df['综合评分'] = (
            (expert_df['彩龄'] / expert_df['彩龄'].max()) * 30 +
            (expert_df['中奖率'] / expert_df['中奖率'].max()) * 40 +
            (expert_df['文章数量'] / expert_df['文章数量'].max()) * 20 +
            (level_score / level_score.max()) * 10
        )

        plt.hist(expert_df['综合评分'], bins=15, alpha=0.7, edgecolor='black', color='cyan')
        plt.title('专家综合实力评分分布')
        plt.xlabel('综合评分')
        plt.ylabel('专家数量')
        plt.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.show()

        # 打印详细统计报告
        print("\n" + "="*60)
        print("                专家数据统计分析报告")
        print("="*60)

        print(f"专家总数：{len(expert_df)}人")
        print(f"数据获取时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"\n=== 基本属性统计 ===")
        print(f"平均彩龄：{expert_df['彩龄'].mean():.1f}年（标准差：{expert_df['彩龄'].std():.1f}年）")
        print(f"彩龄范围：{expert_df['彩龄'].min()}年 - {expert_df['彩龄'].max()}年")
        print(f"平均发文量：{expert_df['文章数量'].mean():.0f}篇（标准差：{expert_df['文章数量'].std():.0f}篇）")
        print(f"发文量范围：{expert_df['文章数量'].min()}篇 - {expert_df['文章数量'].max()}篇")

        print(f"\n=== 中奖情况统计 ===")
        print(f"大乐透一等奖总计：{expert_df['大乐透一等奖'].sum()}次")
        print(f"大乐透二等奖总计：{expert_df['大乐透二等奖'].sum()}次")
        print(f"大乐透三等奖总计：{expert_df['大乐透三等奖'].sum()}次")
        print(f"平均中奖率：{expert_df['中奖率'].mean():.2f}%（标准差：{expert_df['中奖率'].std():.2f}%）")
        print(f"最高中奖率：{expert_df['中奖率'].max():.2f}%")
        print(f"最低中奖率：{expert_df['中奖率'].min():.2f}%")

        print(f"\n=== 不同等级专家统计 ===")
        for level in expert_df['等级'].unique():
            level_data = expert_df[expert_df['等级'] == level]
            if not level_data.empty:
                print(f"{level}专家（{len(level_data)}人）：")
                print(f"  平均彩龄：{level_data['彩龄'].mean():.1f}年")
                print(f"  平均发文量：{level_data['文章数量'].mean():.0f}篇")
                print(f"  平均中奖率：{level_data['中奖率'].mean():.2f}%")
                print(f"  一等奖总数：{level_data['大乐透一等奖'].sum()}次")

        print(f"\n=== 相关性分析 ===")
        print(f"彩龄与中奖率相关系数：{correlation_age:.3f}")
        print(f"发文量与中奖率相关系数：{correlation_articles:.3f}")

        # 计算更多相关性
        corr_age_total = expert_df['彩龄'].corr(expert_df['总中奖次数'])
        corr_articles_total = expert_df['文章数量'].corr(expert_df['总中奖次数'])
        print(f"彩龄与总中奖次数相关系数：{corr_age_total:.3f}")
        print(f"发文量与总中奖次数相关系数：{corr_articles_total:.3f}")

        print(f"\n=== Top 10 专家排行榜 ===")
        # 按综合评分排序
        top_experts = expert_df.nlargest(10, '综合评分')
        for i, (_, expert) in enumerate(top_experts.iterrows(), 1):
            print(f"{i:2d}. {expert['name']}：")
            print(f"    综合评分：{expert['综合评分']:.1f} | 彩龄：{expert['彩龄']}年 | 中奖率：{expert['中奖率']:.2f}%")
            print(f"    发文：{expert['文章数量']}篇 | 等级：{expert['等级']} | 一等奖：{expert['大乐透一等奖']}次")

        print(f"\n=== 中奖效率最高专家 ===")
        # 按中奖率排序
        top_winners = expert_df.nlargest(5, '中奖率')
        for i, (_, expert) in enumerate(top_winners.iterrows(), 1):
            print(f"{i}. {expert['name']}：中奖率{expert['中奖率']:.2f}%，彩龄{expert['彩龄']}年，一等奖{expert['大乐透一等奖']}次")

        # 保存专家数据分析结果
        try:
            expert_df.to_csv('expert_analysis_result.csv', index=False, encoding='utf-8-sig')
            print(f"\n专家分析结果已保存到：expert_analysis_result.csv")
        except Exception as e:
            print(f"保存分析结果失败：{e}")

        print("\n" + "="*60)
        print("                专家数据分析完成")
        print("="*60)

        return expert_df

    def save_data(self, filename='dlt_data.csv'):
        """保存数据到CSV文件"""
        try:
            self.df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"数据已保存到：{filename}")
        except Exception as e:
            print(f"保存数据失败：{e}")

def show_menu():
    """显示菜单"""
    print("\n" + "="*60)
    print("               大乐透数据分析系统")
    print("="*60)
    print("请选择功能：")
    print("1. 销售额趋势分析与预测")
    print("2. 号码频率统计与可视化分析")
    print("3. 智能号码预测推荐")
    print("4. 不同开奖日对比分析")
    print("5. 专家数据统计分析")
    print("6. 综合分析报告")
    print("0. 退出系统")
    print("="*60)

def main():
    """主函数"""
    print("=== 大乐透数据分析系统启动 ===")

    # 加载数据
    try:
        print("正在加载数据...")
        # 优先从CSV文件加载
        try:
            df_existing = pd.read_csv('大乐透开奖数据.csv', encoding='utf-8-sig')
            if not df_existing.empty:
                print(f"从CSV文件加载数据成功，共{len(df_existing)}条记录")
                lottery_data = df_existing.to_dict('records')
            else:
                raise FileNotFoundError("CSV文件为空")
        except:
            # 如果CSV文件不存在或为空，从爬虫获取数据
            print("CSV文件不存在或为空，尝试获取新数据...")
            spider = DLTSpider()
            lottery_data = spider.crawl_lottery_data(target_periods=100)
            if not lottery_data:
                print("无法获取数据，程序退出")
                return

        # 创建分析器实例
        analyzer = DLTAnalyzer(lottery_data)
        analyzer.save_data('大乐透开奖数据.csv')

        # 主循环
        while True:
            show_menu()
            try:
                choice = input("请输入选择（0-6）：").strip()

                if choice == '0':
                    print("感谢使用大乐透数据分析系统！")
                    break
                elif choice == '1':
                    print("\n执行销售额趋势分析与预测...")
                    analyzer.analyze_sales_trend()
                elif choice == '2':
                    print("\n执行号码频率统计与可视化分析...")
                    analyzer.analyze_number_frequency(top_n=10)
                elif choice == '3':
                    print("\n执行智能号码预测...")
                    predicted_front, predicted_back = analyzer.predict_lottery_numbers()
                    if predicted_front and predicted_back:
                        front_str = [f"{num:02d}" for num in sorted(predicted_front)]
                        back_str = [f"{num:02d}" for num in sorted(predicted_back)]
                        print(f"\n🎯 2025年7月1日后最新一期推荐号码：")
                        print(f"前区：{' '.join(front_str)}")
                        print(f"后区：{' '.join(back_str)}")
                elif choice == '4':
                    print("\n执行不同开奖日对比分析...")
                    analyzer.analyze_weekday_patterns()
                elif choice == '5':
                    print("\n执行专家数据统计分析...")
                    analyzer.analyze_expert_data()
                elif choice == '6':
                    print("\n生成综合分析报告...")
                    # 执行所有分析
                    analyzer.analyze_sales_trend()
                    analyzer.analyze_number_frequency(top_n=10)
                    predicted_front, predicted_back = analyzer.predict_lottery_numbers()
                    analyzer.analyze_weekday_patterns()
                    analyzer.analyze_expert_data()

                    if predicted_front and predicted_back:
                        front_str = [f"{num:02d}" for num in sorted(predicted_front)]
                        back_str = [f"{num:02d}" for num in sorted(predicted_back)]
                        print(f"\n🎯 最终推荐号码：")
                        print(f"前区：{' '.join(front_str)}")
                        print(f"后区：{' '.join(back_str)}")
                else:
                    print("无效选择，请重新输入！")

                input("\n按回车键继续...")

            except KeyboardInterrupt:
                print("\n\n程序被用户中断")
                break
            except Exception as e:
                print(f"执行过程中发生错误：{e}")
                input("按回车键继续...")

    except Exception as e:
        print(f"程序启动失败：{e}")


class ExpertSpider:
    def __init__(self):
        self.base_url = "https://www.cmzj.net/dlt/tickets"
        self.expert_base_url = "https://www.cmzj.net/expertItem"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

    def get_expert_list(self, target_count=30):
        """获取专家列表，通过换一批按钮获取更多专家"""
        try:
            # 配置浏览器选项
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            print(f"正在访问专家页面: {self.base_url}")
            driver.get(self.base_url)
            time.sleep(5)

            all_experts = []
            rounds = 0
            max_rounds = 6

            while len(all_experts) < target_count and rounds < max_rounds:
                print(f"第{rounds + 1}轮获取专家信息...")

                # 等待专家列表加载
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "items"))
                    )
                    time.sleep(2)
                except:
                    print("专家列表加载超时")
                    break

                # 获取当前页面的前8个专家名称
                expert_names = []
                try:
                    experts = driver.find_elements(By.CLASS_NAME, "items")
                    expert_items = experts[:8]  # 只取前8个作为专家

                    print(f"找到 {len(expert_items)} 个专家item")

                    for expert in expert_items:
                        try:
                            name_element = expert.find_element(By.CLASS_NAME, "okami-name")
                            expert_name = name_element.text.strip()

                            # 检查是否已经获取过该专家
                            if expert_name and expert_name not in [e['name'] for e in all_experts]:
                                expert_names.append(expert_name)

                        except Exception as e:
                            print(f"提取专家名称时出错: {e}")
                            continue

                    print(f"本轮准备获取 {len(expert_names)} 位新专家数据")

                except Exception as e:
                    print(f"获取专家列表时出错: {e}")
                    break

                # 逐个点击专家获取详细信息
                for i, expert_name in enumerate(expert_names):
                    try:
                        if len(all_experts) >= target_count:
                            break

                        print(f"正在获取第{i + 1}位专家：{expert_name}")

                        # 确保在主页面，重新查找专家元素
                        current_url = driver.current_url
                        if self.base_url not in current_url:
                            print("不在主页面，返回主页面")
                            driver.get(self.base_url)
                            time.sleep(3)
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "items"))
                            )
                            time.sleep(2)

                        # 重新获取专家元素列表（只查找前8个）
                        experts = driver.find_elements(By.CLASS_NAME, "items")
                        expert_items = experts[:8]
                        target_expert = None

                        # 在前8个专家中查找目标专家
                        for expert in expert_items:
                            try:
                                name_element = expert.find_element(By.CLASS_NAME, "okami-name")
                                if name_element.text.strip() == expert_name:
                                    target_expert = name_element
                                    break
                            except:
                                continue

                        if target_expert:
                            # 点击专家名称进入详情页
                            print(f"点击专家：{expert_name}")
                            driver.execute_script("arguments[0].click();", target_expert)
                            time.sleep(3)

                            # 等待详情页加载
                            try:
                                WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, "okami-text"))
                                )
                                time.sleep(2)
                            except:
                                print(f"专家详情页加载超时：{expert_name}")
                                # 返回主页面继续
                                driver.get(self.base_url)
                                time.sleep(3)
                                continue

                            # 获取专家详细信息
                            expert_data = self.parse_expert_detail(driver)
                            if expert_data:
                                expert_data['name'] = expert_name
                                all_experts.append(expert_data)
                                print(f"成功获取专家 {expert_name} 的数据，目前总数：{len(all_experts)}")
                            else:
                                print(f"获取专家 {expert_name} 数据失败")

                            # 返回主页面
                            print("返回主页面...")
                            driver.get(self.base_url)
                            time.sleep(3)

                            # 等待主页面加载完成
                            try:
                                WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CLASS_NAME, "items"))
                                )
                                time.sleep(2)
                            except:
                                print("返回主页面加载超时")
                                break

                        else:
                            print(f"未找到专家：{expert_name}")

                    except Exception as e:
                        print(f"处理专家 {expert_name} 时出错: {e}")
                        # 确保返回主页面
                        try:
                            driver.get(self.base_url)
                            time.sleep(3)
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "items"))
                            )
                            time.sleep(2)
                        except:
                            print("返回主页面失败")
                            break
                        continue

                rounds += 1

                # 如果还需要更多专家，点击"换一批"按钮
                if len(all_experts) < target_count and rounds < max_rounds:
                    try:
                        print("准备点击'换一批'按钮...")

                        # 确保在主页面
                        current_url = driver.current_url
                        if self.base_url not in current_url:
                            driver.get(self.base_url)
                            time.sleep(3)
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "items"))
                            )
                            time.sleep(2)

                        # 查找并点击"换一批"按钮
                        change_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.change"))
                        )

                        # 滚动到按钮位置
                        driver.execute_script("arguments[0].scrollIntoView(true);", change_button)
                        time.sleep(1)

                        # 点击换一批按钮
                        driver.execute_script("arguments[0].click();", change_button)
                        print("成功点击'换一批'按钮")
                        time.sleep(4)  # 等待新的专家列表加载

                        # 验证新列表是否加载
                        try:
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "items"))
                            )
                            time.sleep(2)
                            print("新专家列表加载完成")
                        except:
                            print("新专家列表加载超时")
                            break

                    except Exception as e:
                        print(f"点击'换一批'按钮失败: {e}")
                        # 尝试其他方式查找按钮
                        try:
                            # 尝试通过包含文本"换一批"的元素查找
                            change_buttons = driver.find_elements(By.XPATH, "//div[contains(@class, 'change')]")
                            if change_buttons:
                                driver.execute_script("arguments[0].click();", change_buttons[0])
                                print("通过备用方法点击'换一批'按钮")
                                time.sleep(4)
                            else:
                                print("未找到'换一批'按钮，结束获取")
                                break
                        except Exception as e2:
                            print(f"备用方法也失败: {e2}")
                            break

            driver.quit()
            print(f"专家数据获取完成，共获取{len(all_experts)}位专家信息")
            return all_experts

        except Exception as e:
            print(f"获取专家列表时出错: {e}")
            try:
                driver.quit()
            except:
                pass
            return []

    def parse_expert_detail(self, driver):
        """解析专家详情页面"""
        try:
            # 等待页面加载
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "okami-text"))
            )
            time.sleep(2)

            expert_data = {}

            # 获取彩龄
            try:
                cailing_elements = driver.find_elements(By.XPATH, "//p[contains(text(), '彩龄：')]/span")
                if cailing_elements:
                    cailing_text = cailing_elements[0].text.strip()
                    cailing_match = re.search(r'(\d+)', cailing_text)
                    expert_data['彩龄'] = int(cailing_match.group(1)) if cailing_match else 1
                else:
                    # 备用方法
                    cailing_p = driver.find_elements(By.XPATH, "//p[contains(text(), '彩龄：')]")
                    if cailing_p:
                        cailing_text = cailing_p[0].text
                        cailing_match = re.search(r'彩龄：(\d+)', cailing_text)
                        expert_data['彩龄'] = int(cailing_match.group(1)) if cailing_match else 1
                    else:
                        expert_data['彩龄'] = 1
            except Exception as e:
                print(f"获取彩龄时出错: {e}")
                expert_data['彩龄'] = 1

            # 获取文章数量
            try:
                article_elements = driver.find_elements(By.XPATH, "//p[contains(text(), '文章数量：')]/span")
                if article_elements:
                    article_text = article_elements[0].text.strip()
                    article_match = re.search(r'(\d+)', article_text)
                    expert_data['文章数量'] = int(article_match.group(1)) if article_match else 0
                else:
                    # 备用方法
                    article_p = driver.find_elements(By.XPATH, "//p[contains(text(), '文章数量：')]")
                    if article_p:
                        article_text = article_p[0].text
                        article_match = re.search(r'文章数量：(\d+)', article_text)
                        expert_data['文章数量'] = int(article_match.group(1)) if article_match else 0
                    else:
                        expert_data['文章数量'] = 0
            except Exception as e:
                print(f"获取文章数量时出错: {e}")
                expert_data['文章数量'] = 0

            # 初始化中奖情况
            expert_data['大乐透一等奖'] = 0
            expert_data['大乐透二等奖'] = 0
            expert_data['大乐透三等奖'] = 0

            # 获取大乐透中奖情况
            try:
                # 查找所有包含奖项信息的元素
                prize_elements = driver.find_elements(By.XPATH, "//div[@class='item']")

                for item in prize_elements:
                    try:
                        item_text = item.text
                        # 匹配大乐透各等奖
                        if '大乐透' in item_text and '一等奖' in item_text:
                            match = re.search(r'(\d+)', item_text)
                            if match:
                                expert_data['大乐透一等奖'] = int(match.group(1))
                        elif '大乐透' in item_text and '二等奖' in item_text:
                            match = re.search(r'(\d+)', item_text)
                            if match:
                                expert_data['大乐透二等奖'] = int(match.group(1))
                        elif '大乐透' in item_text and '三等奖' in item_text:
                            match = re.search(r'(\d+)', item_text)
                            if match:
                                expert_data['大乐透三等奖'] = int(match.group(1))
                    except Exception as e:
                        continue

            except Exception as e:
                print(f"解析中奖情况时出错: {e}")

            # 获取专家等级
            try:
                level_elements = driver.find_elements(By.CLASS_NAME, "expert-rank")
                if level_elements:
                    level_text = level_elements[0].text
                    if '特级' in level_text:
                        expert_data['等级'] = '特级'
                    elif '高级' in level_text:
                        expert_data['等级'] = '高级'
                    elif '中级' in level_text:
                        expert_data['等级'] = '中级'
                    else:
                        expert_data['等级'] = '初级'
                else:
                    expert_data['等级'] = '初级'
            except Exception as e:
                print(f"获取专家等级时出错: {e}")
                expert_data['等级'] = '初级'

            # 计算总中奖次数和中奖率
            total_wins = expert_data['大乐透一等奖'] + expert_data['大乐透二等奖'] + expert_data['大乐透三等奖']
            expert_data['总中奖次数'] = total_wins

            # 估算推荐次数（基于彩龄和文章数量）
            estimated_predictions = max(expert_data['彩龄'] * 50, expert_data['文章数量'] * 2, 100)
            expert_data['推荐次数'] = estimated_predictions

            # 计算中奖率
            if estimated_predictions > 0:
                expert_data['中奖率'] = (total_wins / estimated_predictions) * 100
            else:
                expert_data['中奖率'] = 0

            print(f"专家数据: 彩龄{expert_data['彩龄']}年, 文章{expert_data['文章数量']}篇, 大乐透中奖{total_wins}次")
            return expert_data

        except Exception as e:
            print(f"解析专家详情时出错: {e}")
            return None

    def crawl_experts(self, target_count=30):
        """爬取专家数据的主方法"""
        print(f"开始获取{target_count}位专家数据...")

        experts_data = self.get_expert_list(target_count)

        if experts_data:
            print(f"成功获取{len(experts_data)}位专家数据")

            # 保存专家数据到文件
            try:
                expert_df = pd.DataFrame(experts_data)
                expert_df.to_csv('experts_data.csv', index=False, encoding='utf-8-sig')
                print("专家数据已保存到：experts_data.csv")
            except Exception as e:
                print(f"保存专家数据失败：{e}")
        else:
            print("未获取到任何专家数据")

        return experts_data

    def generate_mock_data(self, count=30):
        """生成模拟专家数据（备用方案）"""
        expert_names = [
            "倩女幽球", "诸葛战神", "刘飞", "福道缘", "纳财纳福",
            "金铃铛", "引领者", "时代彩民", "彩票达人", "幸运星",
            "数字专家", "预测大师", "中奖王", "彩神", "运势分析师",
            "号码猎手", "彩票研究员", "大奖收割机", "选号专家", "概率大师",
            "走势分析师", "彩票教授", "中奖专家", "数据分析师", "彩票顾问",
            "预测专家", "彩票导师", "中奖助手", "号码专家", "彩票学者"
        ]

        np.random.seed(42)
        mock_experts = []

        for i, name in enumerate(expert_names[:count]):
            expert = {
                'name': name,
                '彩龄': np.random.randint(3, 20),
                '文章数量': np.random.randint(100, 2000),
                '大乐透一等奖': np.random.choice([0, 1, 2, 3, 4, 5], p=[0.3, 0.3, 0.2, 0.1, 0.07, 0.03]),
                '大乐透二等奖': np.random.randint(0, 8),
                '大乐透三等奖': np.random.randint(2, 20),
                '等级': np.random.choice(['初级', '中级', '高级', '特级'], p=[0.2, 0.3, 0.4, 0.1])
            }

            # 计算总中奖次数
            total_wins = expert['大乐透一等奖'] + expert['大乐透二等奖'] + expert['大乐透三等奖']
            expert['总中奖次数'] = total_wins

            # 估算推荐次数
            estimated_predictions = max(expert['彩龄'] * 50, expert['文章数量'] * 2, 200)
            expert['推荐次数'] = estimated_predictions

            # 计算中奖率
            expert['中奖率'] = (total_wins / estimated_predictions) * 100

            mock_experts.append(expert)

        return mock_experts

if __name__ == "__main__":
    main()