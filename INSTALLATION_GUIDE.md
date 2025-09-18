# دليل التثبيت والتشغيل - ExaPlay Control API

# Installation and Setup Guide - ExaPlay Control API

هذا الدليل يوضح خطوات تثبيت وتشغيل مشروع ExaPlay Control API على جهاز جديد بالكامل.

This guide explains the steps to install and run the ExaPlay Control API project on a completely new machine.

---

## 📋 المتطلبات الأساسية | System Requirements

### 1. نظام التشغيل | Operating System

- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 20.04+, CentOS 8+)

### 2. البرامج المطلوبة | Required Software

- Python 3.12 أو أحدث
- Node.js 18 أو أحدث
- Git
- Docker (اختياري | Optional)

---

## 🔧 خطوات التثبيت | Installation Steps

### الخطوة 1: تثبيت Python | Step 1: Install Python

#### على Windows | On Windows:

```powershell
# تحميل Python من الموقع الرسمي
# Download Python from official website
# https://www.python.org/downloads/

# أو استخدام Chocolatey
# Or using Chocolatey
choco install python

# التحقق من التثبيت
# Verify installation
python --version
pip --version
```

#### على macOS | On macOS:

```bash
# استخدام Homebrew
# Using Homebrew
brew install python@3.12

# التحقق من التثبيت
# Verify installation
python3 --version
pip3 --version
```

#### على Linux | On Linux:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-pip

# CentOS/RHEL
sudo dnf install python3.12 python3.12-pip

# التحقق من التثبيت
# Verify installation
python3 --version
pip3 --version
```

### الخطوة 2: تثبيت Node.js | Step 2: Install Node.js

#### على Windows | On Windows:

```powershell
# تحميل من الموقع الرسمي
# Download from official website
# https://nodejs.org/

# أو استخدام Chocolatey
# Or using Chocolatey
choco install nodejs

# التحقق من التثبيت
# Verify installation
node --version
npm --version
```

#### على macOS | On macOS:

```bash
# استخدام Homebrew
# Using Homebrew
brew install node

# التحقق من التثبيت
# Verify installation
node --version
npm --version
```

#### على Linux | On Linux:

```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# CentOS/RHEL
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo dnf install nodejs npm

# التحقق من التثبيت
# Verify installation
node --version
npm --version
```

### الخطوة 3: تثبيت Git | Step 3: Install Git

#### على Windows | On Windows:

```powershell
# تحميل من الموقع الرسمي
# Download from official website
# https://git-scm.com/download/win

# أو استخدام Chocolatey
# Or using Chocolatey
choco install git

# التحقق من التثبيت
# Verify installation
git --version
```

#### على macOS | On macOS:

```bash
# Git مثبت مسبقاً مع Xcode Command Line Tools
# Git comes pre-installed with Xcode Command Line Tools
xcode-select --install

# أو استخدام Homebrew
# Or using Homebrew
brew install git

# التحقق من التثبيت
# Verify installation
git --version
```

#### على Linux | On Linux:

```bash
# Ubuntu/Debian
sudo apt install git

# CentOS/RHEL
sudo dnf install git

# التحقق من التثبيت
# Verify installation
git --version
```

### الخطوة 4: استنساخ المشروع | Step 4: Clone the Project

```bash
# إنشاء مجلد للمشاريع
# Create projects directory
mkdir ~/projects
cd ~/projects

# استنساخ المشروع
# Clone the project
git clone [PROJECT_REPOSITORY_URL] exaplay-project
cd exaplay-project

# أو إذا كان لديك المشروع محلياً
# Or if you have the project locally
# نسخ ملفات المشروع إلى المجلد الجديد
# Copy project files to new directory
```

---

## 🐍 إعداد Backend (Python FastAPI) | Backend Setup

### الخطوة 5: إنشاء البيئة الافتراضية | Step 5: Create Virtual Environment

```bash
# الانتقال إلى مجلد المشروع
# Navigate to project directory
cd ~/projects/exaplay-project

# إنشاء البيئة الافتراضية
# Create virtual environment
python -m venv venv

