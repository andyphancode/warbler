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

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 111111
        self.testuser.id = self.testuser_id

        # self.testmessage = Message(text="test", user_id=self.testuser_id)
        # self.testmessage_id = 1111
        # self.testmessage.id = self.testmessage_id

        db.session.commit()



    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_message_invalid_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 4569876789679824

            resp = c.post("/messages/new", data={"text": "test"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_add_message_no_session(self):

        with self.client as c:
            resp = c.post("/messages/new", data={"text": "test"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
 
    def test_show_message(self):

        message = Message(
            id=1111,
            text="test",
            user_id=self.testuser_id
        )
        
        db.session.add(message)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            message = Message.query.get(1111)

            resp = c.get(f'/messages/1111')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(message.text, str(resp.data))
            
    def test_invalid_message(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get('/messages/xxxxxxxxxxx')

            self.assertEqual(resp.status_code, 404)

    def test_message_delete_unauthorized(self):

        wronguser = User.signup("wronguser", "wrong@email.com", "wrongpw", None)

        wronguser.id = 12345

        message = Message(
            id=1111,
            text="test",
            user_id=self.testuser_id
        )

        db.session.add_all([wronguser,message])
        db.session.commit()


        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 12345

            resp = c.post("/messages/1111/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_message_delete_unauthenticated(self):

        message = Message(
            id=1111,
            text="test",
            user_id=self.testuser_id
        )
        db.session.add(message)
        db.session.commit()

        with self.client as c: 
            resp = c.post("/messages/1111/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m = Message.query.get(1111)
            self.assertIsNotNone(m)
    
    def test_message_delete_correct_user(self):
        message = Message(
            id=1111,
            text="test",
            user_id=self.testuser_id
        )
        db.session.add(message)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/1111/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            msg = Message.query.get(1111)
            self.assertIsNone(msg)