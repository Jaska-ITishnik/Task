Task Project
Overview
Task project is a robust web application engineered with Python, leveraging the Django framework and Django REST Framework (DRF) to facilitate order management, real-time notifications, and transaction processing. It employs PostgreSQL as the database backbone, with Django Channels and Redis powering a scalable WebSocket infrastructure. The system supports three distinct user roles—Admin, Client, and Worker—secured via JWT-based authentication, and integrates simulated payment gateways (Payme and Click) with comprehensive transaction logic.
Technologies

Backend: Python, Django, Django REST Framework
Database: PostgreSQL
WebSocket: Django Channels with Redis as the channel layer
Authentication: JWT (JSON Web Token)
Dependencies: Refer to requirements.txt for a comprehensive list, including channels, channels_redis, djangorestframework_simplejwt, pyOpenSSL, and psycopg2-binary.

Models:

User

Service

Order

Notification (History model for websoket real time messages)

Transaction


Features
Order Management
<img width="1280" height="697" alt="image" src="https://github.com/user-attachments/assets/4c756b0c-fd86-48c0-ae38-670547e216c1" />

Order Creation: Clients initiate orders, triggering WebSocket notifications to the assigned worker and the admin group.
<img width="1280" height="701" alt="image" src="https://github.com/user-attachments/assets/1537251a-d6c3-4c0a-8fa7-700f676cc939" />

Status Updates: Workers modify order statuses (Pending, Paid, In_process, Completed, Canceled), with each change broadcasting a WebSocket notification to the respective client.
<img width="1280" height="701" alt="image" src="https://github.com/user-attachments/assets/ba3be708-26f9-42ad-97bb-46857d613ea3" />

Administrative Oversight: Admins receive real-time notifications for all new orders and can monitor all communications between workers and clients.

Real-Time Notification System
<img width="1280" height="701" alt="image" src="https://github.com/user-attachments/assets/76041dce-22fc-4f2d-8d7b-e75bbc93b118" />
<img width="1280" height="701" alt="image" src="https://github.com/user-attachments/assets/e2b7aac3-1a7c-4906-8221-aa716a34fcd5" />
<img width="1280" height="701" alt="image" src="https://github.com/user-attachments/assets/774ab214-7e58-4c9d-a6e7-327695c14048" />

Endpoint: https://task.jaska-itishnik.uz/api/v1/notification-page/
Authenticated users (Admin, Client, Worker) access role-specific, real-time message streams.
Requires JWT authentication for secure access.
Leverages Django Channels and Redis to deliver instantaneous updates tailored to the logged-in user's role:
Admins view all messages.
Clients and Workers see messages relevant to their orders.




Implementation: WebSocket connections ensure low-latency delivery of notifications, with Redis managing channel layers for scalability.

Permission Model

Admin: Full visibility of order history and all notifications.
Client/Worker: Restricted to orders and notifications pertinent to their role.

Payment Integration

Simulated Payme and Click payment systems with a fully implemented transaction model.
Status transitions (e.g., Confirmed, Canceled) dynamically update associated order statuses.

CI/CD Deployment

Workflow: Integrated CI/CD pipeline named "Task Project CI/CD Deployment" automates deployment on master branch pushes.
Configuration:

Runs on ubuntu-latest.
Utilizes appleboy/ssh-action@v0.1.10 for remote SSH execution.
Steps include navigating to /var/www/Task, pulling the latest changes with git pull, and restarting the service with systemctl restart task.service.
Secured with environment secrets: HOST, USER, and SSH_KEY.
Benefits: Enhances development efficiency with automated deployments, reduces manual errors, ensures rapid updates, and maintains system consistency across environments.

Installation

Clone the repository: git clone <repository-url>.
Install dependencies: pip install -r requirements.txt.
Configure PostgreSQL in settings.py with appropriate credentials.
Set up Redis for the channel layer in settings.py.
Apply migrations: python manage.py migrate.
Launch the server: python manage.py runserver.

Usage

Authenticate via JWT tokens obtained through the DRF authentication endpoint.
Clients create orders using the API, initiating WebSocket notifications.
Workers update order statuses, triggering client notifications.
Admins access https://task.jaska-itishnik.uz/api/v1/notification-page/ to monitor all activities in real time.
