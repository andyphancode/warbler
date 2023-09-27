"""User View tests."""

# Run test with:K
# FLASK_ENV=production python -m unittest test_user_views.py

import os
from unittest import TestCase

from models import db, User, Follows


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):

        db.drop_all()
        db.create_all()

        user = User.signup("testuser", "test@email.com", "testpw", None)
        
        follower1 = User.signup("f1", "f1@email.com", "pw", None)
        follower2 = User.signup("f2", "f2@email.com", "pw", None)
        follower3 = User.signup("f3", "f3@email.com", "pw", None)

        db.session.commit()

        self.user = user
        self.follower1 = follower1 
        self.follower2 = follower2 
        self.follower3 = follower3 

        f1 = Follows(user_being_followed_id=self.follower1.id, user_following_id=self.user.id)
        f2 = Follows(user_being_followed_id=self.follower2.id, user_following_id=self.user.id)
        f3 = Follows(user_being_followed_id=self.user.id, user_following_id=self.follower3.id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()

        self.client = app.test_client()

    def test_show_following(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user.id

            resp = c.get(f"/users/{self.user.id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@f1", str(resp.data))
            self.assertIn("@f2", str(resp.data))
            self.assertNotIn("@f3", str(resp.data))


    def test_show_followers(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user.id

            resp = c.get(f"/users/{self.user.id}/followers")

            self.assertIn("@f3", str(resp.data))
            self.assertNotIn("@f1", str(resp.data))
            self.assertNotIn("@f2", str(resp.data))


    def test_unauthorized_following_access(self):

        with self.client as c:

            resp = c.get(f"/users/{self.user.id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@f1", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unauthorized_follower_access(self):

        with self.client as c:

            resp = c.get(f"/users/{self.user.id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@f3", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))    