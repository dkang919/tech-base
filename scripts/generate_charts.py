import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import os
import re                  # 정규표현식 사용을 위해 추가
from datetime import datetime # 현재 시간 확인을 위해 추가

def create_category_chart(client, category_sql_name, chart_title, filename, theme_color):
    """
    Mean(평균)과 Median(중간값)을 동시에 시각화하여 데이터 분포 왜곡을 확인하는 차트 생성
    """
    
    # 1. SQL Query
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
    """
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        print(f"⚠️ No data found for category: {category_sql_name}")
        return

    # 2. 데이터 전처리 및 집계 (Aggregation)
    df['date'] = pd.to_datetime(df['date']).dt.normalize()
    
    # Why: 평균과 중간값을 동시에 계산하여 비교
    daily_stats = df.groupby('date')['price'].agg(['mean', 'median']).reset_index()
    daily_stats = daily_stats.sort_values('date')

    # 3. 스타일 설정
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('white')
    ax.grid(axis='y', linestyle='--', alpha=0.3, color='gray')
    ax.set_axisbelow(True)

    # 4. 플롯 그리기 (Dual Line)
    
    # Line 1: Mean (평균) - 점선, 보조적인 느낌
    ax.plot(daily_stats['date'], daily_stats['mean'], 
            linestyle='--', linewidth=2, alpha=0.7,
            color=theme_color, label='Mean (Avg)')
            
    # Line 2: Median (중간값) - 실선, 메인 데이터 느낌
    ax.plot(daily_stats['date'], daily_stats['median'], 
            linestyle='-', marker='o', markersize=5, linewidth=2.5, 
            color=theme_color, label='Median')
    
    # Fill: 시각적 안정감을 위해 Median 아래에 옅은 색 채우기
    ax.fill_between(daily_stats['date'], daily_stats['median'], 
                    color=theme_color, alpha=0.05)

    # 5. Annotation (최신 값 표시)
    last_date = daily_stats['date'].iloc[-1]
    last_median = daily_stats['median'].iloc[-1]
    last_mean = daily_stats['mean'].iloc[-1]
    
    # How: 두 텍스트가 겹치지 않도록 Median은 위쪽, Mean은 아래쪽(혹은 텍스트만) 배치
    
    # Median Annotation (Box Style)
    ax.annotate(f'Median: ${last_median:,.0f}', 
                xy=(last_date, last_median), 
                xytext=(10, 0), textcoords='offset points',
                ha='left', va='center',
                fontsize=10, fontweight='bold', color=theme_color,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=theme_color, alpha=0.9))
    
    # Mean Annotation (Simple Text)
    ax.annotate(f'Mean: ${last_mean:,.0f}', 
                xy=(last_date, last_mean), 
                xytext=(10, -15), textcoords='offset points', # 살짝 아래로 배치
                ha='left', va='top',
                fontsize=9, color='gray')

    # 6. 축 및 레이블 설정
    sns.despine(left=True, bottom=False)
    
    ax.set_title(chart_title, fontsize=18, fontweight='bold', pad=20, loc='left')
    ax.set_ylabel('Price (CAD)', fontsize=11, color='gray')
    ax.legend(loc='upper left', frameon=False) # 범례 추가
    
    # Dynamic Range Calculation (Mean과 Median 전체를 고려)
    all_prices = pd.concat([daily_stats['mean'], daily_stats['median']])
    min_price = all_prices.min()
    max_price = all_prices.max()
    
    margin = (max_price - min_price) * 0.15 if max_price != min_price else 50
    y_bottom = max(0, min_price - margin)
    y_top = max_price + margin
    
    ax.set_ylim(y_bottom, y_top)

    # 날짜 포맷
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xticks(rotation=0, fontsize=10)
    plt.yticks(fontsize=10)

    plt.tight_layout()

    # 7. 저장
    if os.getenv('GITHUB_ACTIONS') == 'true':
        output_dir = "docs/images"
    else:
        output_dir = r"C:\Users\dkang\OneDrive\Desktop\D\tech-base\docs\images"
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ Dual-Metric Chart generated: {output_path}")

    # (Optional) 디버깅용: 데이터가 겹치는지 콘솔에서 확인
    print(f"   Last Data - Mean: {last_mean:.1f}, Median: {last_median:.1f}")


def update_markdown_timestamps(md_file_path):
    """
    마크다운 파일 내의 이미지 링크 버전(?v=...)을 현재 시간으로 자동 갱신
    Why: 매번 수동으로 숫자를 바꾸는 번거로움을 없애고, 방문자가 항상 최신 차트를 보게 함.
    """
    try:
        # 1. 현재 시간 생성 (예: 202402021400)
        new_version = datetime.now().strftime("%Y%m%d%H%M")
        
        # 2. 파일 읽기
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 3. 정규표현식으로 교체 (Regex)
        # How: .png?v=뒤에 오는 숫자나 문자를 찾아서 현재 시간으로 바꿔치기
        # 패턴 설명: \.png\?v=([a-zA-Z0-9_]+) -> .png?v= 뒤에 붙은 기존 버전값 탐색
        # (상대 경로 ../images/ 등도 .png 확장자로 끝나므로 문제없이 동작함)
        new_content = re.sub(r'\.png\?v=[a-zA-Z0-9_]+', f'.png?v={new_version}', content)
        
        # 4. 변경사항이 있으면 저장
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
            'title': 'RAM Price: Mean vs Median', 
            'filename': 'ram_price_trend.png', 
            'color': '#10B981' # Green
        },
        {
            'sql_name': 'gpu',      
            'title': 'GPU Price: Mean vs Median', 
            'filename': 'gpu_price_trend.png', 
            'color': '#3B82F6' # Blue
        },
        {
            'sql_name': 'ssd',      
            'title': 'SSD Price: Mean vs Median', 
            'filename': 'ssd_price_trend.png', 
            'color': '#8B5CF6' # Purple
        },
        {
            'sql_name': 'motherboard',      
            'title': 'Motherboard Price: Mean vs Median', 
            'filename': 'motherboard_price_trend.png', 
            'color': '#F59E0B' # Orange
        },
        {
            'sql_name': 'drone',      
            'title': 'Drone Price: Mean vs Median', 
            'filename': 'drone_price_trend.png', 
            'color': '#EF4444' # Red
        }
    ]

    for t in targets:
        print(f"Processing {t['title']}...")
        create_category_chart(
            client=client,
            category_sql_name=t['sql_name'],
            chart_title=t['title'],
            filename=t['filename'],
            theme_color=t['color']
        )
    
    # [수정됨] 마크다운 파일 경로를 실제 프로젝트 구조에 맞게 변경
    print("Updating Markdown timestamps...")
    update_markdown_timestamps("docs/projects/ca-pc-parts-tracker.md")

if __name__ == "__main__":
    run_analysis()