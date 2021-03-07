"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        user1 = User.signup("tester1", "test@email.com", "testpw", None)
        user1.id = 10000000
        user2 = User.signup("tester2", "test2@email.com", "testpw", None)
        user2.id = 10000001
        self.tester1 = User.query.get_or_404(10000000)
        self.tester2 = User.query.get_or_404(10000001)

        test_msg1 = Message(id=1234567, text="message text1", user_id=self.tester1.id)
        test_msg2 = Message(id=1234568, text="tester2 message", user_id=self.tester2.id)
        db.session.add_all([test_msg1, test_msg2])
        db.session.commit()

    def tearDown(self):
        db.session.rollback()

    def test_show_message(self):
        """test the ability to view the message"""
        with self.client as c:
            res = c.get("/messages/1234568", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("tester2 message", str(res.data))

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.tester2.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.filter(Message.text=="Hello").one()
            self.assertEqual(msg.text, "Hello")       

    def test_no_session_add_message_page(self):
        """Test app route to create new message while not logged it.
        This should redirect to homepage and prompt a unauthorized message with sign up prompt"""
        with app.test_client() as client:
            res = client.get(f"/messages/new", follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized.", str(res.data))
            self.assertIn("Sign up</a>", str(res.data))

    def test_delete_message(self):
        """test deleting a user's posted message. 
        This should redirect and delete the saved msg from DB"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.tester2.id
            res = c.post("/messages/1234568/delete")
            self.assertEqual(res.status_code, 302)
            msg = Message.query.get(1234568)
            self.assertIsNone(msg)
    
    def test_delete_msg_no_login(self):
        """test deleting a user's posted message while not logged in.
        It should redirect and flash unauthorized message."""
        with self.client as c:
            res = c.post("/messages/1234568/delete", follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            msg = Message.query.get(1234568)
            self.assertIn("Access unauthorized.", str(res.data))
            self.assertTrue(msg)

