from flask import Flask, render_template, session, redirect, url_for, request
from sqlalchemy import create_engine
from flaskext.mysql import MySQL
from flask_sqlalchemy import SQLAlchemy
from forms import PostForm, TagForm, AddFriend
import hashlib
import pymysql
pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"



########################
# START DATABASE SETUP #
########################

conn_string = "mysql://{user}:{password}@{host}/{db}?charset=utf8".format(
        user = "root",
        password = "",
        host = "localhost",
        db = "finalproject"
    )
engine = create_engine(conn_string)
con = engine.connect()

######################
# END DATABASE SETUP #
######################



class User:
    def __init__(self, email="", password=""):
        self.email = email
        self.password = password
        self.authenticated = False
        self.itemsicansee = []

    def authenticate(self):
        self.authenticated = True

    def setEmail(self, email):
        self.email = email

    def getEmail(self):
        return self.email

    def setitemsicansee(self, itemsicansee):
        self.itemsicansee = itemsicansee

    def getitemsicansee(self):
        return self.itemsicansee


user = User()

def getEntry(query, search, attr):
    ''' con=connection
        query="SELECT * FROM person WHERE email = %s;"
        search=[email_form]
        attr="email"
    '''

    try:
        result = ""
        db_call = con.execute(query, search)
        for x in db_call:
            result = x[attr]
        return result
    except:
        print("Issue.")


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
def home():
    if user.authenticated == False:
        return redirect(url_for("login"))

    itemstodisplay = []


    ''' add public content to "itemstodisplay" '''
    publiccontentitems = con.execute("SELECT * FROM contentitem WHERE is_pub = 1")
    for publiccontentitem in publiccontentitems:
        wasadded = False
        for i in range(0, len(itemstodisplay)):
            if publiccontentitem["post_time"] < itemstodisplay[i]["post_time"]:
                itemstodisplay.insert(i, publiccontentitem)
                wasadded = True
        if wasadded == False:
            itemstodisplay.append(publiccontentitem)

    ''' now add items from your friend group to "itemstodisplay" '''
    groupcontentitems = con.execute("SELECT * FROM contentitem WHERE email_post IN "
                                    "(SELECT owner_email FROM belong WHERE email = %s);", [user.getEmail()])
    for groupcontentitem in groupcontentitems:
        wasadded = False
        for i in range(0, len(itemstodisplay)):
            if groupcontentitem["post_time"] < itemstodisplay[i]["post_time"]:
                itemstodisplay.insert(i, groupcontentitem)
                wasadded = True
        if wasadded == False:
            itemstodisplay.append(groupcontentitem)

    ''' now handle tagged people '''
    tags = {}
    for itemtodisplay in itemstodisplay:
        tagged = con.execute(f"SELECT email_tagged FROM tag WHERE status = 'True' AND item_id = {itemtodisplay['item_id']};")
        tags[itemtodisplay["item_id"]] = []
        for taggee_email in tagged:
            tags[itemtodisplay["item_id"]].append(taggee_email)

    ''' now ratings '''
    ratings = {}
    for itemtodisplay in itemstodisplay:
        rating = con.execute(
            f"SELECT emoji FROM rate WHERE item_id = {itemtodisplay['item_id']};")
        ratings[itemtodisplay["item_id"]] = []
        for r in rating:
            ratings[itemtodisplay["item_id"]].append(r)

    user.setitemsicansee(itemstodisplay)

    form = TagForm(request.form)

    if request.method == "POST" and form.validate_on_submit():
        email_taggee = request.form["email_taggee"]
        item_id = request.form["item_id"]
        if email_taggee == user.getEmail():
            con.execute(f"INSERT INTO tag VALUES ('{email_taggee}', '{email_taggee}', {item_id}, 'True', '2016-07-07 00:01:01');")
        else:
            con.execute(f"INSERT INTO tag VALUES ('{email_taggee}', '{user.getEmail()}', {item_id}, 'False', '2016-07-07 00:01:01');")

    return render_template('home.html', itemstodisplay=itemstodisplay, tags=tags, ratings=ratings, form=form)

