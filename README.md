# Ghost Inventory  
### Privacy-Preserving Industrial Spare Parts Exchange

Ghost Inventory is an AI-powered local supply mesh that enables factories to securely discover and exchange excess industrial spare parts without exposing sensitive operational data.

---

## 🚨 Problem Statement

Manufacturing clusters face significant production delays due to unplanned machine downtime caused by the unavailability of critical spare parts.

To hedge against global supply chain uncertainty, factories overstock specialized components (valves, bearings, chips, fittings). These remain unused and depreciate in private warehouses.

At the same time, nearby factories experience costly production halts while waiting weeks for identical parts from overseas suppliers.

There is no secure, trusted mechanism to discover and exchange excess inventory between local manufacturers without revealing sensitive inventory data.

---

## 💡 Proposed Solution

Ghost Inventory introduces a privacy-first AI matching layer that:

- Indexes spare parts securely
- Performs semantic AI matching
- Dynamically prices parts based on urgency
- Hides seller identity until confirmation
- Enables confidential peer-to-peer industrial exchange

---

## 🧠 Key Features

### 1️⃣ Semantic AI Matching
Uses Sentence Transformers to match spare parts intelligently, even when queries are not exact text matches.

### 2️⃣ OCR-Based Part Identification
Extracts part details from uploaded images using EasyOCR.

### 3️⃣ Dynamic Downtime-Based Pricing
Adjusts suggested pricing based on urgency level.

### 4️⃣ Privacy-Preserving Transaction Flow
- Seller identity hidden during search
- Revealed only after buyer confirms transaction
- Secure inventory listing

---

## 🏗 System Architecture

**User Layer**
- Seller Portal
- Buyer Portal

**AI Processing Layer**
- OCR Engine
- Semantic Matching Engine
- Pricing Logic

**Database Layer**
- SQLite + SQLAlchemy ORM

**Transaction Layer**
- Confirm-deal API reveals seller only upon agreement

---

## 🛠 Tech Stack

- FastAPI
- SQLAlchemy
- SQLite
- SentenceTransformers
- Scikit-learn (Cosine Similarity)
- EasyOCR
- OpenCV
- Jinja2 Templates

---

## 🚀 How to Run

### 1️⃣ Install dependencies
