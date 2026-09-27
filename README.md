# 🎓 EduHub — Learning Management System

A modern, AI-powered LMS built with **Flask**, **Bootstrap 5**, **Socket.IO**, and **OpenAI**.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

- 👥 **Multi-role platform** — Admin · Teacher · Student
- 📚 **Course management** — Courses, lessons, video content
- 🤖 **AI Tutor** — ChatGPT-powered Q&A per course
- 📊 **Analytics** — Real-time dashboards with Chart.js
- 🏅 **Gamification** — Points, badges, leaderboard
- 📜 **PDF Certificates** — Auto-generated with QR codes
- 💳 **Stripe Payments** — Test mode ready
- 🔔 **Real-time notifications** — Socket.IO
- 💬 **Class chat rooms** — Live per-course chat
- 📧 **Email verification** — Flask-Mail
- 🌙 **4 theme modes** — Light · Dark · Neumorphic · High Contrast
- 🎨 **Premium animations** — Page transitions, morphing cards, custom cursor
- 🔒 **Security hardened** — CSRF, rate limiting, audit log, secure cookies

---

## 🚀 Live Demo

👉 **[View Live Demo](https://eduhub-lms-1.onrender.com)**

---

## 🧰 Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11 · Flask 3 · SQLAlchemy |
| Auth | Flask-Login · Werkzeug |
| Forms | Flask-WTF · WTForms |
| Real-time | Flask-SocketIO · eventlet |
| AI | OpenAI GPT-4o-mini |
| PDF | ReportLab · qrcode |
| Payments | Stripe |
| Email | Flask-Mail |
| Security | Flask-Limiter · Flask-Talisman |
| Frontend | Bootstrap 5.3 · Bootstrap Icons · Chart.js |
| Database | SQLite (dev) · PostgreSQL (prod) |
| Deploy | Render · Gunicorn |

---

## 🖥️ Run Locally

```bash
git clone https://github.com/<your-username>/eduhub-lms.git
cd eduhub-lms
python -m venv .venv
.venv\Scripts\activate           # Windows
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Open **http://127.0.0.1:5000** — first registered user becomes **admin** 👑.

---

## 🌐 Deploy to Render

1. Push code to GitHub
2. Go to [render.com](https://eduhub-lms-1.onrender.com) → **New → Blueprint**
3. Select your repo → Render reads `render.yaml` → click **Apply**
4. Wait ~4 minutes → done 🚀

---

## 🎯 Roles

| Role | Capabilities |
|---|---|
| 👑 **Admin** | Manage users, courses, view audit log, platform stats |
| 👨‍🏫 **Teacher** | Create courses, add lessons, build quizzes, view analytics |
| 🎓 **Student** | Enroll, learn, take quizzes, earn certificates |

---

## 🔐 Security

- ✅ PBKDF2 password hashing
- ✅ CSRF protection on all forms
- ✅ Rate limiting (login, register, AI)
- ✅ Account lockout after 5 failed attempts
- ✅ Content Security Policy headers
- ✅ Secure HttpOnly SameSite cookies
- ✅ MIME-type verification on uploads
- ✅ Audit logging
- ✅ Role-based access control

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

## 👨‍💻 Author

**GUYO DIKA**
Lecturer at Werabe University
🌐 [Portfolio](https://github.com/guyodika6891-lgtm) · 📧 [guyodika6891@gmail.com](mailto:guyodika6891@gmail.com)
