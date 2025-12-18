# 🩺 MedChain

**MedChain** is a modular blockchain-based medical data management system designed to ensure the **integrity, transparency, and security** of healthcare data through cryptographic hashing and immutable record-keeping.

---

## 🎯 Purpose

MedChain is developed as an **academic and conceptual project** to demonstrate how blockchain principles can be applied as an **integrity layer** for sensitive medical data **without relying on public blockchains**.

---

## ✨ Key Features

* Modular local blockchain implementation
* Medical data integrity using cryptographic hashing (SHA-256)
* Immutable chain of records for tamper detection
* RESTful API for data input and testing
* Clear separation between **source of truth** (blockchain) and **data display layer**

---

## 🛠️ Technology Stack

* **Programming Language:** Python
* **Framework:** Flask
* **Cryptography:** SHA-256 hashing
* **Data Format:** JSON

---

## 📂 Project Structure

```
medchain/
├── app.py               # Flask API
├── blockchain.py        # Blockchain logic
├── storage.py           # Persistent storage
├── blockchain.json      # Blockchain data (auto-generated)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🧱 Block Structure

```json
{
  "block_id": 1,
  "patient_id": "PSN-001",
  "clinic_name": "Klinik Sehat Sentosa",
  "diagnosis": "Hipertensi",
  "treatment": "Amlodipine",
  "date": "2025-12-08 09:30:00",
  "doctor": "Dr. Andi",
  "prev_hash": null,
  "current_hash": "e21cbb90a1..."
}
```

---

## 🔌 API Endpoints

### 1️⃣ Add Medical Record

**POST** `/add_data`
Adds a new block to the local blockchain and synchronizes it with the cloud display.

**Request Body:**

```json
{
  "block_id": 1,
  "patient_id": "PSN-001",
  "clinic_name": "Klinik A",
  "diagnosis": "Hipertensi",
  "treatment": "Amlodipine",
  "date": "2025-12-08 09:30:00",
  "doctor": "Dr. Andi"
}
```

---

### 2️⃣ Get Blockchain

**GET** `/get_chain`
Returns the entire blockchain stored locally.

---

### 3️⃣ Verify Full Blockchain

**GET** `/verify_chain`
Verifies the integrity of the entire blockchain.

**Possible Results:**

* `Blockchain is valid`
* `Blockchain is tampered`

---

### 4️⃣ Verify Specific Block

**GET** `/verify_chain/<block_id>`
Verifies a specific block by validating its `prev_hash`.

---

### 5️⃣ Detect Cloud Tampering

**GET** `/detect_cloud_tampering`
Compares local blockchain data with cloud data (Google Sheets).

**Example Response:**

```json
{
  "status": "TAMPERED",
  "details": [
    {
      "block_id": 1,
      "field": "diagnosis",
      "local": "Hipertensi",
      "cloud": "Cancer"
    }
  ]
}
```

---

## 🩺 How It Works

1. Medical data is submitted through the REST API.
2. Each record is hashed and stored as a block.
3. Every new block references the previous block’s hash.
4. Any data modification can be detected through hash validation.

---

## 📜 License

This project is licensed under the **MIT License** and is intended for **educational and research purposes**.