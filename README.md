# 🛡️ Security Asset Manager

> A modern CLI-based Cybersecurity Asset Management System built with **Python + MySQL**.

Security Asset Manager is a command-line application designed to help manage and monitor IT security assets in a centralized database. The system provides asset management, risk classification, security status monitoring, maintenance tracking, authentication, statistics, and a hidden real-time security scanning feature.

---

## 📌 Features

### 🔐 Authentication

* Login system with username and password
* Maximum of 3 login attempts
* Password verification using **bcrypt**
* Default administrator account

### 🖥️ Asset Management

Manage IT assets through a complete CRUD system:

* ➕ Add Asset
* 📋 View Assets
* ✏️ Update Asset
* ❌ Delete Asset
* 🔍 Search Asset

Each asset contains:

* Asset Code
* Asset Name
* Asset Type
* IP Address
* Risk Level
* Security Status
* Description

### ⚠️ Risk Classification

Assets can be classified into four risk levels:

| Risk Level  | Description            |
| ----------- | ---------------------- |
| 🟢 Low      | Low security risk      |
| 🔵 Medium   | Moderate security risk |
| 🟡 High     | High security risk     |
| 🔴 Critical | Critical security risk |

### 🛡️ Security Status

Each asset has a security status:

* ✅ Secure
* ⚠️ Warning
* ❌ Compromised

### 📊 Security Score

The system automatically calculates an overall security score based on asset security status.

| Status      | Points |
| ----------- | -----: |
| Secure      |    100 |
| Warning     |     60 |
| Compromised |     20 |

The final score is displayed from **0–100** and classified as:

* 🟢 GOOD
* 🔵 MODERATE
* 🟡 WARNING
* 🔴 CRITICAL

### 🔧 Maintenance Management

The system provides maintenance record management:

* ➕ Add Maintenance
* 📋 View Maintenance History
* ✏️ Update Maintenance
* ❌ Delete Maintenance

Maintenance statuses:

* Scheduled
* In Progress
* Completed

### 📈 Statistics Dashboard

The dashboard displays:

* Total Assets
* High/Critical Risk Assets
* Secure Assets
* Security Score
* Risk Distribution

### 🔍 Asset Search

Search assets using:

* Asset Code
* Asset Name
* IP Address

### 🕵️ Hidden Security Features

The project also contains hidden commands that can be discovered from the main menu.

#### `scan`

Runs a real-time security check against the database.

The scanner checks:

* Total asset records
* Critical-risk assets
* Compromised assets
* Maintenance tasks currently in progress

It then reports whether immediate security issues are detected.

#### `matrix`

Activates a hidden security-themed terminal mode with:

* Random security characters
* Loading animation
* Database connection checks
* Authentication status
* Asset database status
* Security monitoring status

This works as an Easter egg while also performing actual database checks.

---

# 🏗️ System Architecture

```text
                    ┌──────────────────────┐
                    │        USER          │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Python CLI App    │
                    │                      │
                    │  Rich UI / Menus     │
                    │  Authentication      │
                    │  CRUD Operations     │
                    │  Security Analysis   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    MySQL Database    │
                    │                      │
                    │  users               │
                    │  assets              │
                    │  maintenance         │
                    └──────────────────────┘
```

---

# 🗄️ Database Structure

The application automatically creates the database:

```text
security_asset_db
```

The project uses three main tables:

### `users`

Stores authentication information.

```text
users
├── id
├── username
└── password
```

Passwords are stored using bcrypt hashing.

### `assets`

Stores IT security asset information.

```text
assets
├── id
├── asset_code
├── asset_name
├── asset_type
├── ip_address
├── risk_level
├── security_status
├── description
└── created_at
```

### `maintenance`

Stores maintenance records associated with assets.

```text
maintenance
├── id
├── asset_id
├── maintenance_date
├── maintenance_type
├── description
└── status
```

The `maintenance.asset_id` field references the `assets.id` field using a foreign key.

---

# 🛠️ Technologies

| Technology         | Purpose                           |
| ------------------ | --------------------------------- |
| 🐍 Python 3        | Main programming language         |
| 🗄️ MySQL          | Database management               |
| 🔌 MySQL Connector | Python–MySQL connection           |
| 🔐 bcrypt          | Password hashing and verification |
| 🎨 Rich            | Modern CLI interface              |
| 🌐 ipaddress       | IP address validation             |

---

# 📦 Requirements

Make sure the following are installed:

* Python 3
* MySQL / XAMPP
* pip

