"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

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
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        user1 = User.signup("test1", "email1@email.com", "testpw1", None)
        user2 = User.signup("test2", "email2@email.com", "testpw2", None)

        user1.id = 111111
        user2.id = 222222

        db.session.commit()

        user1 = User.query.get(111111)
        user2 = User.query.get(222222)

        self.user1 = user1
        self.user2 = user2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

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

    ########################################
    # Authenticating

    def test_wrong_username(self):
        self.assertFalse(User.authenticate("wrongusername", "testpw1"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate("test1", "wrongpassword"))
    
    def test_authentication(self):
        user = User.authenticate(self.user1.username, "password")
        self.assertIsNotNone(user)

    ########################################
    # Following

    def test_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertEqual(len(self.user2.followers), 1)
        self.assertEqual(len(self.user1.following), 1)

        self.assertEqual(self.user2.followers[0].id, self.user1.id)
        self.assertEqual(self.user1.following[0].id, self.user2.id)
    
    def test_is_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))

    def test_is_followed_by(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user2.is_followed_by(self.user1))
        self.assertFalse(self.user1.is_followed_by(self.user2))

    #############################
    # Signup 

    def test_signup(self):

        user = User.signup("testuser", "testemail@email.com", "testpassword", None)
        user.id = 333333
        db.session.commit()

        user = User.query.get(333333)

        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "testemail@email.com")
        # checks that pw is encrypted
        self.assertNotEqual(user.password, "testpassword")

    def test_invalid_username(self):
        user = User.signup(None, "testemail@email.com", "testpassword", None)
        user.id = 333333
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_invalid_email(self):
        user = User.signup("testuser", None, "testpassword", None)
        user.id = 333333
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password(self):
        with self.assertRaises(ValueError) as context:
            user = User.signup("testuser", "testemail@email.com", None, None)
        with self.assertRaises(ValueError) as context:
            user = User.signup("testuser", "testemail@email.com", "", None)
          