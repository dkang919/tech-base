# 🇨🇦 Canada IEC Working Holiday Monitor

캐나다 워킹홀리데이 인비테이션 발송 여부를 실시간으로 감지하고 알림을 보내는 자동화 봇입니다.

## 💡 Project Background
캐나다 워홀 인비테이션은 불시에 발송되는데, 매번 웹사이트에 들어가서 확인하는 것이 비효율적이라 판단했습니다. 이를 해결하기 위해 **"변화가 감지되면 내 폰으로 알림이 오는"** 시스템을 구축했습니다.

## 🛠 Tech Stack
* **Language:** Python
* **Cloud:** GCP (Cloud Run, Firestore)
* **DevOps:** Docker, GitHub Actions
* **Notification:** Telegram API

## 🚀 Key Features
1.  **Automated Scraping:** 하루 1회 공식 웹사이트 상태 스캔 (사용자 피드백 반영하여 주기 최적화). # [수정]
2.  **Change Detection:** 이전 상태와 현재 상태를 해시값으로 비교하여 변경 감지.
3.  **Instant Alert:** 변경 감지 시 텔레그램으로 즉시 푸시 알림 전송.

## 📈 Impact
* 링크드인 게시물 **40 Likes** 달성 (실제 사용자들의 높은 관심 확인). # [수정]
* 알림 주기를 10분에서 1일 1회로 조정하여 알림 피로도 감소 및 효율성 증대. # [추가]