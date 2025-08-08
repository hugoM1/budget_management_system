# Budget Management System

A comprehensive Django-based budget management system for advertising campaigns with PostgreSQL backend, Celery task scheduling, and real-time budget monitoring.

## 🚀 Features

- **Budget Tracking**: Daily and monthly budget monitoring for campaigns
- **Campaign Management**: Active, inactive, and paused campaign states
- **Dayparting**: Time-based campaign scheduling
- **Real-time Dashboard**: Live budget statistics and alerts
- **Admin Interface**: Full CRUD operations for all models
- **Background Tasks**: Automated budget checks and resets
- **PostgreSQL Database**: Production-ready database backend

## 🛠️ Technology Stack

- **Backend**: Django 4.2.7
- **Database**: PostgreSQL with psycopg3
- **Task Queue**: Celery with Redis
- **Python**: 3.9+
- **Type Checking**: MyPy

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL server
- Redis server
- Virtual environment (recommended)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd budget_management_system
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create PostgreSQL database
createdb -U postgres budget_management

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=budget_management
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Celery / Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 4. Start the Application

```bash
# Start Django development server
python manage.py runserver

# Start Celery worker (in another terminal)
celery -A budget_system worker -l info

# Start Celery beat (in another terminal)
celery -A budget_system beat -l info
```

### 5. Create Sample Data

```bash
python manage.py create_sample_data
```

## 🌐 Access Points

- **Dashboard**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/

## 📊 System Overview

### Models

- **Brand**: Top-level entity with daily/monthly budgets
- **Campaign**: Individual campaigns with budget limits
- **Spend**: Daily and monthly spend tracking
- **DaypartingSchedule**: Time-based campaign scheduling

### Features

- **Budget Monitoring**: Real-time tracking of daily and monthly spend
- **Campaign States**: Active, inactive, and paused with reasons
- **Alert System**: Warnings for campaigns approaching budget limits
- **Dayparting**: Schedule campaigns to run during specific hours
- **Automated Tasks**: Daily and monthly budget resets

## 🔧 Development

### Running Tests

```bash
# Run Django unit tests
python manage.py test -v 2

# Optional: specific app/package
python manage.py test campaigns.tests -v 2
```

Manual scripts (optional):
```bash
# Test PostgreSQL connection
python test_postgres.py

# Test Celery tasks (queues tasks; requires worker)
python test_celery.py

# End-to-end functional script
python test_system.py
```

### Database Management

```bash
# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database
python manage.py flush
```

## 📈 Monitoring

The system includes comprehensive logging and monitoring:

- **Budget Alerts**: Automatic notifications for budget limits
- **Campaign Status**: Real-time status updates
- **Spend Tracking**: Detailed spend analytics
- **Performance Metrics**: System performance monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions, please check the documentation or create an issue in the repository.