# FreeSWITCH CTI Application

A comprehensive Call Center Technology Integration (CTI) application for FreeSWITCH, providing real-time call visualization, drag-and-drop call management, park orbit visualization, and conference room monitoring.

## Features

- **Real-time Call Visualization**: Monitor all active calls across the domain/tenant
- **Drag & Drop Call Management**: Transfer calls between extensions using intuitive drag and drop
- **Park Orbit Visualizer**: Visual representation of call parking orbits with availability status
- **Conference Room Visualizer**: Monitor conference rooms and participants
- **Secure ESL Connection**: FreeSWITCH Event Socket Layer connection over SSH tunnel
- **User Management**: Web-based user registration and extension linking
- **Real-time Updates**: WebSocket-based communication for instant updates

## Architecture

### Backend
- **FastAPI**: Modern Python web framework
- **FastAPI Users**: Authentication and user management
- **SQLAlchemy**: Database ORM with PostgreSQL support
- **WebSockets**: Real-time communication
- **Paramiko**: SSH tunnel for secure ESL connection

### Frontend
- **Electron**: Cross-platform desktop application
- **WebSockets**: Real-time communication with backend
- **Modern UI**: Responsive design with drag-and-drop functionality

## Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL
- FreeSWITCH server with ESL enabled
- SSH access to FreeSWITCH server

## Installation

### Backend Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Initialize database:
```bash
alembic upgrade head
```

5. Run the backend:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run in development mode:
```bash
npm run dev
```

3. Build for production:
```bash
npm run build
```

## Configuration

### Backend Configuration (.env)

```env
# Database (SQLite for development, PostgreSQL for production)
DATABASE_URL=sqlite+aiosqlite:///./cti_dev.db
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cti_db

# JWT Secret
SECRET_KEY=your-super-secret-jwt-key-here

# FreeSWITCH Connection
FREESWITCH_HOST=192.168.1.100
FREESWITCH_ESL_PORT=8021
FREESWITCH_ESL_PASSWORD=ClueCon
SSH_USERNAME=freeswitch
SSH_PRIVATE_KEY_PATH=/path/to/ssh/key

# Application Settings
DEBUG=True
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

### FreeSWITCH Configuration

Ensure ESL is enabled in your FreeSWITCH configuration:

```xml
<!-- conf/autoload_configs/event_socket.conf.xml -->
<configuration name="event_socket.conf" description="Socket Client">
  <settings>
    <param name="nat-map" value="false"/>
    <param name="listen-ip" value="127.0.0.1"/>
    <param name="listen-port" value="8021"/>
    <param name="password" value="ClueCon"/>
    <param name="apply-inbound-acl" value="loopback.auto"/>
  </settings>
</configuration>
```

## Usage

1. Start the backend server
2. Launch the Electron frontend application
3. Register users through the web interface
4. Link users to FreeSWITCH extensions
5. Monitor calls in real-time
6. Use drag-and-drop to transfer calls
7. Monitor park orbits and conference rooms

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout

### Extensions
- `GET /api/extensions` - List all extensions
- `POST /api/extensions` - Create new extension
- `PUT /api/extensions/{id}` - Update extension
- `DELETE /api/extensions/{id}` - Delete extension

### Calls
- `GET /api/calls/active` - Get active calls
- `POST /api/calls/transfer` - Transfer call
- `POST /api/calls/park` - Park call
- `POST /api/calls/hangup` - Hangup call

### WebSocket
- `WS /ws` - Real-time event stream

## WebSocket Events

### Incoming Events (from backend)
- `call_created` - New call initiated
- `call_answered` - Call answered
- `call_ended` - Call terminated
- `call_parked` - Call parked
- `conference_update` - Conference room update

### Outgoing Events (to backend)
- `transfer_call` - Transfer call request
- `park_call` - Park call request
- `hangup_call` - Hangup call request

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Security Considerations

- ESL connection secured via SSH tunnel
- JWT-based authentication
- CORS configuration for frontend access
- Input validation on all API endpoints
- Secure password hashing

## Future Enhancements

- Queue management and monitoring
- Call recording integration
- Advanced reporting and analytics
- Mobile application support
- Multi-tenant support
- Integration with CRM systems

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the GitHub repository.