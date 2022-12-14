from flask import Flask, render_template, request, redirect, url_for, flash
import os, json
from os import listdir
from datetime import date, datetime
from write_db import db_init, db
from models import Jesuits, Curia, Log
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from form import Registration, Login, Reset, Image_upload

# create the app
app = Flask(__name__)
app.config['SECRET_KEY']="AndsjCatalogue"
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///andhra.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# initialize the app with the extension
db_init(app)
bcrypt=Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def save_image(picture_file):
    picture_name=picture_file.filename
    picture_path=os.path.join(app.root_path, 'static/images/photos', picture_name)
    picture_file.save(picture_path)
    return picture_name

@login_manager.user_loader
def load_user(user_id):
    return Log.query.get(user_id)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('login'))
    form = Registration()
    if form.validate_on_submit():
        encrypted_pwd=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = Log(email=form.email.data, password=encrypted_pwd)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully", category='success')
        # return redirect(url_for('login'))
    return render_template('register.html', form=form)
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('content'))
    form = Login()
    if form.validate_on_submit():
        user=Log.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('content'))
        else:
            flash("Login unsuccessful\nEnter valid details ", category='danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/reset', methods=['GET', 'POST'])
@login_required
def reset():
    form = Reset()
    if form.validate_on_submit():
        if current_user.is_authenticated and bcrypt.check_password_hash(current_user.password, form.current_pwd.data):
            encrypted_pwd = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
            current_user.password=encrypted_pwd
            db.session.add(current_user)
            db.session.commit()
            flash("Your password has been successfully changed", category='success')
            return redirect(url_for('login'))
        else:
            flash("Please Enter correct password", category='danger')
    return render_template('reset.html', form=form)


@app.route('/content')
@login_required
def content():
    # index= ["curia", "communities", "alphabetical", "contact", "house_index", "birthdays", "superiors",
    #          "residing_common", "photos", "residing_india", "jesuits_formation", "residing_foreign", "andhra_vani"]
    filename = os.path.join(app.static_folder, "index.json")
    with open(filename) as test_file:
        index = json.load(test_file)
    data = Jesuits.query.all()
    bdays = []
    count=0
    for day in data:
        bday = day.dob
        bdays.append(bday)
    tday = date.today()
    for i in bdays:
        birth = datetime.strptime(i, "%Y-%m-%d").date()
        if birth.day == tday.day and birth.month == tday.month:
            count+=1
    return render_template("content.html", index=index, count=count)


@app.route("/curia")
@login_required
def curia():
    pro = db.session.execute(db.select(Curia).filter_by(sort="pro")).scalars()
    pc = db.session.execute(db.select(Curia).filter_by(sort="pc")).scalars()
    com = db.session.execute(db.select(Curia).filter_by(sort="com")).scalars()
    po = db.session.execute(db.select(Curia).filter_by(sort="po")).scalars()
    filename = os.path.join(app.static_folder, "commission.json")
    with open(filename) as test_file:
        GBM = json.load(test_file)
    return render_template("curia.html", pro=pro, pc=pc, com=com, po=po, GBM=GBM)


@app.route("/communities")
@login_required
def communities():
    filename = os.path.join(app.static_folder, 'station.json')
    with open(filename) as test_file:
        data = json.load(test_file)
    return render_template("community.html", data=data)


@app.route("/info/<string:name>")
@login_required
def community(name):
    place = db.session.execute(db.select(Jesuits).filter_by(place=name)).scalars()
    title = name
    if name == "Secunderabad":
        aca = db.session.execute(db.select(Jesuits).filter_by(place="Academy")).scalars()
        sam = db.session.execute(db.select(Jesuits).filter_by(place="Samadarshini")).scalars()
        curia = db.session.execute(db.select(Jesuits).filter_by(place="Curia")).scalars()
        pat = db.session.execute(db.select(Jesuits).filter_by(place="Patrick")).scalars()
        return render_template("namecard.html", aca=aca, sam=sam, curia=curia, pat=pat, title=title)
    if name == "Nagarjunanagar":
        novice1 = db.session.execute(db.select(Jesuits).filter_by(sort="FYN")).scalars()
        novice2 = db.session.execute(db.select(Jesuits).filter_by(sort="SYN")).scalars()
        return render_template("namecard.html", data=place, title=title, novice1=novice1, novice2=novice2)
    if name == "Vijayawada":
        san = db.session.execute(db.select(Jesuits).filter_by(place="Sanjeevan")).scalars()
        return render_template("namecard.html", data=place, title=title, san=san)
    return render_template("namecard.html", data=place, title=title)


