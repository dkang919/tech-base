import os
import json
from datetime import datetime

# --- 설정 ---
BASE_DIR = os.getcwd()
# 데이터 및 이미지 경로 (docs/taste/ 기준)
JSON_PATH = os.path.join(BASE_DIR, "docs", "taste", "food_log.json")
MD_PATH = os.path.join(BASE_DIR, "docs", "taste", "cooking.md")
IMG_DIR_ABS = os.path.join(BASE_DIR, "docs", "taste", "images", "food")
IMG_DIR_REL = "images/food" # 마크다운에서 참조할 상대 경로

def load_data():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def scan_new_images(current_data):
    """폴더를 스캔해서 JSON에 없는 이미지가 있으면 추가합니다."""
    existing_files = {item['filename'] for item in current_data}
    new_entries = []
    
    if not os.path.exists(IMG_DIR_ABS):
        print(f"Error: 이미지 폴더가 없습니다 -> {IMG_DIR_ABS}")
        return []

    # 이미지 파일 스캔
    files = sorted([f for f in os.listdir(IMG_DIR_ABS) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
    
    for f in files:
        if f not in existing_files:
            # 날짜 파싱 (파일명 20251225... 기준)
            date_str = "Unknown"
            try:
                date_part = f.split('_')[0]
                if len(date_part) == 8 and date_part.isdigit():
                    date_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]}"
            except:
                pass
            
            # 새 데이터 구조 생성
            new_entries.append({
                "id": f, # 고유 ID로 파일명 사용
                "date": date_str,
                "filename": f,
                "title": "",     # 사용자가 JSON에서 직접 입력
                "comment": "",   # 사용자가 JSON에서 직접 입력
                "tags": []       # 확장성을 위한 태그
            })
    
    if new_entries:
        print(f"[{len(new_entries)}개]의 새 이미지를 발견하여 JSON에 추가합니다.")
        # 날짜순 정렬을 위해 합치고 다시 정렬
        updated_data = current_data + new_entries
        updated_data.sort(key=lambda x: x['filename']) # 파일명(날짜) 순 정렬
        return updated_data
    
    return current_data

def generate_markdown(data):
    """JSON 데이터를 기반으로 마크다운 파일을 생성합니다 (디자인 개선됨)."""
    
    # 1. 헤더 작성
    content = "# Algorithm of Taste - Cooking Log\n\n"
    content += "데이터 기반으로 자동 생성된 요리 기록입니다.\n\n"
    content += "---\n\n"
    
    # 2. 최신순 정렬 (날짜 내림차순)
    # 날짜가 같으면 파일명으로 2차 정렬
    sorted_data = sorted(data, key=lambda x: (x.get('date', ''), x.get('filename', '')), reverse=True)

    for item in sorted_data:
        date = item.get('date', 'Unknown Date')
        title = item.get('title', 'Untitled')
        comment = item.get('comment', '')
        filename = item['filename']
        tags = item.get('tags', [])
        
        # --- 마크다운 디자인 영역 ---
        
        # 제목 및 날짜 (### 2026-01-21 : 요리이름)
        content += f"### 📅 {date} : {title}\n\n"
        
        # 이미지
        content += f"![{title}]({IMG_DIR_REL}/{filename})\n\n"
        
        # 코멘트 (인용구 스타일)
        if comment:
            content += f"> 📝 **Note**: {comment}\n\n"
        
        # 태그 (인라인 코드 스타일)
        if tags:
            tag_str = " ".join([f"`#{t}`" for t in tags])
            content += f"**Tags**: {tag_str}\n\n"
            
        content += "<br>\n\n---\n\n" # 여백 추가 및 구분선

    # 파일 쓰기
    with open(MD_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Markdown 생성 완료: {MD_PATH}")

def save_json(data):
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    # 1. 기존 데이터 로드
    data = load_data()
    
    # 2. 새 이미지 스캔 및 데이터 병합
    updated_data = scan_new_images(data)
    
    # 3. 변경사항 있으면 JSON 저장
    if len(updated_data) != len(data) or not os.path.exists(JSON_PATH):
        save_json(updated_data)
        print("JSON 파일이 업데이트되었습니다. 내용을 채워주세요.")
    
    # 4. 마크다운 생성 (항상 수행)
    generate_markdown(updated_data)