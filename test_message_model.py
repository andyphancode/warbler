"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py

import os
from unittest import TestCase

from models import db, User, Message, Likes

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
    """Test message model."""

    def setUp(self):

        db.drop_all()
        db.create_all()

        user = User.signup("testuser", "test@email.com", "testpw", None)
        user.id = 111111

        db.session.commit()

        self.user = User.query.get(111111)

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """Does basic model work?"""

        message = Message(text="test", user_id=111111)

        db.session.add(message)
        db.session.commit()

        self.assertEqual(self.user.messages[0].text, "test")
    
    def test_message_like(self):

        message = Message(text="test", user_id=111111)

        user = User.signup("testuser2", "test2@email.com", "testpw2", None)

        user.id = 222222

        db.session.add_all([message, user])
        db.session.commit()

        user.likes.append(message)

        db.session.commit()

        likes = Likes.query.filter(Likes.user_id == 222222).all()
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].message_id, message.id)
