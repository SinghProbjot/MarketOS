# MarketOS  

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white)
![Inno Setup](https://img.shields.io/badge/Inno%20Setup-6-007ACC?logo=windows&logoColor=white)

---

## What is MarketOS

MarketOS is a comprehensive hybrid Point of Sale (POS) and Inventory Management system engineered for small retail businesses, mini-markets, and grocery stores.

It bridges the gap between the reliability of offline desktop software and the flexibility of modern cloud solutions.

The system features a Hybrid Core architecture, allowing seamless operation offline using a local SQLite engine, with optional real-time synchronization to Google Firebase for remote management and data redundancy.

---

## Key Features

- **Hybrid Database Engine:** Local (Browser), Server (SQLite), and Cloud (Firestore) with smart fallback.
- **Professional POS Interface:** Touch-optimized checkout with barcode scanner support and dynamic weight input.
- **Advanced Inventory Control:** Real-time stock tracking, cost/margin analytics, dynamic category management.
- **Label Printing Hub:** Shelf labels + A4 barcode sheet generator.
- **Financial Intelligence:** Dashboard powered by Recharts for revenue, profit margins, weekly sales trends.
- **Cloud Migration Tool:** One-click upload of local dataset to Firebase.
- **OTA Auto-Update:** GitHub-based automatic update system.

---

## Tech Stack

- **Language:** Python 3.10+  
- **Frontend:** React 18 (Babel Standalone), Tailwind CSS, Recharts  
- **Backend:** Flask + SQLite / Firestore  
- **Wrapper:** pywebview  
- **Deployment:** Inno Setup Compiler 6  

---

## Installation

### 🔹 For End Users

1. Download the installer **MarketOS_Setup_v7.6.exe** from Releases.  
2. Run setup (Python environment auto-configured).  
3. Launch *MarketOS Pro* from the Desktop shortcut.

### 🔹 For Developers

```bash
git clone https://github.com/SinghProbjot/MarketOS.git
cd MarketOS

pip install -r requirements.txt
# Make sure: flask, flask-cors, pywebview, requests are included
