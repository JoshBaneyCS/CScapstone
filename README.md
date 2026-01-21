# UMGC Spring 2026 Capstone - Online Casino!

> University of Maryland Global Campus — Computer Science Capstone (Spring 2026)

---

## Overview

*This capstone project focuses on the development of a web-based singleplayer casino gaming application designed to simulate real-world casino gameplay while demonstrating core computer science principles. The application will allow users to securely register and authenticate through a login system, select from available casino games, and play using a virtual bankroll that is tracked across sessions. The initial release of the system will support two popular card games: Blackjack and Poker.
The primary objective of this project is to design and implement a full-stack web application that integrates backend game logic, user authentication, database-driven state management, and modern deployment practices. Each user will begin with a predefined starting bankroll, and all wagers, wins, and losses will be persistently stored in a relational database. The system will validate user credentials and ensure proper session management to maintain data integrity and security.
In addition to application functionality, this project emphasizes real-world software engineering practices. The application will be deployed on self-hosted infrastructure using containerization and orchestration technologies. Continuous integration and continuous deployment (CI/CD) pipelines will be implemented to automate testing and deployment. By completing this project, the team aims to demonstrate proficiency in web development, backend programming, database management, and DevOps methodologies, while delivering a functional and extensible casino simulation platform.
*

## Features

- Stateful db storage for User accounts and bankroll
- Pygame framework to create each app
- Containerized and built on Kubernetes

## Tech Stack

| Layer       | Technology       |
|-------------|------------------|
| Frontend    | Python, TS       |
| Backend     | Python, GO       |
| Database    | Postgres/mysql   |
| Infrastructure    | Cloud Native, but self hosted Kubernetes. Cloudflare, Traefik or HAProxy          |
| Deployment  | ArgoCD, GitHub Actions, Grafana/Prometheus. Kubernetes hosted on Prem, Block and S3-like storage. ARM64 Container registry within Kubernetes. Seperate Dev, Staging, and Prod Enviorments. Blue-Green Deployment using tags in GitHub.          |

## Getting Started

### Prerequisites


```
- Python
- Pygame
- TypeScript
- React Framework
- GOlang REST API
```

### Installation

```bash
# Clone the repository
git clone https://github.com/JoshBaneyCS/CScapstone.git
# Navigate to the project directory
cd your-repo

# Install dependencies
# Add specific commands here
cd backend/
go mod tidy
go build
..
cd frontend/ 
npm install
```

### Running the Application

```bash
# Add run commands here
```

## Project Structure

```

```

## Team

| Name | Role | Contact |
|------|------|---------|
| Josh | DevOps / SRE, Backend | [Email](mailto:joshnbaney@gmail.com) [Phone] (410-946-4226) |
| Jerry | Backend | [Email](mailto:gardinjb@hotmail.com) [Phone] (607-661-6313) |
| David | Full Stack | [Email](mailto:atreusion@gmail.com) [Phone] (443-538-5585) |
| Alan | Full Stack | [Email](alanb97@icloud.com) [Phone] (562-219-1482) |

### Responsibilities

**Josh** — Owns CI/CD pipelines, observability (monitoring, logging, alerting), and infrastructure. Available to support backend development.

## Documentation

- [Project Proposal](docs/proposal.md)
- [Requirements Specification](docs/requirements.md)
- [Design Document](docs/design.md)
- [User Guide](docs/user-guide.md)

## Timeline

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Project Proposal | 1/20/26 | ✅ Complete |
| Requirements Complete | 1/20/26 | 👷 Inprogress |
| Design Complete | 2/3/26 | 🔲 Not Started |
| Implementation | 2/10/26 | 🔲 Not Started |
| Testing | 2/10/26 | 🔲 Not Started |
| Final Presentation | 3/3/26 | 🔲 Not Started |

## License

This project is developed as part of the UMGC Computer Science Capstone course. All rights reserved.

---

<p align="center">
  <sub>UMGC Computer Science Capstone • Spring 2026</sub>
</p>