@app.route("/add", methods=["POST", "GET"])
def add():
    if user.authenticated == False:
        return redirect(url_for("login"))

    form = AddFriend(request.form)

    if request.method == "POST" and form.validate_on_submit():
        friendgroup = request.form["friendgroup"]
        fname = request.form["fname"]
        lname = request.form["lname"]

        result = con.execute(f"SELECT COUNT(*) FROM person WHERE fname = '{fname}' AND lname = '{lname}';")
        theresult = 4
        for x in result:
            theresult = x
        if "1" in str(theresult):
            theresult = 1

        if theresult == 1:
            owner_person = con.execute(f"SELECT * FROM belong WHERE fg_name = '{friendgroup}';")
            for x in owner_person:
                owner_email = x["owner_email"]
            person = con.execute(f"SELECT * FROM person WHERE fname = '{fname}' AND lname = '{lname}';")
            for x in person:
                their_email = x["email"]

            con.execute(f"INSERT INTO belong VALUES ('{their_email}', '{owner_email}', '{friendgroup}');")
        else:
            print("More than one person by that name OR person does not exist.")

    return render_template("add.html", form=form)

@app.route("/tags", methods=["POST", "GET"])
def tags():
    if user.authenticated == False:
        return redirect(url_for("login"))

    itemsimtaggedin = con.execute("SELECT * FROM contentitem WHERE item_id IN (SELECT item_id FROM tag WHERE "
                                  "email_tagged = %s AND status = 'False');", [user.getEmail()])

    if request.method == "POST":
        if request.form.get("Accept", None):
            id = request.form.get("Accept", None)
            con.execute(f"UPDATE tag SET status = 'True' WHERE item_id = {id}")

        elif request.form.get("Decline", None):
            id = request.form.get("Decline", None)
            con.execute(f"DELETE FROM tag WHERE item_id = {id}")

    return render_template("tags.html", itemsimtaggedin=itemsimtaggedin)


@app.route("/post", methods=["POST", "GET"])
def post():
    if user.authenticated == False:
        return redirect(url_for("home"))

    form = PostForm(request.form)

    if request.method == "POST" and form.validate_on_submit():
        # item_id = form.item_id.data
        # email_post = form.email_post.data
        # post_time = form.post_time.data
        # file_path = form.file_path.data
        # item_name = form.item_name.data
        # is_pub = form.is_pub.data
        # group_name = form.group_name.data

        # item_id = 4
        # email_post = "jack@gmail.com"
        # post_time = "2001-01-19 03:14:07"
        # file_path = "https://bit.ly/2EyCzY9"
        # item_name = "churchill"
        # is_pub = 0
        # group_name = "Squad"

        item_id = request.form["item_id"]
        email_post = request.form["email_post"]
        post_time = request.form["post_time"]
        file_path = request.form["file_path"]
        item_name = request.form["item_name"]
        is_pub = request.form["is_pub"]
        group_name = request.form["group_name"]


        con.execute(f"INSERT INTO contentitem VALUES({item_id}, '{email_post}', '{post_time}', '{file_path}',"
                    f" '{item_name}', {is_pub});")



    return render_template("post.html", form=form)


# @app.route("/tagit", methods=["GET", "POST"])
# def tagit():
#     if user.authenticated == True:
#         return redirect((url_for("home")))
#
#
#
#     return render_template("tagit.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if user.authenticated == True:
        return redirect(url_for("home"))

    # people = con.execute("SELECT * FROM person")
    # con.close()


    error = None

    if request.method == 'POST':
        email_form = request.form['email']
        password_form = request.form['password']

        try:
            db_people = con.execute("SELECT * FROM person WHERE email = %s;", [email_form])
            for person in db_people:
                email_form = person["email"]
        except:
            error = "Issue."
        hashed_password_form = hashlib.sha256(password_form.encode("utf-8")).hexdigest()

        try:
            db_people = con.execute("SELECT * FROM person WHERE email = %s;", [email_form])
            for person in db_people:
                password_form = person["password"]
        except:
            error = "Issue."
        hashed_db_pass = hashlib.sha256(password_form.encode("utf-8")).hexdigest()

        if hashed_password_form == hashed_db_pass:
            user.authenticate()
            user.setEmail(email_form)
            return redirect(url_for("home"))
        else:
            error = "User not found."
    return render_template("login.html", error=error)


if __name__ == '__main__':
    app.run()
