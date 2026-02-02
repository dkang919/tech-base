import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import os

def create_category_chart(client, category_sql_name, chart_title, filename, theme_color):
    """
    특정 카테고리에 대한 데이터 조회 및 차트 생성 함수
    Why: 반복되는 로직(쿼리->가공->플롯->저장)을 함수로 묶어 코드 중복을 제거하고 유지보수성을 높임.
    """
    
    # 1. SQL: 동적 카테고리 적용
    # How: f-string을 사용하여 query 내의 category 값을 파라미터로 교체
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
    
    # 데이터가 없을 경우 예외 처리
    if df.empty:
        print(f"⚠️ No data found for category: {category_sql_name}")
        return

    # 2. 데이터 전처리
    df['date'] = pd.to_datetime(df['date']).dt.normalize()
    
    # 일별 평균 계산
    daily_median = df.groupby('date')['price'].median().reset_index()
    daily_median = daily_median.sort_values('date')

    # 3. 스타일 설정
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('white')
    ax.grid(axis='y', linestyle='--', alpha=0.3, color='gray')
    ax.set_axisbelow(True)

    # 4. 플롯 그리기 (파라미터로 받은 색상 적용)
    ax.plot(daily_median['date'], daily_median['price'], 
            marker='o', markersize=6, linewidth=2.5, 
            color=theme_color, label='Avg Price')
    
    ax.fill_between(daily_median['date'], daily_median['price'], 
                    color=theme_color, alpha=0.1)

    # 5. Annotation
    last_date = daily_median['date'].iloc[-1]
    last_price = daily_median['price'].iloc[-1]
    
    ax.annotate(f'Current: ${last_price:,.0f}', 
                xy=(last_date, last_price), 
                xytext=(0, 15), textcoords='offset points',
                ha='center', va='bottom',
                fontsize=11, fontweight='bold', color=theme_color,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=theme_color, alpha=0.9))

    # 6. 축 및 레이블 설정
    sns.despine(left=True, bottom=False)
    
    ax.set_title(chart_title, fontsize=18, fontweight='bold', pad=20, loc='left')
    ax.set_xlabel('')
    ax.set_ylabel('Avg Price (CAD)', fontsize=11, color='gray')
    
    # Dynamic Range Calculation
    min_price = daily_median['price'].min()
    max_price = daily_median['price'].max()
    
    # How: 가격대가 다른 GPU($1000+)와 SSD($100)를 모두 수용하기 위해 여백을 동적으로 계산
    margin = (max_price - min_price) * 0.1 if max_price != min_price else 50
    y_bottom = max(0, min_price - margin)
    y_top = max_price + margin
    
    ax.set_ylim(y_bottom, y_top)

    # 날짜 포맷
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xticks(rotation=0, fontsize=10)
    plt.yticks(fontsize=10)

    plt.tight_layout()

    # 7. 저장 경로 설정
    if os.getenv('GITHUB_ACTIONS') == 'true':
        output_dir = "docs/images"
    else:
        output_dir = r"C:\Users\dkang\OneDrive\Desktop\D\tech-base\docs\images"
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig) # 메모리 누수 방지를 위해 명시적으로 닫기
    print(f"✅ Clean Design Chart generated: {output_path}")


def run_analysis():
    client = bigquery.Client()
    
    # 설정 리스트 (Configuration)
    # Why: 나중에 카테고리가 추가되거나 색상을 변경할 때 로직을 건드리지 않고 이 리스트만 수정하면 됨.
    # 주의: DB에 저장된 실제 카테고리명('gpu', 'ssd')이 정확해야 합니다. 다를 경우 수정하세요.
    targets = [
        {
            'sql_name': 'memory', 
            'title': 'RAM (Memory) Price Trend', 
            'filename': 'ram_price_trend.png', 
            'color': '#10B981' # Green
        },
        {
            'sql_name': 'gpu',      # DB에 저장된 실제 카테고리 값 확인 필요 (예: 'video-card' 일 수도 있음)
            'title': 'GPU Price Trend', 
            'filename': 'gpu_price_trend.png', 
            'color': '#3B82F6' # Blue
        },
        {
            'sql_name': 'ssd',      # DB에 저장된 실제 카테고리 값 확인 필요 (예: 'storage' 일 수도 있음)
            'title': 'SSD Price Trend', 
            'filename': 'ssd_price_trend.png', 
            'color': '#8B5CF6' # Purple
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

if __name__ == "__main__":
    run_analysis()