import pandas as pd
from google.cloud import bigquery
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import os
import time  # 시간 추가를 위해 import

def run_analysis():
    client = bigquery.Client()
    
    # 1. SQL 조회
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
    
    # 2. 전처리
    df['date'] = pd.to_datetime(df['date']).dt.normalize()
    
    daily_avg = df.groupby('date')['price'].mean().reset_index()
    daily_avg = daily_avg.sort_values('date')

    # 3. 스타일 설정
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('white')
    ax.grid(axis='y', linestyle='--', alpha=0.3, color='gray')
    ax.set_axisbelow(True)

    # 4. 그리기
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

    # 6. 축 설정 (Dynamic Y-Axis + Debugging)
    sns.despine(left=True, bottom=False)
    ax.set_title('RAM (Memory) Price Trend', fontsize=18, fontweight='bold', pad=20, loc='left')
    ax.set_xlabel('')
    ax.set_ylabel('Avg Price (CAD)', fontsize=11, color='gray')
    
    # --- [여기가 핵심 수정 부분] ---
    if not daily_avg.empty:
        min_price = daily_avg['price'].min()
        max_price = daily_avg['price'].max()
        
        y_bottom = max(0, min_price - 100)
        y_top = max_price + 100
        
        ax.set_ylim(y_bottom, y_top)
        
        # [Debug] 실제로 계산된 값이 얼마인지 터미널에 출력해서 확인
        print(f"DEBUG: Min Price={min_price}, Max Price={max_price}")
        print(f"DEBUG: Setting Y-Limit to Bottom={y_bottom}, Top={y_top}")
    # ----------------------------

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xticks(rotation=0, fontsize=10)
    plt.yticks(fontsize=10)

    plt.tight_layout()

    # 7. 저장 (파일명 변경으로 캐시 회피)
    if os.getenv('GITHUB_ACTIONS') == 'true':
        output_dir = "docs/images"
    else:
        output_dir = r"C:\Users\dkang\OneDrive\Desktop\D\tech-base\docs\images"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 파일명에 _updated 를 붙여서 기존 파일과 구분
    output_path = os.path.join(output_dir, "ram_price_trend_updated.png")
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Chart saved to: {output_path}")

if __name__ == "__main__":
    run_analysis()