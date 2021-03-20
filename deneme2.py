from flask import Flask,render_template,flash,redirect,url_for,session,logging,request,abort
from flask_pymongo import PyMongo
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,MultipleFileField,SelectField
from passlib.hash import sha256_crypt
from pymongo import MongoClient
from functools import wraps
from werkzeug.utils import secure_filename
import os
import pandas as pd
import json
import glob



client=MongoClient("mongodb://localhost:27017/")
db=client["deneme-data"]
collection=db["Kullanici"]
collection2=db["SeriAlma"]



#Kullanici Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
             return f(*args, **kwargs)
        else:
            flash("You have to Logged in to get there!","danger")
            return redirect(url_for("login"))
    return decorated_function




#kullanici kayit formu
class RegisterForm(Form):
    name = StringField("Name Surname",validators=[validators.Length(min=4, max=25)])
    username = StringField("Username",validators=[validators.Length(min=5, max=35)])
    password = PasswordField("Password",validators=[
        validators.Length(min=4, max=25),
        validators.DataRequired(message="Please, give a password"),
        validators.EqualTo(fieldname="confirm_password",message="Different password")
    ])
    email = StringField("Give Email",validators=[validators.Email(message= "Invalid Email")])
    confirm_password=PasswordField("Confirm Your Password")

#Kullanici giris formu
class LoginForm(Form):
    username = StringField("Username")
    password = PasswordField("Password")

#Search Formu
class SearchForm(Form):
    word= TextAreaField("Search")
'''
#Upload Kullanici Secme Formu
class UploadForm (Form):
    account = SelectField(u'Accounts', choices=[('Murat Er','Murat Er'),
                                                ('Ihsan Alp','Ihsan Alp'),
                                                ('Ömer Onur Altok','Ömer Onur Altok'),
                                                ('Orhan Yuksel','Orhan Yuksel'),
                                                ('Mustafa Gurses','Mustafa Gurses'),
                                                ('Natalie Galynova','Natalie Galynova'),
                                                ('Ramazan Yilmaz','Ramazan Yilmaz'),
                                                ('Sales Engineering','Sales Engineering'),
                                                ('Sylvester Ibhaze','Sylvester Ibhaze'),
                                                ('Sara Topraklı','Sara Topraklı'),
                                                ('Hasan Ilgaz','Hasan Ilgaz')])
'''

app= Flask(__name__)
app.secret_key="anttna"#uygulamalarda bu secret key olmak zorunda
#app.config['UPLOAD_FOLDER']= YUKLEME_KLASORU

