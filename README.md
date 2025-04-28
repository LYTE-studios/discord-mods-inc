# Discord Mods Inc

A Django-based platform for AI-powered Discord moderation and management.

## Project Structure

```
web/
├── chat/               # Chat application
├── config/             # Django project settings
├── core/              # Core functionality
│   ├── services/      # Backend services
│   │   ├── ai_service.py
│   │   ├── monitoring_service.py
│   │   ├── security_service.py
│   │   ├── ticket_service.py
│   │   ├── workflow_service.py
│   │   └── service_registry.py
│   └── models.py      # Core models
├── static/            # Static files
├── templates/         # HTML templates
└── users/             # User management app
```

## Core Services

The platform provides several core services:

### AI Service
Handles AI-powered interactions and responses using OpenAI's GPT models.

```python
from web.core.services import ai_service

response = await ai_service.generate_response("Your prompt here")
```

### Monitoring Service
Provides system monitoring and alerting functionality.

```python
from web.core.services import monitoring_service

metrics = monitoring_service.get_system_metrics()
alerts = monitoring_service.check_alerts()
```

### Security Service
Manages authentication, authorization, and security features.

```python
from web.core.services import security_service

token = security_service.generate_token(user_id)
user = security_service.get_user_from_token(token)
```

### Ticket Service
Handles support ticket management.

```python
from web.core.services import ticket_service

ticket = ticket_service.create_ticket(data, user)
stats = ticket_service.get_ticket_stats()
```

### Workflow Service
Manages workflow processes and tasks.

```python
from web.core.services import workflow_service

workflow = workflow_service.create_workflow(data, user)
stats = workflow_service.get_workflow_stats()
```

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the development server:
```bash
python manage.py runserver
```

## Docker Deployment

The project includes Docker configuration for easy deployment:

```bash
docker compose up -d
```

This will start all necessary services:
- Django web server
- Redis for channels
- Celery workers
- Nginx for static files and reverse proxy

## Environment Variables

Key environment variables:

- `DJANGO_SECRET_KEY`: Django secret key
- `DJANGO_DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `OPENAI_API_KEY`: OpenAI API key for AI functionality
- `REDIS_HOST`: Redis host for channels
- `REDIS_PORT`: Redis port
- `JWT_SECRET_KEY`: Secret key for JWT tokens

See `.env.example` for a complete list of configuration options.