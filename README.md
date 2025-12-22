# 🩺 MedChain

**MedChain** is a modular, local blockchain system that acts as an **integrity layer** for medical records.  
In this project, the **local blockchain is the source of truth**, while **Google Sheets is used as a cloud display** and as a place to **simulate cloud-side manipulation (tampering)**.

---

## 🎯 Project Context (Course Assignment)

**Course:** Cryptography & Blockchain  
**Topic:** Modular Blockchain as an Integrity Layer for Cloud Data  
**Case:** Medical ledger integrity across clinics

**Architecture:**

```
Postman
  ↓
Flask API (Python)
  ↓
Local Modular Blockchain (Source of Truth)
  ↓
Google Apps Script (Web API)
  ↓
Google Sheets (Cloud Display + Tampering Simulation)
```

---

## ✨ Key Features

- Local blockchain ledger with **SHA-256 hashing**
- Each block contains a **prev_hash** that links to the previous block
- **Persistent storage** using `blockchain.json` (data remains after restart)
- REST API for testing using **Postman**
- Cloud synchronization to **Google Sheets** via **Google Apps Script**
- Tampering detection:
  - Detects **data differences** between local chain vs cloud chain
  - Detects **hash inconsistencies** if cloud data is edited manually

---

## 🛠️ Technology Stack

- **Language:** Python
- **API Framework:** Flask
- **Hashing:** SHA-256 (`hashlib`)
- **Testing:** Postman
- **Cloud Display:** Google Sheets
- **Sync Layer:** Google Apps Script

---

## 📂 Project Structure

```
medchain/
├── app.py               # Flask API (endpoints + cloud tampering detection)
├── blockchain.py        # Blockchain logic (hashing, add_block, verify_chain)
├── storage.py           # Persistent storage (load/save blockchain.json)
├── blockchain.json      # Local blockchain data (auto-generated / persistent)
├── requirements.txt
├── .gitignore
└── README.md
```

> Note: `blockchain.json` is generated/updated automatically when you call `POST /add_data`.

---

## ⚙️ Installation & Setup

### 1) Clone Repository

```bash
git clone https://github.com/Erlemico/MedChain.git
cd MedChain
```

### 2) Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 3) Install Dependencies

```bash
pip install -r requirements.txt
```

### 4) Run the Application

```bash
python app.py
```

Flask will run locally (usually on `http://127.0.0.1:5000`).

---

## 🧱 Block Structure

Each block is stored in a nested structure with a `data` object. The `current_hash` is computed from:

- `block_id`
- `timestamp`
- `data` (patient record fields)
- `prev_hash`

Example:

```json
{
  "block_id": 1,
  "timestamp": "2025-12-22T04:23:30Z",
  "data": {
    "patient_id": "PSN-001",
    "clinic_name": "Clinic A",
    "diagnosis": "Flu",
    "treatment": "Amoxicillin",
    "date": "2025-12-11 10:00:00",
    "doctor": "Dr. John"
  },
  "prev_hash": null,
  "current_hash": "93316362b5c823fc0f90d2a82443fbdd432449781fc3869169b90d4fb999513f"
}
```

---

## 🔌 API Endpoints

### 1) POST `/add_data`

Adds a new medical record as a block into the **local blockchain** and sends it to **Google Sheets** (cloud display).

✅ `block_id` and `timestamp` are generated automatically by the API.

**Request Body:**
```json
{
  "patient_id": "PSN-001",
  "clinic_name": "Clinic A",
  "diagnosis": "Flu",
  "treatment": "Amoxicillin",
  "date": "2025-12-11 10:00:00",
  "doctor": "Dr. John"
}
```

**Response (example):**
```json
{
  "status": "success",
  "block": {
    "block_id": 1,
    "timestamp": "2025-12-22T04:23:30Z",
    "data": {
      "patient_id": "PSN-001",
      "clinic_name": "Clinic A",
      "diagnosis": "Flu",
      "treatment": "Amoxicillin",
      "date": "2025-12-11 10:00:00",
      "doctor": "Dr. John"
    },
    "prev_hash": null,
    "current_hash": "93316362b5c823fc0f90d2a82443fbdd432449781fc3869169b90d4fb999513f"
  },
  "cloud": {
    "status_code": 200,
    "ok": true,
    "response": {
      "status": "success",
      "message": "Block stored",
      "block_id": 1
    }
  }
}
```

---

### 2) GET `/get_chain`

Returns the full local blockchain (source of truth).

**Response:**
```json
{
  "length": 4,
  "chain": [ ... ]
}
```

---

### 3) GET `/verify_chain`

Verifies the integrity of the **local blockchain**:
- Recomputes each block hash and compares with `current_hash`
- Validates linkage (`prev_hash` must match previous `current_hash`)

**Response (valid):**
```json
{
  "valid": true,
  "message": "Blockchain is valid!"
}
```

**Response (tampered):**
```json
{
  "valid": false,
  "message": "Hash mismatch at block_id=2 (index 1)"
}
```

---

### 4) GET `/verify_chain/<block_id>`

Verifies the chain integrity **up to a specific block**.

Example:
```
GET /verify_chain/3
```

---

### 5) GET `/detect_cloud_tampering`

Compares the **local blockchain** (source of truth) against the **cloud chain** retrieved from Google Sheets.

Detects:
1) **Content difference** (local vs cloud)  
2) **Cloud hash mismatch** (cloud data edited but hash not updated)  
3) **Different chain length**

**Example Response (tampering detected):**
```json
{
  "local": {
    "valid": true,
    "message": "Blockchain is valid!",
    "length": 4,
    "last_hash": "52a8827186ee3687f0e2f32d1d95102039ef3ea466107222114fd6f83e98811f"
  },
  "cloud": {
    "length": 4,
    "last_hash": "52a8827186ee3687f0e2f32d1d95102039ef3ea466107222114fd6f83e98811f"
  },
  "tampering_detected": true,
  "divergence_index": 1,
  "cloud_hash_mismatch": true,
  "diff_sample": {
    "diagnosis": {
      "local": "Suspected Pneumonia",
      "cloud": "Cancer"
    }
  },
  "note": null
}
```

---

## 🧪 Required Test Flow (Matches the Assignment)

### Step 1 — Input 4 Blocks (Postman)

Send `POST /add_data` **4 times** to create:
1. Initial checkup (Clinic A)
2. Referral (Clinic A → Clinic B)
3. Follow-up treatment (Clinic B)
4. Control / condition update (Clinic B)

### Step 2 — Verify Local Blockchain

Run:
```
GET /verify_chain
```
Expected: `valid: true`

### Step 3 — Simulate Cloud Tampering

Manually edit a value in **Google Sheets** (example: change `diagnosis` in block 2 from `Suspected Pneumonia` to `Cancer`).

### Step 4 — Detect Tampering

Run:
```
GET /detect_cloud_tampering
```
Expected:
- `tampering_detected: true`
- `diff_sample` shows the modified field
- `cloud_hash_mismatch: true`

---

## 📝 Notes

- The **local blockchain** is the integrity layer (source of truth).
- The **cloud (Google Sheets)** is intentionally vulnerable and used to simulate tampering.
- If you manually edit cloud data, the stored `current_hash` in the sheet will not automatically update, which is the expected behavior for this assignment demo.

---

## 📜 License

This project is licensed under the MIT License and is intended for educational and research purposes.
