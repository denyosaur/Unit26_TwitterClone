"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes

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

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """set up for testing. Create test users."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()
        user1 = User.signup("tester1", "test@email.com", "testpw", None)
        user1.id = 10000000
        user2 = User.signup("tester2", "test2@email.com", "testpw", None)
        user2.id = 10000001
        user3 = User.signup("followertester", "test3@email.com", "testpw", None)
        user3.id = 10000002
        user4 = User.signup("nofollow", "test4@email.com", "testpw", None)
        user4.id = 10000003
        db.session.commit()
        self.tester1 = User.query.get_or_404(10000000)
        self.tester2 = User.query.get_or_404(10000001)
        self.tester3 = User.query.get_or_404(10000002)
        self.tester4 = User.query.get_or_404(10000003)

        test_msg = Message(id=1234567, text="message text1", user_id=self.tester1.id)
        db.session.add(test_msg)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()

    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.tester1.id, user_following_id=self.tester3.id)
        f2 = Follows(user_being_followed_id=self.tester2.id, user_following_id=self.tester3.id)
        f3 = Follows(user_being_followed_id=self.tester3.id, user_following_id=self.tester1.id)
        db.session.add_all([f1,f2,f3])
        db.session.commit()

    def test_following_page(self):
        """test following page to show list of users being followed by logged in user"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.tester3.id
            self.setup_followers()
            res = client.get(f"/users/{self.tester3.id}/following")
            self.assertEqual(res.status_code, 200)
            self.assertIn(self.tester1.username, str(res.data))
            self.assertIn(self.tester2.username, str(res.data))
            self.assertNotIn(self.tester4.username, str(res.data))
    
    def test_followers_page(self):
        """test followers page to show list of users being followed by logged in user"""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.tester3.id
            self.setup_followers()
            res = client.get(f"/users/{self.tester3.id}/followers")
            self.assertEqual(res.status_code, 200)
            self.assertIn(self.tester1.username, str(res.data))
            self.assertNotIn(self.tester2.username, str(res.data))
            self.assertNotIn(self.tester4.username, str(res.data))

    def test_no_session_follower_page(self):
        """test followers page to redirect to homepage when a user is not logged in"""
        with app.test_client() as client:
            res = client.get(f"/users/{self.tester3.id}/followers", follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized.", str(res.data))
            self.assertIn("/signup", str(res.data))

    def test_user_page(self):
        """test user info page"""
        with app.test_client() as client:    
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.tester2.id
            res = client.get(f"/users/{self.tester2.id}")
            self.assertEqual(res.status_code, 200)
            self.assertIn("messages", str(res.data))
            self.assertIn("@tester2", str(res.data))
    
    def test_user_edit_page(self):
        """test user edit page for GET request"""
        with app.test_client() as client:    
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.tester2.id

            res = client.get(f"/users/profile")
            self.assertEqual(res.status_code, 200)
            self.assertIn("tester2", str(res.data))
            self.assertIn("messages", str(res.data))    
    
    def test_user_like(self):
        """test user liking a message. this is a POST request."""
        db.session.commit()
        with app.test_client() as client:    
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.tester2.id
            res = client.post(f"/users/add_like/1234567", follow_redirects=True)
            likes = Likes.query.filter(Likes.message_id==1234567).all()
            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.tester2.id)

    def test_user_unlike(self):
        """test user unliking a message. this is a POST request. First test that message is liked for logged in user
        then remove and test that the like is removed."""
        test_like = Likes(id=12345, user_id=10000001, message_id=1234567)
        db.session.add(test_like)
        db.session.commit()
        with app.test_client() as client:    
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.tester2.id
            likes = Likes.query.filter(Likes.message_id==1234567).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.tester2.id)

            res = client.post(f"/users/add_like/1234567", follow_redirects=True)
            likes = Likes.query.filter(Likes.message_id==1234567).all()
            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(likes), 0)

    def test_sign_up(self):
        """test signing up with a POST request"""
        with app.test_client() as client:  
            res = client.post("/signup", json={"username":"signuptest","email":"testmail@gmail.com","password":"passtest"}, follow_redirects=True)
            new_user = User.query.filter(User.username=="signuptest").one()
            self.assertEqual(res.status_code, 200)
            self.assertTrue(new_user)
            self.assertEqual(new_user.email, "testmail@gmail.com")
            self.assertIn("@signuptest", str(res.data))
        
    
        
    

