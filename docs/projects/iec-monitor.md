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
1.  **Automated Scraping:** 10분 주기로 IEC 공식 웹사이트 상태 스캔.
2.  **Change Detection:** 이전 상태와 현재 상태를 해시값으로 비교하여 변경 감지.
3.  **Instant Alert:** 변경 감지 시 텔레그램으로 즉시 푸시 알림 전송.

## 📈 Impact
* 링크드인 게시물 **19 Likes** 달성 (검증된 아이디어).
* 워커(Worker) 프로세스를 최적화하여 타임아웃 문제 해결.