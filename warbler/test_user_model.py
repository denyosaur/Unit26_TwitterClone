"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


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


class UserModelTestCase(TestCase):
    """Test models for Users."""

    def setUp(self):
        """Create test client, add sample data."""

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

    def tearDown(self):
        """Clean up any setUps."""
        with app.test_client() as client:
            db.session.rollback()

    def test_user_model(self):
        
        """Does basic model work?"""
        with app.test_client() as client:   
            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            db.session.add(u)
            db.session.commit()

            # User should have no messages & no followers
            self.assertEqual(len(u.messages), 0)
            self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        """Test whether a user is following another."""
        with app.test_client() as client:
            self.assertEqual(User.__repr__(self.tester1), "<User #10000000: test, test@email.com>")
            self.assertEqual(User.__repr__(self.tester2), "<User #10000001: tester2, test2@email.com>")

    def test_is_following(self):
        """Test whether a user is following another."""
        with app.test_client() as client:
            self.tester2.following.append(self.tester1)
            db.session.commit()
            self.assertFalse(self.tester1.is_following(self.tester2))
            self.assertTrue(self.tester2.is_following(self.tester1))
    
    def test_is_followed_by(self):
        """Test whether a user is following another."""
        with app.test_client() as client:
            self.tester2.following.append(self.tester1)
            db.session.commit()
            self.assertTrue(self.tester1.is_followed_by(self.tester2))
            self.assertFalse(self.tester2.is_followed_by(self.tester1))

    def test_user_create(self):
        """test that a created user exists"""
        with app.test_client() as client:
            new_user = User.signup("tester3", "test3@email.com", "testpw", None)
            new_user.id = 10000002
            db.session.add(new_user)
            db.session.commit()
            user_info = User.query.get_or_404(new_user.id)
            self.assertEqual(user_info.username, "tester3")
            self.assertEqual(user_info.email, "test3@email.com")
            self.assertEqual(user_info.username, "tester3")
            self.assertTrue(User.authenticate("tester3", "testpw"))


    def test_username_validation(self):
        """test that a valid username is entered when creating an account"""
        with app.test_client() as client:
            new_user = User.signup(None, "test4@email.com", "testpw", None)
            with self.assertRaises(exc.IntegrityError) as context:
                db.session.commit()

    def test_password_validation(self):
        """test that a valid password is entered when creating an account"""
        with app.test_client() as client:
            new_user = User.signup("passwordtest", "test4@email.com", None, None)
            with self.assertRaises(exc.IntegrityError) as context:
                db.session.commit()
    
    def test_password_validation(self):
        """test that a valid email is entered when creating an account"""
        with app.test_client() as client:
            new_user = User.signup("emailtest", None, "testpw", None)
            with self.assertRaises(exc.IntegrityError) as context:
                db.session.commit()

    def test_login_authenticate(self):
        """test authentication from logging in with a valid and invalid account"""
        with app.test_client() as client:
            log_in = User.authenticate("tester2", "testpw")
            self.assertEqual(log_in.id, self.tester2.id)
            self.assertFalse(User.authenticate(self.tester2.username, "failtest"))
            self.assertFalse(User.authenticate("failtest", self.tester2.username))