# تفعيل البيئة الافتراضية
# Activate virtual environment

# على Windows | On Windows:
venv\Scripts\activate

# على macOS/Linux | On macOS/Linux:
source venv/bin/activate

# يجب أن ترى (venv) في بداية سطر الأوامر
# You should see (venv) at the beginning of command prompt
```

### الخطوة 6: تثبيت تبعيات Python | Step 6: Install Python Dependencies

```bash
# التأكد من أن البيئة الافتراضية مفعلة
# Make sure virtual environment is activated
# يجب أن ترى (venv) في بداية سطر الأوامر
# You should see (venv) at the beginning

# ترقية pip
# Upgrade pip
python -m pip install --upgrade pip

# تثبيت التبعيات من pyproject.toml
# Install dependencies from pyproject.toml
pip install -e .

# أو إذا لم يعمل الأمر السابق
# Or if the previous command doesn't work
pip install fastapi uvicorn python-osc httpx pydantic pydantic-settings structlog python-dotenv pytest

# التحقق من التثبيت
# Verify installation
python -c "import fastapi; print('FastAPI installed successfully')"
```

### الخطوة 7: إعداد متغيرات البيئة | Step 7: Setup Environment Variables

```bash
# إنشاء ملف .env
# Create .env file
touch .env

# أو على Windows
# Or on Windows
type nul > .env
```

افتح ملف `.env` وأضف المتغيرات التالية:
Open `.env` file and add the following variables:

```env
# إعدادات ExaPlay | ExaPlay Settings
EXAPLAY_HOST=192.168.1.174
EXAPLAY_TCP_PORT=7000

# مفتاح API (يجب أن يكون قوياً) | API Key (must be strong)
API_KEY=your-secure-api-key-minimum-32-characters-long-replace-this

# إعدادات OSC (اختيارية) | OSC Settings (Optional)
EXAPLAY_OSC_ENABLE=false
EXAPLAY_OSC_PREFIX=exaplay
EXAPLAY_OSC_LISTEN=0.0.0.0:8000

# إعدادات السجلات | Logging Settings
LOG_LEVEL=INFO
LOG_FORMAT=console

# إعدادات CORS | CORS Settings
CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8123
```

**مهم | Important:**

- استبدل `EXAPLAY_HOST` بعنوان IP الصحيح لخادم ExaPlay
- قم بتوليد مفتاح API قوي (32 حرف على الأقل)
- Replace `EXAPLAY_HOST` with the correct IP address of your ExaPlay server
- Generate a strong API key (at least 32 characters)

---

## ⚛️ إعداد Frontend (React) | Frontend Setup

### الخطوة 8: تثبيت تبعيات Node.js | Step 8: Install Node.js Dependencies

```bash
# الانتقال إلى مجلد Frontend
# Navigate to Frontend directory
cd exaplay-ui

# تثبيت التبعيات
# Install dependencies
npm install

# التحقق من التثبيت
# Verify installation
npm list react
```

---

## 🚀 تشغيل المشروع | Running the Project

### الطريقة 1: تشغيل يدوي | Method 1: Manual Run

#### تشغيل Backend | Start Backend

```bash
# الانتقال إلى المجلد الرئيسي
# Navigate to main directory
cd ~/projects/exaplay-project

# تفعيل البيئة الافتراضية
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# أو | or
venv\Scripts\activate     # Windows

# تشغيل الخادم
# Start the server
python start_api.py

# أو استخدام uvicorn مباشرة
# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### تشغيل Frontend (في terminal جديد) | Start Frontend (in new terminal)

```bash
# فتح terminal جديد
# Open new terminal
cd ~/projects/exaplay-project/exaplay-ui

# تشغيل خادم التطوير
# Start development server
npm run dev
```

### الطريقة 2: استخدام Docker | Method 2: Using Docker

```bash
# إنشاء ملف .env أولاً كما هو موضح أعلاه
# Create .env file first as shown above

# تشغيل باستخدام Docker Compose
# Run using Docker Compose
docker-compose up -d

# للتشغيل مع خادم وهمي للاختبار
# To run with mock server for testing
docker-compose --profile testing up

# عرض السجلات
# View logs
docker-compose logs -f exaplay-api
```

