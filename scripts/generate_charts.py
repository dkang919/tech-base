import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import os

# 이 파일은 scripts/ 안에 있으므로 한 단계 위가 레포 루트다.
# Why: 실행 위치나 OS에 상관없이 같은 곳에 저장/수정하기 위함.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def create_category_chart(client, category_sql_name, chart_title, filename, theme_color, extra_sql_filter=""):
    """
    Mean(좌측 Y축), Median(우측 Y축), Item Count(배경) 시각화
    라벨 및 축 겹침 방지 최적화 버전
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

    # 2. 데이터 전처리
    df['date'] = pd.to_datetime(df['date']).dt.normalize()
    daily_stats = df.groupby('date')['price'].agg(['mean', 'median', 'count']).reset_index()
    daily_stats = daily_stats.sort_values('date')

    # 3. 스타일 설정
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    
    fig, ax1 = plt.subplots(figsize=(11, 7)) # 가로 길이를 살짝 늘림
    ax1.set_facecolor('white')
    ax1.grid(axis='y', linestyle='--', alpha=0.2, color='gray')

    # 4. 좌측 축 (ax1): Mean & Item Count
    # Item Count (배경 막대)
    ax1_count = ax1.twinx() # 임시축으로 배경 막대 그리기 (Y축 텍스트는 숨김)
    ax1_count.bar(daily_stats['date'], daily_stats['count'], color='gray', alpha=0.08, width=0.8)
    ax1_count.set_ylim(0, daily_stats['count'].max() * 5)
    ax1_count.get_yaxis().set_visible(False) # 카운트 축 수치는 숨김

    # Mean Line
    lns1 = ax1.plot(daily_stats['date'], daily_stats['mean'], 
                    linestyle='--', linewidth=2, alpha=0.8,
                    color=theme_color, label='Mean (Left Axis)')
    ax1.set_ylabel('Mean Price (CAD)', fontsize=10, color=theme_color, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=theme_color)

    # 5. 우측 축 (ax2): Median
    ax2 = ax1.twinx()
    lns2 = ax2.plot(daily_stats['date'], daily_stats['median'], 
                    linestyle='-', marker='o', markersize=5, linewidth=2.5, 
                    color=theme_color, label='Median (Right Axis)')
    ax2.set_ylabel('Median Price (CAD)', fontsize=10, color=theme_color, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=theme_color)
    
    # Median 아래 채우기
    ax2.fill_between(daily_stats['date'], daily_stats['median'], color=theme_color, alpha=0.05)

    # 6. Annotation (상단 배치 및 겹침 방지)
    last_date = daily_stats['date'].iloc[-1]
    last_mean = daily_stats['mean'].iloc[-1]
    last_median = daily_stats['median'].iloc[-1]
    last_count = int(daily_stats['count'].iloc[-1])

    # Mean Label (왼쪽 상단 방향)
    ax1.annotate(f'Mean: ${last_mean:,.0f}\nCount: {last_count}', 
                xy=(last_date, last_mean), 
                xytext=(-5, 25), textcoords='offset points',
                ha='right', va='bottom', fontsize=9, color='gray',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.7))

    # Median Label (오른쪽 상단 방향)
    ax2.annotate(f'Median: ${last_median:,.0f}', 
                xy=(last_date, last_median), 
                xytext=(5, 25), textcoords='offset points',
                ha='left', va='bottom', fontsize=10, fontweight='bold', color=theme_color,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=theme_color, alpha=0.9))

    # 7. 레이아웃 및 여백 설정
    sns.despine(ax=ax1, top=True, right=False, left=False)
    ax1.set_title(chart_title, fontsize=16, fontweight='bold', pad=40, loc='center')

    # 범례 합치기 (ax1 상단 왼쪽에 배치)
    lns = lns1 + lns2
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc='upper left', frameon=False, fontsize=9)

    # Y축 범위 최적화 (라벨 공간을 위해 상단 마진 50% 추가)
    for ax, data in zip([ax1, ax2], [daily_stats['mean'], daily_stats['median']]):
        ymin, ymax = data.min(), data.max()
        diff = ymax - ymin if ymax != ymin else ymax * 0.1
        ax.set_ylim(max(0, ymin - diff * 0.2), ymax + diff * 0.6)

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xticks(rotation=0)
    plt.tight_layout()

    # 8. 저장
    # Why: 예전에는 로컬 경로를 절대경로로 박아뒀는데, 폴더를 옮기면 조용히
    #      엉뚱한 곳에 저장된다. 스크립트 위치에서 레포 루트를 찾아 쓴다.
    output_dir = os.path.join(REPO_ROOT, "docs", "images")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ 개선된 듀얼 축 차트 생성: {output_path}")

# run_analysis 내 targets는 이전과 동일하게 사용하면 됩니다.

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

if __name__ == "__main__":
    run_analysis()