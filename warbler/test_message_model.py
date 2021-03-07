"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

class MessageModelTestCase(TestCase):
    """Test views for Messages."""
    def setUp(self):
        db.drop_all()
        db.create_all()

        self.client = app.test_client()
        user1 = User.signup("test", "test@email.com", "testpw", None)
        user1.id = 10000000
        user2 = User.signup("tester2", "test2@email.com", "testpw", None)
        user2.id = 10000001
        db.session.commit()
        self.tester1 = User.query.get_or_404(10000000)
        self.tester2 = User.query.get_or_404(10000001)
        self.client = app.test_client()

    def tearDown(self):
        with app.test_client() as client:
            db.session.rollback()
        
    def test_message_model(self):
        """test message model"""
        with app.test_client() as client:
            new_msg = Message(text="text", timestamp=None, user_id=self.tester2.id)
            db.session.add(new_msg)
            db.session.commit()
            
            self.assertEqual(len(self.tester2.messages), 1)
            self.assertEqual(self.tester2.messages[0].text, "text")