#Dosya Yuklemede Gerekli Olan Yerler
app.config['UPLOAD_FOLDER'] = 'D:/YAZILIM/Deneme'
path = os.getcwd()
UPLOAD_FOLDER = os.path.join(path, 'uploads')
# Make directory if "uploads" folder not exists
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = set(['csv'])
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#kayit olma
@app.route("/register",methods=["GET","POST"])
@login_required
def register():
    form=RegisterForm(request.form)
    if request.method=="POST" and form.validate():
        name= form.name.data
        username= form.username.data
        email= form.email.data
        password=sha256_crypt.encrypt (form.password.data)#sifreleme yapildi
        mydict= {"name":name,"username":username,"email": email,"password": password}
        x= collection.insert_one(mydict)
        flash("Your Register is succeeded...","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form =form)

#Login Islemi
@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        for x in collection.find():
            password_database=x["password"]
            if x["username"]==username and sha256_crypt.encrypt(password_database):#Sifrelemeyi kaldirip karsilastirma yapiliyor
                flash("Your login progress is a success...","success")

                session["logged_in"]=True
                session["username"]= username

                return redirect(url_for("index"))
            else:
                flash("Wrong username or password...","danger")
                return redirect(url_for("login"))
    return render_template("login.html",form=form)

#Logout Islemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#Arama Sayfasi
@app.route("/search",methods=["GET","POST"])
@login_required
def search():
    form = SearchForm(request.form)
    return render_template("search.html", form=form)

@app.route("/")
@login_required
def index ():
    return render_template("index.html")






#Bos Kisi Kaldirma
@app.route("/space-remove",methods=["GET","POST"])
@login_required
def boskisi ():
    if request.method == "POST":
        a = 0
        error = {"linkedinProfile": None}  # bu ve alttaki satir ile bos olanlar belirlenir
        error_find = collection2.find(error)
        for x in error_find:
            if x["baseUrl"] == 'profileUrl' or x["baseUrl"] == None or x["baseUrl"] == 'error':
                a = a + 1
                collection2.delete_one(x)
        deleted=str(a)
        deleted2=deleted+"satir silindi"
        flash(deleted2, "success")
    return render_template("space-remove.html")

#Dublicate Kaldirma
@app.route("/dublicate-remove",methods=["GET","POST"])
@login_required
def dublicate():
    if request.method == "POST":
        a = 0
        koru = []
        b = 0
        c = 0
        while b == 0:
            for x in collection2.find():
                for y in collection2.find():
                    if x["baseUrl"] == y["baseUrl"] and x["_id"] != y["_id"]:  # base url ayni ve id ler farkli ise bu bir dublicatedir
                        if x["_id"] in koru or y["_id"] in koru:  # For dongulerine daha oncden bilgi cekildigi icin daha oncesinde dublicate bulunmus ve fazlaliklari silinmis ogelerin bir daha silinmesi onlendi
                            break
                        collection2.delete_one(y)
                        a = a + 1  # dublicate sayisni tutar
                        koru.append(y["_id"])  # islem yapilmis birimleri tutar
                        koru.append(x["_id"])
                        break
            koru = []  # veriler baska dublicateler icin sifirlandi
            c = 0  # baska dublicate varsa diye sifirlandi
            for x in collection2.find():  # baska dublicate var mi diye bakildi
                for y in collection2.find():
                    if x["baseUrl"] == y["baseUrl"] and x["_id"] != y["_id"]:
                        b = 0
                        c = 1
            if c != 1:  # dublicate yoksa cikilmasi saglandi
                b = 1

        deleted = str(a)
        deleted2 = deleted + "satir silindi"
        flash(deleted2, "success")
    return render_template("dublicate-remove.html")





#Scrape Dosylarii Yukleme
@app.route('/')
@login_required
def upload_form():
    return render_template('upload.html')


@app.route('/', methods=['POST','GET'])
@login_required
def upload_file():
    #form = UploadForm(request.form)
    if request.method == 'POST':
        a=0
        if 'files[]' not in request.files:
            flash('No file part','danger')
            return redirect(request.url)

        files = request.files.getlist('files[]')

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                a=a+1
            else:
                flash('There are some not supported file','danger')
        account=request.form.get("account")
        #account=form.account.data
        os.chdir("D:\YAZILIM\Deneme")
        extension = 'csv'
        all_filenames = [i for i in glob.glob('*.{}'.format(extension))]
        df = pd.concat([pd.read_csv(f) for f in all_filenames])
        df.insert(0, column="Account", value=account)  # Hangi hesaptan girildigini anlamak icin
        df.reset_index( inplace=True)  # The error indicates that your dataframe index has non-unique (repeated) values. Since it appears you're not using the index, you could create a new one with:
        dimensions = df.shape  # Olsuan excel dosyasinin satir ve sutun sayisni verir, ilki satir ikincisi sutun
        records = json.loads(df.T.to_json()).values()
        collection2.insert_many(records)
        if dimensions[0] == 0:
            flash('There is no file in there', 'danger')
        else:
            flash('Data Uploaded', "success")
            upload = str(dimensions[0])
            upload2 = upload + " " + " new data successfully uploaded"
            flash(upload2, "success")
        if a!=0:
            upload = str(a)
            upload2 = upload+" "+"file(s) successfully uploaded"
            flash(upload2, "success")
        dizin = 'D:\YAZILIM\Deneme'
        for dosya in os.listdir(dizin):#Hosta kaydedilen dosyalari silme
            dosyaYolu = os.path.join(dizin, dosya)
            try:
                if os.path.isfile(dosyaYolu):
                    os.remove(dosyaYolu)
                elif os.path.isdir(dosyaYolu):
                    shutil.rmtree(dosyaYolu)
            except Exception as hata:
                flash('Hata', "danger")
        return redirect('/')




if __name__ == "__main__":
    app.run(debug=True)




#acmak icin asagidakini kullan
#D:/YAZILIM/PycharmProjects/ANT-TNArayuzBoots/deneme2.py