@app.route("/alphabetical")
@login_required
def alphabetical():
    mem = Jesuits.query.all()
    return render_template("alphabetical.html", mem=mem)


@app.route("/contact")
@login_required
def contact():
    mem = Jesuits.query.all()
    return render_template("contact.html", mem=mem)


@app.route("/House_index")
@login_required
def house_index():
    return render_template("houses.html")


@app.route("/Birthdays")
@login_required
def birthdays():
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
              "November", "December"]
    data = Jesuits.query.all()
    bdays = []
    for day in data:
        bday = day.dob
        bdays.append(bday)
    tday = date.today()
    for i in bdays:
        birth = datetime.strptime(i, "%Y-%m-%d").date()
        if birth.day == tday.day and birth.month == tday.month:
            birthday = db.session.execute(db.select(Jesuits).filter_by(dob=i)).scalars()
            return render_template("birthday.html", data=data, months=months, tday=tday, birthday=birthday)

    return render_template("birthday.html", data=data, months=months, tday=tday)


@app.route("/superiors")
@login_required
def superiors():
    sup= db.session.execute(db.select(Jesuits).filter_by(sort="sup")).scalars()
    return render_template("superior.html", sup=sup)


@app.route("/Residing_common")
@login_required
def residing_common():
    junior = db.session.execute(db.select(Jesuits).filter_by(place="SICJ")).scalars()
    dnc = db.session.execute(db.select(Jesuits).filter_by(place="DNC")).scalars()
    vj = db.session.execute(db.select(Jesuits).filter_by(place="Vidyajyothi")).scalars()
    satya = db.session.execute(db.select(Jesuits).filter_by(place="Satyanilayam")).scalars()
    shem = db.session.execute(db.select(Jesuits).filter_by(place="Shembaganur")).scalars()
    isi = db.session.execute(db.select(Jesuits).filter_by(place="ISI")).scalars()
    sita = db.session.execute(db.select(Jesuits).filter_by(place="Sitagarha")).scalars()
    pastoral = db.session.execute(db.select(Jesuits).filter_by(sort="Pastroal")).scalars()
    return render_template("res_common_house.html", junior=junior, dnc=dnc, vj=vj, satya=satya, shem=shem, isi=isi, sita=sita, pastoral=pastoral)


@app.route("/Residing_india")
@login_required
def residing_india():
    delhi = db.session.execute(db.select(Jesuits).filter_by(place="DELHI")).scalars()
    jaipur = db.session.execute(db.select(Jesuits).filter_by(place="JAIPUR")).scalars()
    dindigul = db.session.execute(db.select(Jesuits).filter_by(place="DINDIGUL")).scalars()
    palak = db.session.execute(db.select(Jesuits).filter_by(place="PALAYAMKOTTAI")).scalars()
    trichi = db.session.execute(db.select(Jesuits).filter_by(place="THIRUCHIRAPPALLI")).scalars()
    return render_template("try.html", delhi=delhi,jaipur=jaipur, dindigul=dindigul, palak=palak, trichi=trichi)


