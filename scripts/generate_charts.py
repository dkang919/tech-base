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
    Mean, Median, and Item Count 시각화
    """
    
    # 1. SQL Query
    # How: extra_sql_filter를 추가하여 특정 키워드가 포함된 제품만 필터링 (Sub-categorization)
    query = f"""
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
        {extra_sql_filter}
    """
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        print(f"⚠️ No data found for category: {chart_title}")
        return

    # 2. 데이터 전처리 및 집계
    df['date'] = pd.to_datetime(df['date']).dt.normalize()
    
    # How: 'count'를 추가하여 해당 일자의 재고(수집된 상품 수) 계산
    daily_stats = df.groupby('date')['price'].agg(['mean', 'median', 'count']).reset_index()
    daily_stats = daily_stats.sort_values('date')

    # 3. 스타일 설정
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.set_facecolor('white')
    ax1.grid(axis='y', linestyle='--', alpha=0.3, color='gray')
    ax1.set_axisbelow(True)

    # 4. 플롯 그리기 (Dual Line for Price)
    ax1.plot(daily_stats['date'], daily_stats['mean'], 
            linestyle='--', linewidth=2, alpha=0.7,
            color=theme_color, label='Mean (Avg)')
            
    ax1.plot(daily_stats['date'], daily_stats['median'], 
            linestyle='-', marker='o', markersize=5, linewidth=2.5, 
            color=theme_color, label='Median')
    
    ax1.fill_between(daily_stats['date'], daily_stats['median'], 
                    color=theme_color, alpha=0.05)

    # 5. Volume Tracking (Bar Chart for Count)
    # How: twinx()를 사용하여 동일한 X축을 공유하는 두 번째 Y축 생성
    ax2 = ax1.twinx()
    ax2.bar(daily_stats['date'], daily_stats['count'], 
            color='gray', alpha=0.15, width=0.8, label='Item Count')
    
    # 차트 배경에 얕게 깔리도록 최대값의 3~4배로 Y축 한도 설정
    ax2.set_ylim(0, daily_stats['count'].max() * 3.5)
    ax2.set_ylabel('Available Item Count', fontsize=10, color='gray')

    # 6. Annotation (최신 값 표시)
    last_date = daily_stats['date'].iloc[-1]
    last_median = daily_stats['median'].iloc[-1]
    last_mean = daily_stats['mean'].iloc[-1]
    last_count = int(daily_stats['count'].iloc[-1])
    
    ax1.annotate(f'Median: ${last_median:,.0f}', 
                xy=(last_date, last_median), 
                xytext=(10, 0), textcoords='offset points',
                ha='left', va='center',
                fontsize=10, fontweight='bold', color=theme_color,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=theme_color, alpha=0.9))
    
    ax1.annotate(f'Mean: ${last_mean:,.0f}\nCount: {last_count}', 
                xy=(last_date, last_mean), 
                xytext=(10, -15), textcoords='offset points', 
                ha='left', va='top',
                fontsize=9, color='gray')

    # 7. 축 및 레이블 설정
    sns.despine(ax=ax1, left=True, bottom=False, right=False)
    sns.despine(ax=ax2, left=True, bottom=False, right=True)
    
    ax1.set_title(chart_title, fontsize=18, fontweight='bold', pad=20, loc='left')
    ax1.set_ylabel('Price (CAD)', fontsize=11, color='gray')
    
    # 범례 병합
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', frameon=False) 
    
    # Dynamic Range Calculation
    all_prices = pd.concat([daily_stats['mean'], daily_stats['median']])
    min_price = all_prices.min()
    max_price = all_prices.max()
    
    margin = (max_price - min_price) * 0.15 if max_price != min_price else 50
    y_bottom = max(0, min_price - margin)
    y_top = max_price + margin
    ax1.set_ylim(y_bottom, y_top)

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax1.tick_params(axis='x', rotation=0, labelsize=10)
    ax1.tick_params(axis='y', labelsize=10)

    plt.tight_layout()

    # 8. 저장
    if os.getenv('GITHUB_ACTIONS') == 'true':
        output_dir = "docs/images"
    else:
        output_dir = r"C:\Users\dkang\OneDrive\Desktop\D\tech-base\docs\images"
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ Chart generated: {output_path} | Last Count: {last_count}")

def update_markdown_timestamps(md_file_path):
    # (Existing logic remains unchanged)
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
    
    # How: 'sql_filter' 키를 추가하여 특정 키워드로 데이터를 분리
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
        # Split GPU into High-End and Mid-Range
        {
            'sql_name': 'gpu',      
            'title': 'High-End GPU Price (RTX 4080/4090, RX 7900)', 
            'filename': 'gpu_high_price_trend.png', 
            'color': '#1D4ED8', # Dark Blue
            'sql_filter': "AND (LOWER(name) LIKE '%4090%' OR LOWER(name) LIKE '%4080%' OR LOWER(name) LIKE '%7900%')"
        },
        {
            'sql_name': 'gpu',      
            'title': 'Mid-Range GPU Price (RTX 4060/4070, RX 7600/7700)', 
            'filename': 'gpu_mid_price_trend.png', 
            'color': '#3B82F6', # Light Blue
            'sql_filter': "AND (LOWER(name) LIKE '%4060%' OR LOWER(name) LIKE '%4070%' OR LOWER(name) LIKE '%7600%' OR LOWER(name) LIKE '%7700%')"
        },
        # Split Drones into Pro and Consumer
        {
            'sql_name': 'drone',      
            'title': 'Pro Drone Price (Inspire/Matrice)', 
            'filename': 'drone_pro_price_trend.png', 
            'color': '#B91C1C', # Dark Red
            'sql_filter': "AND (LOWER(name) LIKE '%inspire%' OR LOWER(name) LIKE '%matrice%' OR LOWER(name) LIKE '%mavic 3 pro%')"
        },
        {
            'sql_name': 'drone',      
            'title': 'Consumer Drone Price (Mini/Air)', 
            'filename': 'drone_consumer_price_trend.png', 
            'color': '#EF4444', # Light Red
            'sql_filter': "AND (LOWER(name) LIKE '%mini%' OR LOWER(name) LIKE '%air%')"
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