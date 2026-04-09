# 🔐 Eliptic Signer  
**Ed25519 Message Signing & Verification Tool for Radio Communications**

![License](https://img.shields.io/badge/license-MIT-green)  ![Python](https://img.shields.io/badge/python-3.9%2B-blue)  ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20MacOS-lightgrey)  ![Status](https://img.shields.io/badge/status-active-success)

---

## ✨ Overview

**Eliptic Signer** is a lightweight application designed to **sign and verify messages using Ed25519**, with a strong focus on **amateur radio communications and offline environments**.

It enables operators to **prove identity and message authenticity** over HF links (MeshFest, VARA, JS8Call, etc.) without using encryption.

---

## 🚀 Features

- ✍️ Sign messages with **Ed25519**
- ✅ Verify message authenticity
- 🔑 Generate public/private key pairs
- 📄 Export keys (PEM / Base64)
- 🧩 Simple GUI for Windows, Linux, MacOS and Android
- ⚡ Deterministic signatures
- 📡 Designed for radio environments:
  - VARA HF
  - JS8Call
  - MeshFest

---

## 📡 Real-World Use Cases

- ✔️ Authenticate in **Net Control Stations**
- ✔️ Prevent impersonation on Radio Comms links
- ✔️ Validate messages in emergency comms
- ✔️ Identity verification in decentralized networks
- ✔️ Mesh ↔ HF hybrid systems

### Example

```
MSG: 070426 START NET CONTROL EA1ABC
SIG: RnZ5ts8cFnPUwy9bkqmUuX2RZ4RTVF57r6jUdnzC1iD6boM1VXynW+vWWJa4ooJ2XhuhTdzriuF5OiEMjk19Cw==
```

→ Signed → Any station can verify authenticity using the public key and the Signature (SIG) of the message (MSG)

---

## 🔐 Why Ed25519?

- ⚡ Fast and efficient
- 🔒 Strong modern cryptography
- 📏 Compact signatures (64 bytes)
- 🔁 Deterministic (same message → same signature)

Perfect for **low-bandwidth radio links**.

---

## 🧱 Project Structure

```
eliptic-signer/
│
├── main.py
├── crypto/
│   └── crypto_manager.py
├── ui/
│   └── main_screen.py
├── storage.py
├── assets/
│   └── logo.ico
└── requirements.txt
```

---

## ⚙️ Installation Windows / Linux / MacOS

For Windows you can just download the last .exe on Release section: [Releases](https://github.com/QuixoteNetwork/eliptic-signer/releases)


### 1. Clone the repository

```bash
git clone https://github.com/youruser/eliptic-signer.git
cd eliptic-signer
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the App

```bash
python main.py
```

---

## 🔑 Key Formats

| Format   | Use Case |
|----------|----------|
| PEM      | Standard interoperability |
| Base64   | Compact for radio transmission |
| Raw      | Internal use |

---


## ⚠️ Legal Notice (Amateur Radio)

- ❌ Encryption is **not allowed** on most amateur radio bands  
- ✔️ Digital signatures **are allowed** (they do not hide content)  
- ✔️ This tool is intended for **authentication only**

---

## 🛠️ Roadmap

- [ ] Android version  
- [ ] Direct VARA / JS8Call integration
- [ ] MeshFest integration
- [ ] QR key exchange  
- [ ] Trusted contacts management  
- [ ] Automatic message signing  
  

---

## ❤️ Support the Project

If you find this project useful and want to support its development:

👉 **Ko-fi:** https://ko-fi.com/quixotenetwork  

Your support helps maintain and improve tools for the radio community 🙌

---

## 🤝 Contributing

Contributions are welcome!

- Open an issue for bugs or ideas  
- Submit a pull request  
- Help improve documentation  

