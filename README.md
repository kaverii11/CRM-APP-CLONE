# Customer Relationship Management

**Project ID:** P08  
**Course:** UE23CS341A  
**Academic Year:** 2025  
**Semester:** 5th Sem  
**Campus:** RR  
**Branch:** CSE  
**Section:** E  
**Team:** Kryptonite

## 📋 Project Description

A simple CRM app which takes care of customers

This repository contains the source code and documentation for the Customer Relationship Management project, developed as part of the UE23CS341A course at PES University.

## 🧑‍💻 Development Team (Kryptonite)

- [@kaverii11](https://github.com/kaverii11) - Scrum Master
- [@Kavana-coder](https://github.com/Kavana-coder) - Developer Team
- [@KarthikSahukar](https://github.com/KarthikSahukar) - Developer Team
- [@khushi0605](https://github.com/khushi0605) - Developer Team

## 👨‍🏫 Teaching Assistant

- [@RakshithKakunje9](https://github.com/RakshithKakunje9)
- [@Thaman-N](https://github.com/Thaman-N)
- [@v-s-v-i-s-h-w-a-s](https://github.com/v-s-v-i-s-h-w-a-s)

## 👨‍⚖️ Faculty Supervisor

- [@rbanginwar](https://github.com/rbanginwar)


## 🚀 Getting Started

### Prerequisites
- [List your prerequisites here]

### Installation
1. Clone the repository
   ```bash
   git clone https://github.com/pestechnology/PESU_RR_CSE_E_P08_Customer_Relationship_Management_Kryptonite.git
   cd PESU_RR_CSE_E_P08_Customer_Relationship_Management_Kryptonite
   ```

2. Install dependencies
   ```bash
   # Add your installation commands here
   ```

3. Run the application
   ```bash
   # Add your run commands here
   ```

## 📁 Project Structure

```
PESU_RR_CSE_E_P08_Customer_Relationship_Management_Kryptonite/
├── src/                 # Source code
├── docs/               # Documentation
├── tests/              # Test files
├── .github/            # GitHub workflows and templates
├── README.md          # This file
└── ...
```

## 🛠️ Development Guidelines

### Branching Strategy
- `main`: Production-ready code
- `develop`: Development branch
- `feature/*`: Feature branches
- `bugfix/*`: Bug fix branches

### Commit Messages
Follow conventional commit format:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test-related changes

### Code Review Process
1. Create feature branch from `develop`
2. Make changes and commit
3. Create Pull Request to `develop`
4. Request review from team members
5. Merge after approval

## 📚 Documentation

- [API Documentation](docs/api.md)
- [User Guide](docs/user-guide.md)
- [Developer Guide](docs/developer-guide.md)

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

## 📄 License

This project is developed for educational purposes as part of the PES University UE23CS341A curriculum.

---

**Course:** UE23CS341A  
**Institution:** PES University  
**Academic Year:** 2025  
**Semester:** 5th Sem

## 🚀 CI/CD Pipeline (Epic 11)

This project uses a 5-stage GitHub Actions pipeline to ensure code quality and security.

1.  **Build**: Installs all dependencies from `requirements.txt`.
2.  **Test**: Runs all unit and integration tests using `pytest`.
3.  **Coverage**: Checks test coverage with `pytest-cov`. [cite_start]The build fails if coverage is **< 75%**[cite: 628].
4.  **Lint**: Analyzes code quality with `pylint`. [cite_start]The build fails if the score is **< 7.5/10**[cite: 676].
5.  **Security**: Scans for vulnerabilities with `bandit`. The build fails if any issues are found.