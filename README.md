# MedGoals — Full-Stack Performance Evaluation System

**MedGoals** is a **full‑stack employee performance evaluation and goal management system** built with **Odoo 17** (backend) and **Next.js 15** (frontend). It allows organizations to define goals, track progress, manage evaluation cycles, calculate performance scores, and visualize leaderboards — all fully integrated with Odoo’s HR module.

---

## Project Overview

**Architecture:**
- **Backend:** Odoo 17 (Python 3.10) deployed on **AWS EC2 (Bitnami AMI)**.
- **Frontend:** Next.js 15 + React + TailwindCSS deployed on **Vercel**.
- **Database:** PostgreSQL (AWS managed within the Odoo instance).

**Core features:**
- HR integration: extends `hr.employee` to include performance metrics.
- Goal assignment and progress tracking per employee.
- Evaluation cycles with score computation (0–10 scale).
- Real‑time performance logs and data analysis.
- Automatic top performer detection and ranking.
- REST API endpoints to connect with the Next.js frontend.

---

## Backend — Odoo 17 (AWS)

### **Tech Stack**
- **Language:** Python 3.10
- **Framework:** Odoo 17 (Community Edition)
- **Deployment:** AWS EC2 with Bitnami Odoo AMI
- **Database:** PostgreSQL (installed with Bitnami stack)
- **Server OS:** Debian 12 (64‑bit)

### **Deployment Steps (Summary)**
1. Launch an EC2 instance using **Bitnami Odoo 17 AMI**.
2. Connect via SSH:
   ```bash
   ssh -i "odoo17-key.pem" bitnami@<your-ec2-public-ip>
   ```
3. Find default credentials:
   ```bash
   cat ~/bitnami_credentials
   ```
4. Access Odoo backend:
   ```
   https://<your-ec2-public-ip>/web/login
   ```
5. Upload the custom module:
   ```bash
   cd /opt/bitnami/odoo/addons
   sudo mkdir med_goals
   sudo chown -R bitnami:bitnami med_goals
   ```
6. Copy your module files via SCP or AWS Console.
7. Restart Odoo services:
   ```bash
   sudo /opt/bitnami/ctlscript.sh restart
   ```

### **Main Module Structure**
```
med_goals/
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── hr_employee_inherit.py
│   ├── goal_assignment.py
│   ├── performance_log.py
│   ├── evaluation_cycle.py
│   └── employee_score.py
├── views/
│   ├── hr_employee_inherit_views.xml
│   ├── goal_assignment_views.xml
│   ├── performance_log_views.xml
│   ├── evaluation_cycle_views.xml
│   ├── employee_score_views.xml
│   └── med_menus.xml
├── security/
│   ├── ir.model.access.csv
│   └── med_goals_security.xml
└── controllers/
    └── api_controllers.py  (REST endpoints for Next.js)
```

### **Backend Features**
- Custom models for goals, performance logs, and evaluation cycles.
- Computed employee scores integrated into `hr.employee`.
- Role‑based access control (Manager / User).
- REST API (JSON endpoints) for frontend consumption.
- Modular, MVC‑compliant Odoo structure.

### **SOLID & Design Patterns (Backend)**
- SRP: reusable helpers for scoring and JSON serialization now live in `backend/med_goals/services` to keep controllers/models lean.
- OCP + Strategy: `ScoreEngine` composes strategies (`GoalsStrategy`, `ProductivityStrategy`, `QualityStrategy`, `EconomicStrategy`) so new score rules can be added without editing the evaluation model.
- Factory: `ScoreEngineFactory` builds engines from cycle configs, centralizing instantiation logic.
- Adapter: `RecordSerializer` converts Odoo many2one values to frontend‑friendly dicts across all API responses.

---

## Frontend — Next.js 15 (Vercel)

### **Tech Stack**
- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS + Shadcn/UI
- **Charts:** Recharts / Chart.js for data visualization
- **Hosting:** Vercel (CI/CD linked to GitHub)

### **Environment Variables (.env.local)**
```env
NEXT_PUBLIC_API_BASE_URL=https://<your-ec2-public-ip>/api
ODOO_URL=https://<your-ec2-public-ip>
ODOO_DB=bitnami_odoo
```

### **Frontend Features**
- Dashboard displaying employee rankings and performance metrics.
- Pages for goal creation, progress updates, and evaluations.
- Secure authentication through Odoo session API.
- Responsive UI for desktop and mobile.

---

## API Endpoints (example)
| Method | Endpoint | Description |
|--------|-----------|-------------|
| `POST` | `/api/session/login` | Authenticate against Odoo backend |
| `GET`  | `/api/employees` | Fetch employees with performance info |
| `GET`  | `/api/goals` | Retrieve goal definitions and assignments |
| `POST` | `/api/logs` | Register a new performance log entry |
| `GET`  | `/api/scores/leaderboard` | Get top performers by area/specialty |

---

## Future Improvements
- Advanced analytics dashboards (PowerBI / Metabase integration)
- Machine learning model for predictive performance trends
- Email notifications and evaluation reports (PDF generation)
- Multi‑company and multi‑language support
- Dockerized development environment

---

## License
This project is licensed under the **LGPL‑3.0** license — compatible with Odoo Community guidelines.

---

## Authors
**Stefan Jativa**  
Software Engineer & Full‑Stack Developer  
GitHub: [@byPronox](https://github.com/byPronox)

**Justin Gomezcoello**  
Software Engineer & Full‑Stack Developer  
GitHub: [@byPronox](https://github.com/byPronox)

---

### Summary
MedGoals unifies performance management in a single ecosystem — with a robust Odoo backend running on AWS and a fast, scalable Next.js frontend deployed on Vercel. It provides an extensible foundation for HR analytics, goal tracking, and data‑driven decision‑making.