@app.route("/Jesuits_formation")
@login_required
def jesuits_formation():
    novice1 = db.session.execute(db.select(Jesuits).filter_by(sort="FYN")).scalars()
    novice2 = db.session.execute(db.select(Jesuits).filter_by(sort="SYN")).scalars()
    junior = db.session.execute(db.select(Jesuits).filter_by(sort="JUNIOR")).scalars()
    ug1 = db.session.execute(db.select(Jesuits).filter_by(sort="FYUG")).scalars()
    ug2 = db.session.execute(db.select(Jesuits).filter_by(sort="SYUG")).scalars()
    ug3 = db.session.execute(db.select(Jesuits).filter_by(sort="TYUG")).scalars()
    pg = db.session.execute(db.select(Jesuits).filter_by(sort="PG")).scalars()
    reg = db.session.execute(db.select(Jesuits).filter_by(sort="REG")).scalars()
    phil1 = db.session.execute(db.select(Jesuits).filter_by(sort="FYPHIL")).scalars()
    phil2 = db.session.execute(db.select(Jesuits).filter_by(sort="SYPHIL")).scalars()
    the1 = db.session.execute(db.select(Jesuits).filter_by(sort="FYTHE")).scalars()
    the2 = db.session.execute(db.select(Jesuits).filter_by(sort="SYTHE")).scalars()
    the3 = db.session.execute(db.select(Jesuits).filter_by(sort="TYTHE")).scalars()
    pm = db.session.execute(db.select(Jesuits).filter_by(sort="PM")).scalars()
    at = db.session.execute(db.select(Jesuits).filter_by(sort="AT")).scalars()
    it = db.session.execute(db.select(Jesuits).filter_by(sort="IT")).scalars()
    fv = db.session.execute(db.select(Jesuits).filter_by(sort="FV")).scalars()
    dis = db.session.execute(db.select(Jesuits).filter_by(sort="DIS")).scalars()
    ls = db.session.execute(db.select(Jesuits).filter_by(sort="LS")).scalars()
    return render_template("formation.html", novice1=novice1, novice2=novice2, junior=junior, ug1=ug1, ug2=ug2, ug3=ug3,
                           pg=pg,
                           reg=reg, phil1=phil1, phil2=phil2, the1=the1, the2=the2, the3=the3, pm=pm, at=at, it=it,
                           fv=fv, dis=dis, ls=ls)


@app.route("/Residing_foreign")
@login_required
def residing_foreign():
    countries = ["Italy", "France", "Belgium", "USA", "Timor"]
    rome = db.session.execute(db.select(Jesuits).filter_by(place="Rome")).scalars()
    france = db.session.execute(db.select(Jesuits).filter_by(place="France")).scalars()
    belgium = db.session.execute(db.select(Jesuits).filter_by(place="Belgium")).scalars()
    usa = db.session.execute(db.select(Jesuits).filter_by(place="USA")).scalars()
    Timor = db.session.execute(db.select(Jesuits).filter_by(place="Timor Leste")).scalars()
    return render_template("outindia.html", countries=countries, Rome=rome, France=france, Belgium=belgium, Usa=usa,
                           Timor=Timor)



@app.route("/Photos", methods=['GET', 'POST'])
@login_required
def photos():
    form=Image_upload()
    if form.validate_on_submit():
        save_image(form.picture.data)
        return redirect(url_for('photos'))
    images = os.listdir(os.path.join(app.static_folder, "images/photos"))
    return render_template("img_upload.html", form=form, images=images)

@app.route("/Andhra_vani")
@login_required
def andhra_vani():
    return render_template("AndhraVani.html")


@app.route("/upload", methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        dob = request.form['dob']
        name = request.form['name']
        ministry = request.form['ministry']
        place = request.form['place']
        phone = request.form['phone']
        mail_id = request.form['mail_id']
        filename = request.form['photo_name']
        entered = request.form['entered']
        ordained = request.form['ordained']
        finalvows = request.form['finalvows']
        jesuits = Jesuits(name=name, ministry=ministry, place=place, phone_number=phone, mail_id=mail_id,
                          photo_name=filename, dob=dob, entered=entered, ordained=ordained, finalvows=finalvows)
        db.session.add(jesuits)
        db.session.commit()
    return render_template("db_upload.html")


if __name__ == "__main__":
    app.run(debug=True)
    # app.run(host='127.0.0.1', port=3000, debug=True)

# def run():
#     name= db.session.execute(db.select(Jesuits).order_by(Jesuits.place)).scalars()
#     print(name)
#
# run()
