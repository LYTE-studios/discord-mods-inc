# Discord Mods Inc - AI Development Team

A revolutionary platform that creates AI-powered development teams through Discord bots. Each team member (CTO, UX Designer, UI Designer, Developers, and Testers) is an AI bot that collaborates to develop software based on user requests.

## 🌟 Features

- **AI Team Members**: Each bot has a specialized role and personality
- **GitHub Integration**: Automatic repository management and code handling
- **Ticket System**: Organized task management and tracking
- **Real-time Collaboration**: Bots communicate and work together
- **Monitoring System**: Track system health and performance
- **Security**: JWT-based authentication and role-based access control

## 🛠 Technology Stack

- **Language**: Python 3.11+
- **Framework**: Discord.py for bot interactions
- **Database**: Supabase (PostgreSQL)
- **Authentication**: JWT + Supabase Auth
- **Monitoring**: Custom monitoring system with metrics collection
- **Testing**: pytest with asyncio support
- **CI/CD**: GitHub Actions
- **Containerization**: Docker

## 📋 Prerequisites

- Docker and Docker Compose
- Discord Bot Token
- Supabase Account and Credentials
- GitHub Token (for repository management)
- OpenAI API Key

## 🚀 Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/discord-mods-inc.git
cd discord-mods-inc
```

2. Create a `.env` file:
```env
DISCORD_TOKEN=your_discord_token
DISCORD_GUILD_ID=your_guild_id
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key
GITHUB_TOKEN=your_github_token
JWT_SECRET_KEY=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key
LOG_LEVEL=INFO
```

3. Start the application using Docker Compose:
```bash
docker-compose up -d
```

## 🐳 Docker Setup

The application is containerized using Docker for easy deployment and scaling. The setup includes:

- Application container
- Supabase container (for local development)
- Redis container (for caching and rate limiting)

### Building the Image

```bash
docker build -t discord-mods-inc .
```

### Running with Docker Compose

```bash
docker-compose up -d
```

### Environment Variables

All configuration is done through environment variables. See `.env.example` for all required variables.

## 🔧 Development Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

4. Run tests:
```bash
pytest -v
```

## 📚 Project Structure

```
discord-mods-inc/
├── ai/                     # AI team member implementations
├── cogs/                   # Discord bot command modules
├── database/              # Database client and models
├── github/                # GitHub integration
├── monitoring/            # System monitoring
├── security/              # Authentication and authorization
├── tickets/               # Ticket management system
├── utils/                 # Utility functions
├── tests/                 # Test suite
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
├── requirements.txt      # Production dependencies
└── requirements-dev.txt  # Development dependencies
```

## 🤖 AI Team Members

- **CTO Bot**: Strategic planning and architecture decisions
- **UX Designer Bot**: User experience design and flow
- **UI Designer Bot**: Visual design and component creation
- **Developer Bots**: Code implementation and review
- **Tester Bot**: Testing and quality assurance

## 🎫 Ticket System

The system uses a ticket-based workflow:

1. User creates a ticket with requirements
2. CTO Bot analyzes and creates subtasks
3. Team members claim and work on subtasks
4. Tester Bot verifies the implementation
5. CTO Bot reviews and merges the changes

## 📊 Monitoring

The system includes comprehensive monitoring:

- System metrics (CPU, memory, disk usage)
- API and command latency tracking
- Error rate monitoring
- Alert system for issues
- Performance tracking

## 🔐 Security

- JWT-based authentication
- Role-based access control
- Request rate limiting
- Encrypted sensitive data
- Secure webhook handling

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_monitoring.py
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For support, join our [Discord server](https://discord.gg/your-invite-link) or open an issue.