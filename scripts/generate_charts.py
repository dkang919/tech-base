import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import os

def run_analysis():
    client = bigquery.Client()
    
    # 1. SQL: 데이터 조회
    query = """
    SELECT 
        date,
        COALESCE(
            SAFE_CAST(REPLACE(REPLACE(sale_price, '$', ''), ',', '') AS FLOAT64), 
            SAFE_CAST(REPLACE(REPLACE(original_price, '$', ''), ',', '') AS FLOAT64)
        ) AS price
    FROM 
        `cc-auto-scaper.cc_data.products`
    WHERE 
        category = 'memory'
        AND date IS NOT NULL
    """
    
    df = client.query(query).to_dataframe()
    
    # 2. 데이터 전처리
    df['date'] = pd.to_datetime(df['date']).dt.normalize()
    
    # 일별 평균 계산
    daily_avg = df.groupby('date')['price'].mean().reset_index()
    daily_avg = daily_avg.sort_values('date')

    # 3. 스타일 설정
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('white')
    ax.grid(axis='y', linestyle='--', alpha=0.3, color='gray')
    ax.set_axisbelow(True)

    # 4. 플롯 그리기
    main_color = '#10B981' 
    
    ax.plot(daily_avg['date'], daily_avg['price'], 
            marker='o', markersize=6, linewidth=2.5, 
            color=main_color, label='Avg Price')
    
    ax.fill_between(daily_avg['date'], daily_avg['price'], 
                    color=main_color, alpha=0.1)

    # 5. Annotation
    if not daily_avg.empty:
        last_date = daily_avg['date'].iloc[-1]
        last_price = daily_avg['price'].iloc[-1]
        
        ax.annotate(f'Current: ${last_price:,.0f}', 
                    xy=(last_date, last_price), 
                    xytext=(0, 15), textcoords='offset points',
                    ha='center', va='bottom',
                    fontsize=11, fontweight='bold', color=main_color,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=main_color, alpha=0.9))

    # 6. 축 및 레이블 설정 (Dynamic Y-Axis 적용됨)
    sns.despine(left=True, bottom=False)
    
    ax.set_title('RAM (Memory) Price Trend', fontsize=18, fontweight='bold', pad=20, loc='left')
    ax.set_xlabel('')
    ax.set_ylabel('Avg Price (CAD)', fontsize=11, color='gray')
    
    # Dynamic Range Calculation
    if not daily_avg.empty:
        min_price = daily_avg['price'].min()
        max_price = daily_avg['price'].max()
        
        y_bottom = max(0, min_price - 100)
        y_top = max_price + 100
        
        ax.set_ylim(y_bottom, y_top)

    # 날짜 포맷
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xticks(rotation=0, fontsize=10)
    plt.yticks(fontsize=10)

    plt.tight_layout()

    # 7. 저장 (원래 파일명으로 복구)
    if os.getenv('GITHUB_ACTIONS') == 'true':
        output_dir = "docs/images"
    else:
        output_dir = r"C:\Users\dkang\OneDrive\Desktop\D\tech-base\docs\images"
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "ram_price_trend.png")
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Clean Design Chart generated: {output_path}")

if __name__ == "__main__":
    run_analysis()