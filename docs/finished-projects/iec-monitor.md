# 🇨🇦 Canada IEC Working Holiday Monitor

An automation bot that detects Canada Working Holiday invitation rounds in real-time and sends notifications.

## 💡 Project Background
* **Why:** Canada Working Holiday invitations are sent out unexpectedly. Checking the official website manually is inefficient.
* **How:** I built a system that "sends a notification to my phone as soon as a change is detected."

## 🛠 Tech Stack
* **Language:** Python
* **Cloud:** GCP (Cloud Run, Firestore)
* **DevOps:** Docker, GitHub Actions
* **Notification:** Telegram API

## 🚀 Key Features
1.  **Automated Scraping:** Scans the official website status once per day (cycle optimized based on user feedback).
2.  **Change Detection:** Detects changes by comparing the hash values of the previous and current states.
3.  **Instant Alert:** Sends an immediate push notification via Telegram when a change is detected.

## 📈 Impact
* **Validation:** Shared on social media, achieving **40 Likes on LinkedIn**, confirming high interest from actual users.
* **Optimization:** Improved efficiency and reduced notification fatigue by adjusting the alert cycle from every 10 minutes to once per day.