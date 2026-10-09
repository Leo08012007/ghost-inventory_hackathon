# 👻 Ghost Inventory
### AI-Assisted Industrial Spare Parts Exchange Platform

**Discover unused inventory. Find the right spare part. Reduce industrial downtime.**

Ghost Inventory is a trust-oriented industrial spare parts exchange platform designed to connect businesses that need spare parts with suppliers who have available or unused inventory. It aims to simplify spare-part discovery through image-assisted identification, intelligent matching, urgency-aware price suggestions, geographical proximity and supplier verification.

Built as a hackathon project, Ghost Inventory explores how technology can help businesses reuse existing inventory, improve procurement efficiency and reduce unnecessary purchases.

---

## 🚨 Problem Statement

Industrial businesses often struggle to find compatible spare parts when machinery breaks down or maintenance is required.

Common challenges include:

- Difficulty discovering unused or surplus inventory across suppliers.
- Delays in locating compatible components.
- Limited visibility into supplier reliability and product availability.
- Manual searching through part names, model numbers and product catalogues.
- Increased operational costs caused by procurement delays and machine downtime.
- Unused inventory remaining idle while other businesses need the same components.

## 💡 Our Solution

Ghost Inventory provides a digital marketplace where buyers can search for industrial spare parts and suppliers can list available inventory.

The platform aims to make discovery more efficient through:

- **Image-assisted part identification:** Extract text from uploaded product images using OCR.
- **Inventory matching:** Match buyer requirements against available part listings.
- **Urgency-aware pricing:** Calculate transparent suggested prices using a configurable rule-based formula.
- **Location-aware discovery:** Support proximity-based supplier ranking where location data is available.
- **Supplier trust:** Provide a workflow for seller verification and product review.
- **Transaction management:** Support deal confirmation between buyers and suppliers.
- **Ratings and reviews:** Help buyers assess supplier history when genuine transaction-linked reviews are available.

---

## ✨ Key Features

### 🔍 Intelligent Inventory Search
- Search by part name and product details.
- Match buyer queries against inventory listings.
- Support for extending matching with semantic embeddings.
- Filter relevant products before applying distance and delivery preferences.

### 📷 OCR-Based Product Identification
- Upload an image of a spare part or its label.
- Extract text using EasyOCR.
- Review extracted text and use it to assist inventory listing.

### 💰 Urgency-Based Suggested Pricing
The current baseline pricing approach uses a configurable formula:

\[
P_{\text{suggested}}=P_{\text{base}}+(U\times R)
\]

Where:
- \(P_{\text{base}}\) = listed base price.
- \(U\) = urgency level.
- \(R\) = configured urgency rate.

This is a rule-based pricing mechanism, not a trained machine-learning model.

### 📍 Location-Aware Supplier Discovery
The platform is designed to consider supplier proximity and delivery constraints when ranking suitable listings. Haversine-based distance calculation can be used to estimate straight-line geographical distance when implemented and configured.

### 🛡️ Seller and Product Trust
- Seller registration and verification workflow.
- Separate seller and product verification statuses.
- Verification badges based on backend status.
- Admin review of submitted evidence.
- Ratings and reviews linked to completed transactions.

Verification status must reflect actual checks. Demo accounts and seeded sample records should be clearly identified as demo data.

### 🤝 Deal Confirmation
- View matching inventory.
- Select a suitable listing.
- Confirm interest in a transaction.
- Extend the workflow to include stock confirmation and transaction status tracking.

---

## 🏗️ System Architecture

```text
             BUYER / SELLER
                   |
                   v
          FastAPI Application
                   |
       +-----------+-----------+
       |           |           |
       v           v           v
   Inventory     OCR &       User and
   Management   Matching     Verification
       |           |           |
       +-----------+-----------+
                   |
                   v
          SQLAlchemy ORM
                   |
                   v
              Database
                   |
                   v
       Search, Pricing & Deals
```

The application uses modular FastAPI routers for authentication, administration, buyer operations, seller operations, transactions and reviews.

---

## 🧰 Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Database access | SQLAlchemy ORM |
| Database | Configured SQLAlchemy-supported database |
| Frontend | HTML, CSS, JavaScript |
| Templates | Jinja2 |
| Image processing | OpenCV, NumPy |
| OCR | EasyOCR |
| Search matching | Existing matching module; verify the exact algorithm in source |
| API documentation | FastAPI Swagger UI |
| Server | Uvicorn |
| Version control | Git and GitHub |

---

