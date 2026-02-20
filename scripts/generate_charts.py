import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import os
import re                  
from datetime import datetime 

def create_category_chart(client, category_sql_name, chart_title, filename, theme_color, extra_sql_filter=""):
    """
    Mean, Median, Item Count 시각화 (라벨 겹침 방지 및 상단 배치 버전)
    """
    
    # 1. SQL Query
    query = f"""
    WITH parsed_data AS (
        SELECT 
            date,
            COALESCE(
                SAFE_CAST(REPLACE(REPLACE(sale_price, '$', ''), ',', '') AS FLOAT64), 
                SAFE_CAST(REPLACE(REPLACE(original_price, '$', ''), ',', '') AS FLOAT64)
            ) AS price
        FROM 
            `cc-auto-scaper.cc_data.products`
        WHERE 
            category = '{category_sql_name}'
            AND date IS NOT NULL
    )
    SELECT * FROM parsed_data
    WHERE price IS NOT NULL
    {extra_sql_filter}
    """
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        print(f"⚠️ No data found for category: {chart_title}")
        return

    # 2. 데이터 전처리 및 집계
    df['date'] = pd.to_datetime(df['date']).dt.normalize()
    daily_stats = df.groupby('date')['price'].agg(['mean', 'median', 'count']).reset_index()
    daily_stats = daily_stats.sort_values('date')

    # 3. 스타일 설정
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.set_facecolor('white')
    ax1.grid(axis='y', linestyle='--', alpha=0.3, color='gray')
    ax1.set_axisbelow(True)

    # 4. 플롯 그리기 (Price)
    ax1.plot(daily_stats['date'], daily_stats['mean'], 
            linestyle='--', linewidth=2, alpha=0.7,
            color=theme_color, label='Mean (Avg)')
            
    ax1.plot(daily_stats['date'], daily_stats['median'], 
            linestyle='-', marker='o', markersize=5, linewidth=2.5, 
            color=theme_color, label='Median')
    
    ax1.fill_between(daily_stats['date'], daily_stats['median'], 
                    color=theme_color, alpha=0.05)

    # 5. Volume Tracking (Item Count)
    ax2 = ax1.twinx()
    ax2.bar(daily_stats['date'], daily_stats['count'], 
            color='gray', alpha=0.15, width=0.8, label='Item Count')
    ax2.set_ylim(0, daily_stats['count'].max() * 4) # 배경처럼 깔리게 더 낮춤
    ax2.set_ylabel('Available Item Count', fontsize=10, color='gray')

    # 6. Annotation (라벨 겹침 방지 로직 적용)
    last_date = daily_stats['date'].iloc[-1]
    last_median = daily_stats['median'].iloc[-1]
    last_mean = daily_stats['mean'].iloc[-1]
    last_count = int(daily_stats['count'].iloc[-1])
    
    # How: Median은 항상 포인트 바로 위에 박스 형태로 배치
    ax1.annotate(f'Median: ${last_median:,.0f}', 
                xy=(last_date, last_median), 
                xytext=(0, 15), textcoords='offset points',
                ha='center', va='bottom',
                fontsize=10, fontweight='bold', color=theme_color,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=theme_color, alpha=0.9))
    
    # How: Mean과 Median이 겹치지 않도록 Mean의 위치를 상대적으로 조정
    # Mean이 Median보다 높으면 더 위로, 낮으면 아래로 배치
    if last_mean > last_median:
        mean_offset = 45 # Median 박스보다 더 위로
        mean_va = 'bottom'
    else:
        mean_offset = -30 # 포인트 아래로
        mean_va = 'top'

    ax1.annotate(f'Mean: ${last_mean:,.0f}\nCount: {last_count}', 
                xy=(last_date, last_mean), 
                xytext=(0, mean_offset), textcoords='offset points', 
                ha='center', va=mean_va,
                fontsize=9, color='gray', fontweight='semibold')

    # 7. 축 및 레이블 설정
    sns.despine(ax=ax1, left=True, bottom=False, right=False)
    sns.despine(ax=ax2, left=True, bottom=False, right=True)
    
    ax1.set_title(chart_title, fontsize=18, fontweight='bold', pad=30, loc='left')
    ax1.set_ylabel('Price (CAD)', fontsize=11, color='gray')
    
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', frameon=False) 
    
    # Y축 범위 최적화 (텍스트 라벨이 들어갈 공간 확보)
    all_prices = pd.concat([daily_stats['mean'], daily_stats['median']])
    min_price = all_prices.min()
    max_price = all_prices.max()
    
    margin_bottom = (max_price - min_price) * 0.2
    margin_top = (max_price - min_price) * 0.4 # 상단 텍스트 공간을 위해 더 넓게 잡음
    
    ax1.set_ylim(max(0, min_price - margin_bottom), max_price + margin_top)

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xticks(rotation=0)

    plt.tight_layout()

    # 8. 저장 로직 (기존과 동일)
    if os.getenv('GITHUB_ACTIONS') == 'true':
        output_dir = "docs/images"
    else:
        output_dir = r"C:\Users\dkang\OneDrive\Desktop\D\tech-base\docs\images"
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ 개선된 차트 생성 완료: {output_path}")