---

## ✅ التحقق من التشغيل | Verify Installation

### 1. فحص Backend | Check Backend

```bash
# فحص الصحة
# Health check
curl http://localhost:8000/healthz

# يجب أن ترى | You should see:
# {"status": "healthy"}

# فحص الإصدار
# Check version
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/version
```

### 2. فحص Frontend | Check Frontend

افتح المتصفح وانتقل إلى:
Open browser and navigate to:

- http://localhost:5173 (Vite development server)

### 3. فحص API Documentation | Check API Documentation

افتح المتصفح وانتقل إلى:
Open browser and navigate to:

- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

---

## 🐛 استكشاف الأخطاء | Troubleshooting

### مشاكل شائعة | Common Issues

#### 1. خطأ في اتصال Python | Python Connection Error

```bash
# التحقق من إصدار Python
# Check Python version
python --version

# يجب أن يكون 3.12 أو أحدث
# Should be 3.12 or newer

# إعادة إنشاء البيئة الافتراضية
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -e .
```

#### 2. خطأ في تثبيت تبعيات Node.js | Node.js Dependencies Error

```bash
# حذف node_modules وإعادة التثبيت
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# أو استخدام npm cache clean
# Or use npm cache clean
npm cache clean --force
npm install
```

#### 3. خطأ في الاتصال بـ ExaPlay | ExaPlay Connection Error

```bash
# فحص الاتصال
# Test connection
ping 192.168.1.174

# فحص المنفذ
# Test port
telnet 192.168.1.174 7000

# التحقق من إعدادات .env
# Check .env settings
cat .env
```

#### 4. خطأ في API Key | API Key Error

```bash
# التأكد من صحة API Key في .env
# Make sure API Key is correct in .env
grep API_KEY .env

# اختبار مع curl
# Test with curl
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/version
```

### سجلات مفيدة | Useful Logs

```bash
# عرض سجلات Backend
# View Backend logs
tail -f logs/app.log

# عرض سجلات Docker
# View Docker logs
docker-compose logs -f exaplay-api

# عرض سجلات مفصلة
# View detailed logs
LOG_LEVEL=DEBUG python start_api.py
```

---

## 📚 موارد إضافية | Additional Resources

### روابط مفيدة | Useful Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Docker Documentation](https://docs.docker.com/)

### أوامر مفيدة | Useful Commands

```bash
# إيقاف جميع العمليات
# Stop all processes
# اضغط Ctrl+C في كل terminal
# Press Ctrl+C in each terminal

# أو لـ Docker
# Or for Docker
docker-compose down

# عرض العمليات الجارية
# Show running processes
ps aux | grep python
ps aux | grep node

# إغلاق عملية معينة
# Kill specific process
kill -9 PID_NUMBER
```

---

## 🎉 تم التثبيت بنجاح! | Installation Complete!

بعد اتباع هذه الخطوات، يجب أن يكون لديك:
After following these steps, you should have:

✅ Python FastAPI Backend يعمل على المنفذ 8000
✅ React Frontend يعمل على المنفذ 5173  
✅ API Documentation متاحة على /docs
✅ جميع التبعيات مثبتة بشكل صحيح

✅ Python FastAPI Backend running on port 8000
✅ React Frontend running on port 5173
✅ API Documentation available at /docs  
✅ All dependencies installed correctly

### الخطوات التالية | Next Steps

1. قم بتخصيص إعدادات ExaPlay في ملف .env
2. اختبر الاتصال مع خادم ExaPlay الحقيقي
3. استكشف API Documentation في المتصفح
4. ابدأ في تطوير التطبيق حسب احتياجاتك

5. Customize ExaPlay settings in .env file
6. Test connection with real ExaPlay server
7. Explore API Documentation in browser
8. Start developing your application as needed

---

**💡 نصيحة | Tip:** احتفظ بهذا الملف للرجوع إليه لاحقاً أو لتثبيت المشروع على أجهزة أخرى.

**💡 Tip:** Keep this file for future reference or to install the project on other machines.
