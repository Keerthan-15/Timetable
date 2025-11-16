# Professional Academic Timetable Management System

A comprehensive web-based system for generating and managing academic timetables with intelligent constraint satisfaction algorithms.

## Features

### 🎯 Smart Timetable Generation
- **Generate Timetable**: Create professional timetables with one click
- **Re-generate Timetable**: Modify and regenerate existing timetables
- **All Branches & Semesters**: Support for odd and even semesters across all branches
- **Professional UI**: Modern, attractive interface built with Vue.js + Vuetify

### 🔧 Constraint-Based Scheduling
The system enforces 6 critical scheduling constraints:

1. **First Period Priority**: High-credit subjects (3+ credits) get first period slots on weekdays
2. **Continuous Lab Blocks**: Lab/activity/mini-project classes scheduled in 2-hour continuous blocks
3. **One Lab Per Day**: Maximum one laboratory subject per day
4. **Specialist Classes**: Tutorial/Remedial/Proctor classes in last period only
5. **Saturday Activities**: NSS/Sports/Yoga in 2-hour blocks after break
6. **Credit Hours Accuracy**: Exact allocation based on subject credits and requirements

### 📊 Professional Features
- **Dashboard**: Real-time statistics and constraint compliance indicators
- **Interactive Grid**: Color-coded timetable display with drag-and-drop support
- **Export Options**: Professional PDF and CSV export capabilities
- **Bulk Operations**: Import subjects via CSV, manage teachers and classrooms
- **Validation**: Real-time constraint checking and compliance reporting

## Technology Stack

### Backend
- **Django 4.2**: Python web framework
- **Django REST Framework**: API development
- **PostgreSQL**: Primary database
- **Redis**: Caching and session management
- **WeasyPrint**: Professional PDF generation

### Frontend
- **Vue.js 3**: Modern JavaScript framework
- **Vuetify**: Material Design component library
- **Pinia**: State management
- **Chart.js**: Data visualization
- **Vite**: Fast development tooling

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Timetable
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your database and configuration details
   ```

5. **Database setup**
   ```bash
   # Create PostgreSQL database
   createdb timetable_db

   # Run migrations
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create sample data** (optional)
   ```bash
   python manage.py create_sample_data
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Start Django server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**
   ```bash
   npm run dev
   ```

3. **For production build**
   ```bash
   npm run build
   ```

## Usage

### 1. Generate Timetable
1. Navigate to **Generate Timetable** from the dashboard
2. Select branch, semester, section, and academic year
3. Configure constraint settings as needed
4. Click **Generate Timetable** to create a schedule
5. View results and export if satisfied

### 2. View Timetables
1. Go to **Timetable** section
2. View generated timetables in an interactive grid
3. Check constraint compliance indicators
4. Export to PDF or CSV as needed

### 3. Manage Resources
1. **Subjects**: Add/edit subjects with credits and requirements
2. **Teachers**: Manage teacher assignments and workloads
3. **Classrooms**: Configure room types and capacities
4. **Reports**: Generate comprehensive scheduling reports

## API Documentation

### Core Endpoints

#### Timetable Generation
- `POST /api/generate/` - Generate new timetable
- `POST /api/timetable/{id}/regenerate/` - Regenerate existing timetable
- `GET /api/grid/?session_id={id}` - Get timetable in grid format

#### Resource Management
- `GET /api/branches/` - List all branches
- `GET /api/subjects/` - List all subjects
- `GET /api/teachers/` - List all teachers
- `GET /api/classrooms/` - List all classrooms

#### Export
- `GET /api/timetable/{id}/export/pdf/` - Export timetable as PDF
- `GET /api/timetable/{id}/export/csv/` - Export timetable as CSV

#### Validation
- `POST /api/validate/` - Validate timetable constraints
- `GET /api/dashboard/` - Get dashboard statistics

## Constraint Engine

The system implements a sophisticated constraint satisfaction engine:

### Hard Constraints
- **No teacher conflicts**: Teachers cannot be in two places simultaneously
- **No room conflicts**: Classrooms cannot have overlapping classes
- **Credit hour requirements**: Exact allocation based on subject credits
- **Continuous lab blocks**: Lab classes must be in 2-hour blocks

### Soft Constraints
- **First period priority**: High-credit subjects prefer first period
- **Teacher workload balance**: Distribute teaching load evenly
- **Room utilization efficiency**: Optimize classroom usage

## Professional Features

### PDF Export
- Institution header with branding
- Professional timetable grid layout
- Subject summary and statistics
- Constraint compliance certificate
- Teacher and room utilization charts
- Signature lines for validation

### Dashboard Analytics
- Real-time constraint compliance indicators
- Subject distribution charts
- Room utilization statistics
- Teacher workload analysis
- Generation success metrics

### Advanced Scheduling
- Backtracking algorithm with constraint propagation
- Multiple generation strategies
- Conflict resolution suggestions
- Performance optimization for large datasets

## Development

### Running Tests
```bash
# Backend tests
python manage.py test

# Frontend tests
cd frontend
npm run test
```

### Code Quality
```bash
# Python linting
flake8 timetable_app

# JavaScript linting
cd frontend
npm run lint
```

## Deployment

### Production Setup
1. Set environment variables in `.env`
2. Configure production database
3. Set up Redis for caching
4. Configure web server (nginx/apache)
5. Set up process manager (gunicorn/uwsgi)
6. Configure SSL certificates
7. Set up monitoring and logging

### Environment Variables
```
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_NAME=production_db
DB_USER=production_user
DB_PASSWORD=secure_password
REDIS_URL=redis://your-redis-server:6379/0
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Contact the development team

## Changelog

### v1.0.0
- Initial release with core timetable generation
- Implementation of 6 scheduling constraints
- Professional UI with Vue.js + Vuetify
- PDF and CSV export functionality
- Dashboard with real-time analytics
- Constraint validation engine
- Sample data creation scripts

---

**Built with ❤️ for educational institutions worldwide**