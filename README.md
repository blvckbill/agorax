# Agorax
**Distributed Real-Time Task Orchestration Engine**

Agorax is a high-performance, event-driven task management system designed to demonstrate advanced concepts in distributed systems architecture. It addresses the challenges of state synchronization, data consistency, and low-latency communication across multiple clients in a collaborative environment.

The system decouples write operations from client notifications using an asynchronous message bus, ensuring high throughput and eventual consistency for connected WebSocket clients. It also integrates a hybrid AI inference layer that balances cloud-based LLM capabilities with fault-tolerant local heuristics.

## System Architecture

Agorax moves beyond standard CRUD applications by implementing a multi-layered architecture:

1.  **Write Layer (ACID Compliance):** RESTful API write operations are committed synchronously to a PostgreSQL database to ensure data durability and referential integrity.
2.  **Event Bus (Asynchronous Decoupling):** Upon successful state changes, events are published to a RabbitMQ exchange. This prevents blocking the HTTP response while downstream services process the side effects.
3.  **Real-Time Propagation (Fan-out):** Worker nodes consume events from the message bus and broadcast updates via Redis Pub/Sub to stateless WebSocket servers, ensuring all connected clients receive updates immediately.
4.  **Hybrid Intelligence Layer:** A dedicated service handles natural language understanding using Google Gemini 1.5 Flash. It includes a circuit-breaker pattern that fails over to a deterministic local algorithm during network partitions or rate-limiting events.

## Technical Capabilities

### Event-Driven State Synchronization
* **Architecture:** Implements the Publisher/Subscriber pattern using RabbitMQ to decouple services.
* **Consistency:** Achieves near real-time consistency across distributed clients using Redis streams for message broadcasting.
* **Optimistic Concurrency Control:** The frontend implements optimistic UI updates to mask network latency, rolling back state only in the event of a transactional failure.

### Resilient AI Integration
* **LLM Integration:** Utilizes Google Gemini 1.5 Flash for context-aware task analysis and autocomplete suggestions.
* **Fault Tolerance:** Implements a robust fallback strategy. If the external AI service is unreachable or rate-limited, the system automatically degrades to a local NLP heuristic engine, ensuring zero downtime for the suggestion feature.

### Advanced Data Modeling & Security
* **Referential Integrity:** Enforces strict database constraints, including cascading deletes to prevent orphaned records in a relational environment.
* **Role-Based Access Control (RBAC):** A granular permission system handles authorization at the resource level, distinguishing between Owners, Editors, and Viewers via join-table lookups.
* **Secure Authentication:** Uses OAuth2 with Password Flow and JWT (JSON Web Tokens) for stateless, secure API access.

## Technology Stack

**Backend Infrastructure**
* **Language:** Python 3.11
* **Framework:** FastAPI (Asynchronous Standard Gateway Interface)
* **Database:** PostgreSQL 16 (Relational persistence)
* **ORM:** SQLAlchemy (Data mapping and migration)

**Distributed Messaging & Caching**
* **Message Broker:** RabbitMQ (AMQP 0-9-1)
* **Pub/Sub & Cache:** Redis (In-memory data store)

**Frontend Application**
* **Framework:** React 18 (Vite build toolchain)
* **Language:** TypeScript (Static typing for reliability)
* **State Management:** Context API with complex reducers for socket event handling
* **Communication:** Native WebSockets + REST (Axios)

**DevOps & Deployment**
* **Containerization:** Docker & Docker Compose
* **Reverse Proxy:** Nginx (Optional configuration for production)

## Installation & Setup

The project is containerized for consistent deployment environments.

### Prerequisites
* Docker Engine 20.10+
* Docker Compose V2+

### Configuration
Create a `.env` file in the project root with the following configuration variables:

```env
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=agorax_db
DATABASE_URL=postgresql+psycopg2://postgres:secure_password_here@db:5432/db_name

# Security
SECRET_KEY=your_generated_openssl_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Distributed Services
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

# AI Service Configuration
GEMINI_API_KEY=your_google_api_key
MODEL_NAME=model_name