## 🧠 AI and Machine Learning Roadmap

Ghost Inventory is designed to support further AI enhancements.

| Capability | Purpose | Status |
|---|---|---|
| EasyOCR | Extract text from part images | Integrated in backend |
| Urgency-based pricing | Calculate suggested prices | Rule-based baseline |
| Semantic embeddings | Match differently worded part descriptions | Enhancement; confirm implementation |
| Haversine distance | Estimate buyer–seller distance | Requires implementation verification |
| Random Forest Regressor | Predict prices from historical transactions | Planned |
| LLM procurement assistant | Convert natural-language requirements into search filters | Planned |
| RAG | Retrieve technical specifications from product documents | Planned |

A machine-learning price predictor will require suitable historical transaction data, model training and evaluation before its predictions can be considered reliable.

---

## 🌍 Sustainability Impact

Ghost Inventory aims to support more efficient use of existing industrial resources.

Potential contributions include:

- **SDG 9 — Industry, Innovation and Infrastructure:** Improve industrial procurement and resource accessibility.
- **SDG 12 — Responsible Consumption and Production:** Encourage reuse of suitable surplus inventory.
- **SDG 13 — Climate Action:** Potentially avoid some unnecessary production and transportation, subject to measurable environmental impact.

These are intended contributions. Actual impact must be evaluated using real usage and environmental data.

---

## 🚀 Getting Started

### Prerequisites

- Python installed.
- Git installed.
- A terminal such as PowerShell or a compatible command shell.

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd ghost_inventory
```

Replace the placeholder with your actual GitHub repository URL.

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

If the repository includes a `requirements.txt` file:

```bash
python -m pip install -r requirements.txt
```

Ensure the dependency file includes the packages required by your actual application, including FastAPI, Uvicorn, SQLAlchemy, Jinja2, EasyOCR, OpenCV, NumPy and the configured database driver.

### 4. Configure environment variables

Create a local `.env` file if required by your application. Configure database credentials, secret keys and other settings according to your implementation.

Do not commit real passwords, API keys, government ID documents or production secrets.

### 5. Run the application

From the project root:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
```

### 6. Open the application

- **Web interface:** http://127.0.0.1:8001/
- **API documentation:** http://127.0.0.1:8001/docs
- **Health check:** http://127.0.0.1:8001/health

The database initialization and migration behavior depend on the existing project configuration.

---

## 📁 Project Structure

```text
ghost_inventory/
├── backend/
│   ├── ai_modules/
│   │   ├── matcher.py
│   │   └── ocr.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── buyer.py
│   │   ├── seller.py
│   │   ├── transactions.py
│   │   └── reviews.py
│   ├── templates/
│   │   └── index.html
│   ├── database.py
│   ├── main.py
│   └── models.py
├── uploads/
│   └── products/
├── requirements.txt
├── .gitignore
└── README.md
```

This is the intended structure based on the application's current modular organization. Check the actual repository before publishing, as some files or directories may differ.

---

## 🔐 Security Considerations

- Keep uploaded verification documents private.
- Restrict administrative actions to authorized users.
- Validate uploaded file types and sizes.
- Use secure password hashing and session management.
- Validate inventory, pricing and transaction inputs on the backend.
- Do not expose sensitive business registration details to unauthorized users.
- Clearly distinguish demo verification from real-world verification.

---

## 🧪 Testing

Before presenting or deploying the application, verify:

- Application startup and database initialization.
- Seller registration and authentication.
- Product listing and image upload.
- OCR extraction.
- Search relevance and inventory filtering.
- Pricing calculations.
- Verification permissions.
- Transaction confirmation and persistence.
- API behavior through Swagger UI.

---

## 🔮 Future Enhancements

- Train and evaluate an ML-based price prediction model.
- Improve semantic matching using sentence embeddings.
- Add an LLM-powered natural-language procurement assistant.
- Introduce RAG over manufacturer datasheets and technical manuals.
- Improve geographical ranking and delivery estimation.
- Add supplier analytics and demand forecasting.
- Integrate logistics and transaction tracking.
- Measure inventory reuse and sustainability outcomes.

---

## 🏆 Hackathon Project

Ghost Inventory explores how an intelligent, trust-oriented exchange network can help businesses discover available industrial spare parts more efficiently.

**Our vision:** Make existing industrial inventory easier to discover, safer to exchange and more useful to the businesses that need it.

*Built as a hackathon prototype. Features and integrations should be considered implemented only where supported by the actual source code.*
