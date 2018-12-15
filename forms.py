from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired

class PostForm(FlaskForm):
    item_id = IntegerField("item_id")
    email_post = StringField("email_post")
    post_time = StringField("post_time (e.g. 2038-01-19 03:14:07)")
    file_path = StringField("file_path")
    item_name = StringField("item_name")
    is_pub = IntegerField("is_pub (i.e. 1 for True, 0 for False)")

    group_name = StringField("group_name (i.e. if private")

    submit = SubmitField("Post!")

class TagForm(FlaskForm):
    email_taggee = StringField("email_taggee")
    item_id = IntegerField("item_id")

    submit = SubmitField("Tag!")

class AddFriend(FlaskForm):
    friendgroup = StringField("friendgroup")
    fname = StringField("fname")
    lname = StringField("lname")

    submit = SubmitField("Add!")