Python libraries:

```bash
pip install mysql-connector-python bcrypt rich
```

---

# 🚀 Installation

## 1. Clone the repository

```bash
git clone https://github.com/yusvanfadhil/security-asset-manager.git
```

Enter the project directory:

```bash
cd security-asset-manager
```

> Replace the repository URL above with your actual GitHub repository URL if the repository name is different.

---

## 2. Install dependencies

```bash
pip install mysql-connector-python bcrypt rich
```

---

## 3. Start MySQL

If using XAMPP:

1. Open **XAMPP Control Panel**
2. Start **MySQL**
3. Make sure MySQL is running before launching the application

The current configuration uses:

```text
Host     : localhost
User     : root
Password : empty
Database : security_asset_db
```

---

## 4. Run the application

```bash
python project.py
```

The application automatically initializes the database and required tables when it starts.

---

# 🔑 Default Login

The application creates a default administrator account:

```text
Username: admin
Password: admin123
```

> For a real production environment, change the default credentials before deployment.

---

# 🖥️ Application Flow

```text
START
  │
  ▼
Initialize Database
  │
  ▼
Login
  │
  ├── Failed → Maximum 3 Attempts
  │
  ▼
Dashboard
  │
  ├── Asset Management
  │     ├── Add
  │     ├── View
  │     ├── Update
  │     └── Delete
  │
  ├── Maintenance
  │     ├── Add
  │     ├── View History
  │     ├── Update
  │     └── Delete
  │
  ├── Search Asset
  │
  ├── Statistics
  │
  ├── Logout
  │
  └── Exit
```

---

# 🧪 Example Assets

The application includes example data when the database tables are empty.

| Code    | Asset           | Type     | IP           | Risk     | Status      |
| ------- | --------------- | -------- | ------------ | -------- | ----------- |
| AST-001 | Web Server      | Server   | 192.168.1.10 | High     | Secure      |
| AST-002 | Database Server | Server   | 192.168.1.20 | Critical | Warning     |
| AST-003 | Main Router     | Network  | 192.168.1.1  | Critical | Secure      |
| AST-004 | Admin PC        | Endpoint | 192.168.1.25 | Medium   | Secure      |
| AST-005 | Finance PC      | Endpoint | 192.168.1.30 | High     | Warning     |
| AST-006 | Backup Server   | Server   | 192.168.1.40 | High     | Secure      |
| AST-007 | Office Laptop   | Endpoint | 192.168.1.50 | Low      | Secure      |
| AST-008 | Firewall        | Security | 192.168.1.2  | Critical | Compromised |

---

# 📊 Security Score Calculation

The system calculates the security score using the number of assets in each security status.

```text
Secure       → 100 points
Warning      → 60 points
Compromised  → 20 points
```

Formula:

```text
Security Score =
(Secure × 100 + Warning × 60 + Compromised × 20)
------------------------------------------------
                 Total Assets
```

Example:

```text
Secure       = 5
Warning      = 2
Compromised  = 1

Score =
(5 × 100 + 2 × 60 + 1 × 20) / 8

= 82.5

≈ 83 / 100
```

---

# 🔒 Security Considerations

This project demonstrates several basic security practices:

* Password hashing with bcrypt
* Login attempt limitation
* Parameterized SQL queries
* IP address validation
* Database relationship using foreign keys
* Security status monitoring
* Risk classification

However, this project is primarily intended for **educational and demonstration purposes** and should receive additional hardening before production use.

---

# 🎯 Project Objectives

The main objectives of Security Asset Manager are:

1. Centralize IT asset information
2. Simplify asset management
3. Monitor security conditions
4. Classify cybersecurity risks
5. Track maintenance activities
6. Calculate an overall security score
7. Demonstrate database integration with Python
8. Implement basic authentication and security mechanisms

---

# 👨‍💻 Developers

### Fandi Afnan Alrasya

Student / Developer

```text
Student ID: 2521010121
```

### Muhammad Yusvan Fadillah

Student / Developer

```text
Student ID: 2521010147
```

---

# 📚 Project Type

**Academic / Educational Project**

Category:

```text
Cybersecurity
Database Management
Python Programming
CLI Application
IT Asset Management
```

---

# 📄 License

This project is created for educational purposes.

You are free to study, modify, and improve the project for learning and development purposes.

---

<p align="center">

**🛡️ SECURITY ASSET MANAGER**

*Manage Assets. Monitor Risks. Stay Secure.*

</p>
