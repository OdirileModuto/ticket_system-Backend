import logging
from sqlalchemy import (
    create_engine, Column, String, Integer, ForeignKey, Text, DateTime
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env", verbose=True)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ticketing_system.log"),
        logging.StreamHandler()
    ]
)

# Define Base for ORM
Base = declarative_base()

def create_db_url() -> str:
    """Create database URL from environment variables with error handling."""
    required_vars = ['PGUSER', 'PGPASSWORD', 'PGHOST', 'PGPORT', 'PGDATABASE']
    try:
        env_vars = {var: os.environ[var] for var in required_vars}
        return f'postgresql+psycopg2://{env_vars["PGUSER"]}:{env_vars["PGPASSWORD"]}@{env_vars["PGHOST"]}:{env_vars["PGPORT"]}/{env_vars["PGDATABASE"]}'
    except KeyError as e:
        logging.error(f"Missing environment variable: {e}")
        raise

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, nullable=False)
    user_type = Column(String)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String)

    # Relationships
    tickets_created = relationship("Ticket", back_populates="creator", foreign_keys="[Ticket.user_id]")
    tickets_allocated = relationship("Ticket", back_populates="allocated_user", foreign_keys="[Ticket.allocated_to]")

class Ticket(Base):
    __tablename__ = 'tickets'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    priority = Column(String)
    status = Column(String)
    start_time = Column(DateTime)
    department = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    allocated_to = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    # Relationships
    creator = relationship("User", back_populates="tickets_created", foreign_keys=[user_id])
    allocated_user = relationship("User", back_populates="tickets_allocated", foreign_keys=[allocated_to])
    files = relationship("File", back_populates="ticket")  
    subjects = relationship("TicketSubject", back_populates="ticket")

class File(Base):
    __tablename__ = 'files'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey('tickets.id'))
    type = Column(String)
    size = Column(String)
    last_modified = Column(Text)
    last_modified_date = Column(DateTime)
    file_path = Column(Text)

    ticket = relationship("Ticket", back_populates="files")

class Subject(Base):
    __tablename__ = 'subjects'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_text = Column(Text, nullable=False)
    description = Column(Text)
    answer_1 = Column(Text)
    answer_2 = Column(Text)
    answer_3 = Column(Text)

    ticket_subjects = relationship("TicketSubject", back_populates="subject")

class TicketSubject(Base):
    __tablename__ = 'ticket_subjects'

    id = Column(Integer, primary_key=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey('tickets.id'), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey('subjects.id'), nullable=False)

    ticket = relationship("Ticket", back_populates="subjects")
    subject = relationship("Subject", back_populates="ticket_subjects")

def main():
    # Create database engine
    engine = create_engine(create_db_url())

    # Create tables
    try:
        Base.metadata.create_all(engine)
        logging.info("Database tables created successfully!")
    except Exception as e:
        logging.error(f"Error creating database tables: {e}")
        raise

    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Create a new user
        new_user = User(
            username="john_doe",
            user_type="admin",
            email="john.doe@example.com",
            password="securepass123",
            role="admin"  # Added role field
        )
        session.add(new_user)
        session.commit()
        logging.info(f"New user created: {new_user.username}")

        # Create a new ticket
        new_ticket = Ticket(
            ticket_number="TICK001",
            title="System Access Issue",  # Added title field
            description="User unable to access system",
            priority="High",
            status="Open",
            start_time=datetime.now(),
            user_id=new_user.id,
            department="IT"
        )
        session.add(new_ticket)
        session.commit()
        logging.info(f"New ticket created: {new_ticket.ticket_number}")

        # Create a subject
        new_subject = Subject(
            subject_text="Login Issue",
            description="Unable to login to the system"
        )
        session.add(new_subject)
        session.commit()
        logging.info(f"New subject created: {new_subject.subject_text}")

        # Link the subject to the ticket
        link = TicketSubject(ticket_id=new_ticket.id, subject_id=new_subject.id)
        session.add(link)
        session.commit()
        logging.info(f"Subject linked to ticket: {new_ticket.ticket_number}")

        # Attach a file to the ticket
        new_file = File(
            name="screenshot.png",
            ticket_id=new_ticket.id,
            type="image/png",
            size="1024 KB",
            last_modified="Some metadata",
            last_modified_date=datetime.now(),
            file_path="/path/to/screenshot.png"
        )
        session.add(new_file)
        session.commit()
        logging.info(f"File attached to ticket: {new_file.name}")

        # Query and display results
        ticket_query_result = session.query(Ticket).filter_by(ticket_number="TICK001").first()
        if ticket_query_result:
            for subject in ticket_query_result.subjects:
                logging.info(f"Subject: {subject.subject.subject_text}")

            files_query_result = session.query(File).filter_by(ticket_id=ticket_query_result.id).all()
            for file in files_query_result:
                logging.info(f"File: {file.name}, Path: {file.file_path}")

        logging.info("Data inserted and linked successfully!")

    except Exception as e:
        logging.error(f"Error during database operations: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()