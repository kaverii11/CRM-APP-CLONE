# 🚀 Customer Relationship Management (CRM) System v1.0

![Build Status](https://img.shields.io/badge/Status-Completed-success)
![Team](https://img.shields.io/badge/Team-Kryptonite-blueviolet)
![Version](https://img.shields.io/badge/Version-1.0-blue)
![Stack](https://img.shields.io/badge/Stack-MERN%20%2F%20Spring-green)

> **A robust, secure, and scalable CRM platform designed to provide a 360° customer view, ensuring GDPR compliance and 99.9% uptime.**

---

## 📖 Table of Contents
- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-tech-stack)
---

## 📄 Project Overview

This project is a comprehensive **Customer Relationship Management (CRM) System** developed by **Team Kryptonite**. The system is designed to streamline business processes by managing customer data, sales pipelines, marketing campaigns, and support ticketing in a single unified interface .

The goal was to build a secure and highly reliable platform compliant with **GDPR, PII protection laws**, and **WCAG 2.1 AA accessibility standards** .

---

## 🌟 Key Features

The CRM system encompasses the following core modules:

* **Omni-channel Campaign Management:** Create and track marketing campaigns across Email and SMS.
* **Lead Capture & Scoring:** Automated lead qualification and management.
* **Sales Pipeline:** Visual drag-and-drop pipeline board, quoting, and e-signature functionalities.
* **360° Customer View:** Centralized database for customer interactions and history.
* **Support Ticketing:** Integrated Case Manager with SLA compliance tracking.
* **Loyalty Management:** Rewards programs, tier management, and customer referrals.
* **Analytics & Reporting:** Automated workflows with real-time dashboards.

---

## 🏗 System Architecture

We utilized a **Layered + Modular Service Architecture** to ensure separation of concerns and maintainability.
`UI (SPA)` → `API Layer` → `Micro-Services` → `Database`

### Core Services :
1.  **Auth Service:** Handles RBAC (Role-Based Access Control) and MFA.
2.  **Customer Data Service:** Manages CRUD operations and deduplication.
3.  **Sales & Pipeline Service:** Manages deals and forecasting.
4.  **Campaign Manager:** Handles segmentation and blast messaging.
5.  **Analytics Engine:** Provides reporting and KPI tracking.

---
# 🚀 CRM Application - Setup & Testing Guide

## 📦 Tech Stack

### Backend Framework
- **Flask** - Python web framework for building REST APIs and serving HTML templates
- **Flask-JWT-Extended** - JWT-based authentication and session management

### Database
- **Firebase Admin SDK** - Google Firebase/Firestore for NoSQL database operations
- **Firestore** - Cloud database for storing customers, leads, tickets, opportunities, loyalty profiles, campaigns

### Frontend
- **HTML/CSS/JavaScript** - Server-side rendered templates with vanilla JS
- Templates located in `templates/` directory
- Static assets (CSS, JS) in `static/` directory

### Testing Framework
- **pytest** - Python testing framework
- **pytest-mock** - Mocking utilities for tests
- **pytest-cov** - Code coverage reporting

### Code Quality Tools
- **pylint** - Python linter for code quality (minimum score: 7.5/10)
- **bandit** - Security vulnerability scanner

### Other Dependencies
- **logging** - Built-in Python logging for audit trails and monitoring
- **secrets** - Secure token generation for referral codes and password resets

---

## 🏃 Installation & Setup

Follow these steps to run the application locally.

### 1. Prerequisites
Ensure you have the following installed:
* Python 3.10+
* pip (Package Manager)
* Firebase `serviceAccountKey.json` file

### 2. Clone & Navigate
``'bash
# Clone the repository
git clone [https://github.com/kaverii11/CRM-APP-CLONE.git](https://github.com/kaverii11/CRM-APP-CLONE.git)

# Navigate to the project directory
cd

3. Install DependenciesBashpip install -r requirements.txt

4. Configuration (Environment Variables)You can set up your environment variables manually or create a .env file.Copy and run this block in your terminal to set defaults:Bash# Windows (PowerShell)

$env:JWT_SECRET_KEY="dev-secret-key"
$env:ADMIN_PASSWORD="admin123"
$env:GOOGLE_APPLICATION_CREDENTIALS="./serviceAccountKey.json"

# Mac/Linux (Bash)
export JWT_SECRET_KEY="dev-secret-key"
export ADMIN_PASSWORD="admin123"
export GOOGLE_APPLICATION_CREDENTIALS="./serviceAccountKey.json"

5. Run the ApplicationBashpython app.py

✅ The server will start at: http://127.0.0.1:5000
🔗 Quick Access LinksPageLocal URLDashboardhttp://127.0.0.1:5000/Loginhttp://127.0.0.1:5000/loginCustomershttp://127.0.0.1:5000/customersTicketshttp://127.0.0.1:5000/tickets👤 Default CredentialsNote: These are for development use only.Admin: admin@crm.com / admin123Manager: manager@crm.com / manager123Support: support@crm.com / support123🧪 Testing StrategyWe follow a rigorous testing plan covering Unit, Integration, and System testing 1.Run Automated

TestsTo run the full test suite (requires pytest):Bash# Run all tests with verbose output
pytest -v

Check Code CoverageWe maintain a code coverage threshold of 75%.Bash# generate coverage report
pytest --cov=app --cov-report=term-missing
Quality & Security ChecksBash# Linting (Pylint)
pylint app.py

# Security Audit (Bandit)
bandit -r .
🐛 Troubleshooting<details><summary><strong>🔥 Issue: Firebase Connection Failed</strong></summary>Cause: The serviceAccountKey.json is missing or the path is incorrect.Fix: Ensure the file is in the root directory and the GOOGLE_APPLICATION_CREDENTIALS env variable points to it.</details><details><summary><strong>🔒 Issue: 401 Unauthorized errors</strong></summary>Cause: JWT Token expired or Secret Key mismatch.Fix: Restart the server to refresh the JWT_SECRET_KEY or clear your browser cookies.</details><details><summary><strong>📦 Issue: Module Not Found</strong></summary>Fix: Re-run pip install -r requirements.txt and ensure your virtual environment is active.</details>
