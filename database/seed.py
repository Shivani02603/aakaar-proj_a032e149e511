import os
import sys
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import SessionLocal, User, Session, UploadedFile, Chunk, Message

def seed_database():
    """Seed the database with sample data."""
    db = SessionLocal()
    try:
        print("Starting database seeding...")
        
        # Clear existing data in reverse order of dependencies
        print("Clearing existing data...")
        db.query(Message).delete()
        db.query(Chunk).delete()
        db.query(UploadedFile).delete()
        db.query(Session).delete()
        db.query(User).delete()
        db.commit()
        
        # Create sample users
        print("Creating users...")
        users = [
            User(
                id=uuid4(),
                email="alice.johnson@example.com",
                api_key="sk_alice_" + str(uuid4())[:16]
            ),
            User(
                id=uuid4(),
                email="bob.smith@example.com",
                api_key="sk_bob_" + str(uuid4())[:16]
            ),
            User(
                id=uuid4(),
                email="charlie.williams@example.com",
                api_key="sk_charlie_" + str(uuid4())[:16]
            )
        ]
        db.add_all(users)
        db.commit()
        
        # Create sample sessions
        print("Creating sessions...")
        sessions = []
        for i, user in enumerate(users):
            for j in range(2):  # 2 sessions per user
                session = Session(
                    id=uuid4(),
                    user_id=user.id,
                    name=f"Project Analysis {j+1}",
                    created_at=datetime.now() - timedelta(days=7-j)
                )
                sessions.append(session)
        db.add_all(sessions)
        db.commit()
        
        # Create sample uploaded files
        print("Creating uploaded files...")
        uploaded_files = []
        file_names = [
            "Q1_Sales_Report.xlsx",
            "Customer_Feedback.csv",
            "Product_Catalog.xlsx",
            "Financial_Summary.xlsx",
            "Marketing_Data.csv",
            "Inventory_List.xlsx"
        ]
        
        for i, session in enumerate(sessions):
            for j in range(2):  # 2 files per session
                file_index = (i * 2 + j) % len(file_names)
                uploaded_file = UploadedFile(
                    id=uuid4(),
                    session_id=session.id,
                    filename=file_names[file_index],
                    file_size_bytes=(1024 * 1024 * (j + 1)),  # 1MB to 2MB
                    uploaded_at=datetime.now() - timedelta(days=6-j)
                )
                uploaded_files.append(uploaded_file)
        db.add_all(uploaded_files)
        db.commit()
        
        # Create sample chunks
        print("Creating chunks...")
        chunks = []
        sheet_names = ["Sheet1", "Data", "Summary", "Details", "Raw Data"]
        
        for uploaded_file in uploaded_files:
            for chunk_idx in range(3):  # 3 chunks per file
                chunk = Chunk(
                    id=uuid4(),
                    uploaded_file_id=uploaded_file.id,
                    content=f"This is sample content from {uploaded_file.filename}, sheet {sheet_names[chunk_idx % len(sheet_names)]}. It contains important data about sales, customers, and product performance for Q1 2024.",
                    sheet_name=sheet_names[chunk_idx % len(sheet_names)],
                    row_start=chunk_idx * 100 + 1,
                    row_end=chunk_idx * 100 + 100,
                    chunk_index=chunk_idx
                )
                chunks.append(chunk)
        db.add_all(chunks)
        db.commit()
        
        # Create sample messages
        print("Creating messages...")
        messages = []
        user_questions = [
            "Can you summarize the sales data from Q1?",
            "What were the top performing products?",
            "Show me customer feedback trends",
            "What's the current inventory status?",
            "Analyze the financial summary",
            "What marketing channels performed best?"
        ]
        
        assistant_responses = [
            "Based on the sales report, Q1 revenue increased by 15% compared to last quarter. The top products were Product A and Product B.",
            "The top performing products were Product A with $250K in sales and Product B with $180K. Both showed strong growth in the enterprise segment.",
            "Customer feedback shows a 92% satisfaction rate. Common positive themes include product quality and customer support. Areas for improvement include delivery times.",
            "Current inventory shows healthy levels for most products. Product C is running low with only 200 units remaining. Recommend reordering soon.",
            "The financial summary indicates strong profitability with a 22% net margin. Operating expenses are within budget. Cash flow remains positive.",
            "Marketing data shows digital channels performed best with a 35% conversion rate. Email marketing had the highest ROI at 450%. Social media engagement grew by 40%."
        ]
        
        for i, session in enumerate(sessions):
            for msg_idx in range(2):  # 2 message pairs per session
                # User message
                user_msg = Message(
                    id=uuid4(),
                    session_id=session.id,
                    role="user",
                    content=user_questions[(i * 2 + msg_idx) % len(user_questions)],
                    citations=None,
                    created_at=datetime.now() - timedelta(hours=2-msg_idx)
                )
                messages.append(user_msg)
                
                # Assistant message
                assistant_msg = Message(
                    id=uuid4(),
                    session_id=session.id,
                    role="assistant",
                    content=assistant_responses[(i * 2 + msg_idx) % len(assistant_responses)],
                    citations=[
                        {
                            "chunk_id": str(chunks[(i * 6 + msg_idx * 3) % len(chunks)].id),
                            "filename": uploaded_files[(i * 2 + msg_idx) % len(uploaded_files)].filename,
                            "sheet_name": sheet_names[msg_idx % len(sheet_names)],
                            "rows": f"{msg_idx * 100 + 1}-{msg_idx * 100 + 100}"
                        }
                    ],
                    created_at=datetime.now() - timedelta(hours=1-msg_idx)
                )
                messages.append(assistant_msg)
        
        db.add_all(messages)
        db.commit()
        
        print("Database seeding completed successfully!")
        print(f"Created: {len(users)} users, {len(sessions)} sessions, {len(uploaded_files)} uploaded files, {len(chunks)} chunks, {len(messages)} messages")
        
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()