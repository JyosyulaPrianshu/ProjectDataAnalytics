#!/usr/bin/env python3
"""
Test script to check quiz creation and retrieval
"""

from database import DatabaseManager
import json

def test_quiz_system():
    print("🧪 Testing Quiz System...")
    
    # Initialize database manager
    db = DatabaseManager()
    
    # Test database connection
    print("🔍 Testing database connection...")
    connection = db.get_connection()
    if connection:
        print("✅ Database connection successful")
        connection.close()
    else:
        print("❌ Database connection failed")
        return
    
    # Initialize database tables
    print("🔍 Initializing database tables...")
    if db.init_database():
        print("✅ Database tables initialized")
    else:
        print("❌ Failed to initialize database tables")
        return
    
    # Test quiz creation
    print("🔍 Testing quiz creation...")
    
    # Create a test quiz
    test_questions = [
        {
            "question": "Test question 1?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": 0
        }
    ]
    
    success = db.add_quiz('data_analytics', 'gfg', 'Test Quiz', 'Test description', test_questions, 70, 10)
    if success:
        print("✅ Quiz creation successful")
    else:
        print("❌ Quiz creation failed")
        return
    
    # Test quiz retrieval
    print("🔍 Testing quiz retrieval...")
    quiz = db.get_quiz_by_resource('data_analytics', 'gfg')
    if quiz:
        print("✅ Quiz retrieval successful")
        print(f"   Quiz ID: {quiz['id']}")
        print(f"   Title: {quiz['title']}")
        print(f"   Questions: {len(quiz['questions'])}")
    else:
        print("❌ Quiz retrieval failed")
        return
    
    print("🎉 All tests passed! Quiz system is working correctly.")

if __name__ == "__main__":
    test_quiz_system() 