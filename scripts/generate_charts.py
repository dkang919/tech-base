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
    # df = df[df['price'] < 2000] # 이상치 제거
    
    # 일별 평균 계산
    daily_avg = df.groupby('date')['price'].mean().reset_index()
    daily_avg = daily_avg.sort_values('date')

    # 3. Modern Design Style 설정
    # 폰트 및 스타일 초기화
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    
    # 배경 및 그리드 설정
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('white')
    ax.grid(axis='y', linestyle='--', alpha=0.3, color='gray') # 가로줄만 은은하게
    ax.set_axisbelow(True) # 그리드가 데이터 뒤로 가게

    # 4. 플롯 그리기 (Line + Area)
    # 색상: 신뢰감을 주는 Tech Blue (#2563EB) 또는 Emerald Green (#10B981)
    # 여기서는 기존의 녹색 계열을 더 세련된 색으로 변경
    main_color = '#10B981' 
    
    ax.plot(daily_avg['date'], daily_avg['price'], 
            marker='o', markersize=6, linewidth=2.5, 
            color=main_color, label='Avg Price')
    
    # 하단 영역 채우기 (트렌드 강조)
    ax.fill_between(daily_avg['date'], daily_avg['price'], 
                    color=main_color, alpha=0.1)

    # 5. 최신 가격 강조 (Annotation)
    last_date = daily_avg['date'].iloc[-1]
    last_price = daily_avg['price'].iloc[-1]
    
    ax.annotate(f'Current: ${last_price:,.0f}', 
                xy=(last_date, last_price), 
                xytext=(0, 15), textcoords='offset points',
                ha='center', va='bottom',
                fontsize=11, fontweight='bold', color=main_color,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=main_color, alpha=0.9))

    # 6. 축 및 레이블 다듬기 (Chart Junk 제거)
    sns.despine(left=True, bottom=False) # 왼쪽, 위, 오른쪽 테두리 제거
    
    ax.set_title('RAM (Memory) Price Trend', fontsize=18, fontweight='bold', pad=20, loc='left')
    ax.set_xlabel('') # X축 라벨 생략 (날짜보면 아니까)
    ax.set_ylabel('Avg Price (CAD)', fontsize=11, color='gray')
    ax.set_ylim(500, 800)
    
    # 날짜 포맷
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.xticks(rotation=0, fontsize=10)
    plt.yticks(fontsize=10)

    plt.tight_layout()

    # 7. 저장
    if os.getenv('GITHUB_ACTIONS') == 'true':
        output_dir = "docs/images"
    else:
        # 본인 로컬 경로
        output_dir = r"C:\Users\dkang\OneDrive\Desktop\D\tech-base\docs\images"
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "ram_price_trend.png")
    
    # 해상도 높여서 저장 (Retina Display 대응)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Clean Design Chart generated: {output_path}")

if __name__ == "__main__":
    run_analysis()