def update_markdown_timestamps(md_file_path):
    try:
        new_version = datetime.now().strftime("%Y%m%d%H%M")
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = re.sub(r'\.png\?v=[a-zA-Z0-9_]+', f'.png?v={new_version}', content)
        
        if content != new_content:
            with open(md_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Cache busting tags updated in {md_file_path} to: ?v={new_version}")
        else:
            print(f"ℹ️ No timestamp tags found in {md_file_path} or already up to date.")
            
    except FileNotFoundError:
        print(f"⚠️ Warning: Could not find markdown file at {md_file_path}. Check the path.")

def run_analysis():
    client = bigquery.Client()
    
    targets = [
        {
            'sql_name': 'memory', 
            'title': 'RAM Price Trend', 
            'filename': 'ram_price_trend.png', 
            'color': '#10B981',
            'sql_filter': ''
        },
        {
            'sql_name': 'ssd',      
            'title': 'SSD Price Trend', 
            'filename': 'ssd_price_trend.png', 
            'color': '#8B5CF6',
            'sql_filter': ''
        },
        {
            'sql_name': 'motherboard',      
            'title': 'Motherboard Price Trend', 
            'filename': 'motherboard_price_trend.png', 
            'color': '#F59E0B',
            'sql_filter': ''
        },
        # GPU 분리: 가격 기준 $1,000 Cut
        {
            'sql_name': 'gpu',      
            'title': 'High-End GPU Price (>$1000)', 
            'filename': 'gpu_high_price_trend.png', 
            'color': '#1D4ED8',
            'sql_filter': "AND price >= 1000"
        },
        {
            'sql_name': 'gpu',      
            'title': 'Mid-Range GPU Price (<$1000)', 
            'filename': 'gpu_mid_price_trend.png', 
            'color': '#3B82F6',
            'sql_filter': "AND price < 1000"
        },
        # 드론 분리: 가격 기준 $2,000 Cut
        {
            'sql_name': 'drone',      
            'title': 'Pro Drone Price (>$2000)', 
            'filename': 'drone_pro_price_trend.png', 
            'color': '#B91C1C',
            'sql_filter': "AND price >= 2000"
        },
        {
            'sql_name': 'drone',      
            'title': 'Consumer Drone Price (<$2000)', 
            'filename': 'drone_consumer_price_trend.png', 
            'color': '#EF4444',
            'sql_filter': "AND price < 2000"
        }
    ]

    for t in targets:
        print(f"Processing {t['title']}...")
        create_category_chart(
            client=client,
            category_sql_name=t['sql_name'],
            chart_title=t['title'],
            filename=t['filename'],
            theme_color=t['color'],
            extra_sql_filter=t.get('sql_filter', '')
        )
    
    print("Updating Markdown timestamps...")
    update_markdown_timestamps("docs/projects/ca-pc-parts-tracker.md")

if __name__ == "__main__":
    run_analysis()