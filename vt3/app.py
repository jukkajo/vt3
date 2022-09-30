# -*- coding: utf-8 -*-
import json
import hashlib
#import sqlite3
import os
import io
from flask import Flask, request, Response, render_template, url_for, session, redirect
from flask_wtf.csrf import CSRFProtect
from polyglot import PolyglotForm
from wtforms import Form, PasswordField, StringField, validators, IntegerField, SelectField, widgets, SelectMultipleField, ValidationError, FieldList, FormField, BooleanField
import mysql.connector.pooling
import mysql.connector
from functools import wraps
#from mysql.connector import errorcode #käyttäjän ei varmaan tätä tarvitse tietää


app = Flask(__name__)
app.secret_key = '"\xf9$T\x89\xefT8[\xf1\xd4Y-r@\t\xec!5d\xf9\xcf\xa2\xaa'

csrf = CSRFProtect(app)
csrf.init_app(app)

app.config.update(SESSION_COOKIE_SAMESITE='Lax')
"""
m = hashlib.sha512()
m.update( str(joukkueen_id).encode("UTF-8") )
m.update( 'ties4080'.encode("UTF-8") )
salasana = m.hexdigest()
"""

P, G, Y = "POST", "GET", "y"
kirj_statukset = ["kirjautunut", "admin"]
raja_arvo = 999999

#tkanta yhteyden avaamisen data
#TODO muuta json tiedostoon tkanta-palvelimen osoite
#TODO tähän pythonanywheren polku

tied = io.open("/home/jukkajo/vt3/static/dbconfig.json", encoding="UTF-8")
dbconf = json.load(tied)

pool=mysql.connector.pooling.MySQLConnectionPool(pool_name="tietokantayhteydet", pool_size=3, **dbconf) #TODO pool isommaksi, jos ei pythonanywhere

yhteys_status = None
x_html = ["kirjautumissivu.xhtml","joukkuelistaussivu.xhtml", "muokkaussivu.xhtml", "admin.xhtml", "adminsivu.xhtml", "admin_main.xhtml", "admin_esivu.xhtml", "sarjat.xhtml", "listakoonti.xhtml", "admin_muokkaus.xhtml", 'kilpailut.xhtml', 'sarjojen_sivu.xhtml']

#TODO nämäkin voisivat periaatteessa siellä erillisessä tiedostossa olla
sqllause1 = '''SELECT kisanimi
                FROM kilpailut'''

sqllause2 = '''SELECT joukkueet.id, joukkueet.joukkuenimi, joukkueet.salasana, kilpailut.kisanimi, sarjat.kilpailu
                FROM joukkueet JOIN sarjat ON joukkueet.sarja = sarjat.id
                JOIN kilpailut ON kilpailut.id = sarjat.kilpailu
                WHERE joukkueet.joukkuenimi = %s AND kilpailut.kisanimi = %s'''

sqllause3 = '''SELECT sarjat.sarjanimi, joukkueet.joukkuenimi, joukkueet.jasenet, kilpailut.kisanimi
                FROM sarjat JOIN joukkueet ON sarjat.id = joukkueet.sarja
                JOIN kilpailut ON sarjat.kilpailu = kilpailut.id WHERE kilpailut.kisanimi = %s
                ORDER BY sarjanimi ASC, joukkuenimi ASC, jasenet ASC
                '''

sqllause4 = '''SELECT joukkueet.id FROM joukkueet JOIN sarjat ON joukkueet.sarja = sarjat.id JOIN kilpailut ON sarjat.kilpailu = kilpailut.id
                WHERE kilpailut.kisanimi = %s AND joukkueet.joukkuenimi = %s;
                '''

sqllause5 = '''SELECT sarjat.id, sarjanimi FROM sarjat
                JOIN kilpailut ON sarjat.kilpailu = kilpailut.id AND kilpailut.kisanimi = %s
                ORDER BY sarjanimi ASC
                '''

sqllause6 = '''SELECT joukkueet.jasenet FROM joukkueet JOIN sarjat ON joukkueet.sarja = sarjat.id
                JOIN kilpailut ON sarjat.kilpailu = kilpailut.id WHERE kilpailut.kisanimi = %s
                AND joukkueet.joukkuenimi = %s
                '''

sqllause7 = '''SELECT joukkuenimi FROM joukkueet JOIN sarjat ON joukkueet.sarja = sarjat.id JOIN kilpailut ON sarjat.kilpailu = kilpailut.id
                WHERE kilpailut.kisanimi = %s AND joukkueet.id != %s
                '''

sqllause8 = '''UPDATE joukkueet,sarjat,kilpailut SET joukkuenimi = %s, joukkueet.jasenet = %s, joukkueet.sarja = %s, joukkueet.salasana = %s
                WHERE joukkueet.sarja = sarjat.id AND sarjat.kilpailu = kilpailut.id
                AND kilpailut.kisanimi = %s AND joukkueet.id = %s;
                '''

sqllause9 = '''UPDATE joukkueet,sarjat,kilpailut SET joukkuenimi = %s, joukkueet.jasenet = %s, joukkueet.sarja = %s
                WHERE joukkueet.sarja = sarjat.id AND sarjat.kilpailu = kilpailut.id
                AND kilpailut.kisanimi = %s AND joukkueet.id = %s;
                '''

sqllause10 = '''SELECT * FROM kilpailut ORDER BY alkuaika ASC
                 '''

sqllause11 = '''SELECT salasana FROM admin
                 '''

sqllause12 = '''SELECT sarjat.id, sarjanimi FROM sarjat
                 JOIN kilpailut ON sarjat.kilpailu = kilpailut.id AND kilpailut.kisanimi = %s
                 ORDER BY sarjanimi ASC
                 '''

sqllause13 = '''SELECT sarjat.id FROM sarjat JOIN kilpailut ON sarjat.kilpailu = kilpailut.id
                 WHERE sarjat.sarjanimi = %s AND kilpailut.kisanimi = %s
                 '''

sqllause14 = '''SELECT joukkuenimi FROM joukkueet JOIN sarjat ON joukkueet.sarja = sarjat.id JOIN kilpailut ON
                 sarjat.kilpailu = kilpailut.id WHERE kilpailut.kisanimi = %s AND sarjat.sarjanimi = %s
                 '''

sqllause15 = '''INSERT INTO joukkueet(joukkuenimi, salasana, sarja, jasenet) VALUES(%s, %s, %s, %s)
                 '''

sqllause16 = '''SELECT joukkueet.id FROM joukkueet JOIN sarjat ON joukkueet.sarja = sarjat.id
                JOIN kilpailut ON sarjat.kilpailu = kilpailut.id WHERE kilpailut.kisanimi = %s
                AND joukkueet.joukkuenimi = %s
                '''

sqllause17 = '''UPDATE joukkueet,sarjat,kilpailut SET joukkueet.salasana = %s
                 WHERE joukkueet.sarja = sarjat.id AND sarjat.kilpailu = kilpailut.id
                 AND kilpailut.kisanimi = %s AND joukkueet.id = %s;
                 '''

sqllause18 = '''SELECT joukkuenimi FROM joukkueet JOIN sarjat ON joukkueet.sarja = sarjat.id JOIN kilpailut ON
                sarjat.kilpailu = kilpailut.id WHERE kilpailut.kisanimi = %s AND sarjat.sarjanimi = %s
                '''

sqllause19 = '''SELECT joukkueet.jasenet,joukkueet.id FROM joukkueet JOIN sarjat ON joukkueet.sarja = sarjat.id
                JOIN kilpailut ON sarjat.kilpailu = kilpailut.id WHERE kilpailut.kisanimi = %s
                AND joukkueet.joukkuenimi = %s
                '''

sqllause20 = '''SELECT sarjat.id, sarjanimi FROM sarjat
                JOIN kilpailut ON sarjat.kilpailu = kilpailut.id AND kilpailut.kisanimi = %s
                ORDER BY sarjanimi ASC
                '''
sqllause21 = '''SELECT rasti FROM tupa JOIN joukkueet ON tupa.joukkue = joukkueet.id WHERE joukkueet.id = %s
                '''

sqllause22 = '''DELETE FROM joukkueet WHERE joukkueet.id = %s
                '''

sqllause23 = '''UPDATE joukkueet,sarjat,kilpailut SET joukkuenimi = %s, joukkueet.jasenet = %s, joukkueet.sarja = %s, joukkueet.salasana = %s
                WHERE joukkueet.sarja = sarjat.id AND sarjat.kilpailu = kilpailut.id
                 AND kilpailut.kisanimi = %s AND joukkueet.id = %s;
                '''

sqllause24 = '''UPDATE joukkueet,sarjat,kilpailut SET joukkuenimi = %s, joukkueet.jasenet = %s, joukkueet.sarja = %s
                WHERE joukkueet.sarja = sarjat.id AND sarjat.kilpailu = kilpailut.id
                AND kilpailut.kisanimi = %s AND joukkueet.id = %s;
                '''

sqllause25 = '''SELECT sarjat.id, sarjanimi FROM sarjat
                JOIN kilpailut ON sarjat.kilpailu = kilpailut.id AND kilpailut.kisanimi = %s
                ORDER BY sarjanimi ASC
                '''

sqllause26 = '''SELECT sarjat.id, sarjanimi FROM sarjat
                JOIN kilpailut ON sarjat.kilpailu = kilpailut.id AND kilpailut.kisanimi = %s
                ORDER BY sarjanimi ASC
                '''

sqllause27  = '''SELECT id FROM joukkueet
                 '''

sqllause28 = '''SELECT kisanimi FROM kilpailut
                '''

sqllause29 = '''SELECT sarjat.id, sarjanimi FROM sarjat
                JOIN kilpailut ON sarjat.kilpailu = kilpailut.id AND kilpailut.kisanimi = %s
                ORDER BY sarjanimi ASC
                '''


#muokkaussivun sqllause-taulukko silmukkaa varten
sql_lauseet_msivu = [sqllause4, sqllause5, sqllause6]

#---Toiminnan logiikat ajatuksella funktio per sivu---

#pääreitti ohjelmaan, ts. kirjautumisen sivun toiminta
@app.route('/', methods=[P, G])
def kirjautumissivu():
    # TODO tämä olisi kyllä hyvä saada pois tästä
    app.config['WTF_CSRF_ENABLED'] = False
    virhe = ""
    sql_tulos = None
    #alustetaan ehtolauseen epävalidiuden takia
    form = request.form.get("form")
    #app.config['WTF_CSRF_ENABLED'] = False
    #Haetaan kilpailujen data tkannasta
    try:
        yhteys = pool.get_connection()
        osoitin = yhteys.cursor(buffered=True, dictionary=True)
        osoitin.execute(sqllause1,)
        kilpailut = osoitin.fetchall()
    except:
        pass
    finally:
        yhteys.close()

    if request.method == P:

        #noudetaan käyttäjän syötteet lomakkeelta
        form = request.form.get("form")
        ssana = request.form.get('salasana')
        tunnus = request.form.get('tunnus')
        kilpailu = request.form.get('kilpailun_valinta')

        try:
            yhteys = pool.get_connection()
            osoitin = yhteys.cursor(buffered=True, dictionary=True)
            osoitin.execute(sqllause2, (tunnus,kilpailu))
            #nyt pitäisi olla Joukkueen data tuloksessa
            sql_tulos = osoitin.fetchone()
            session["joukkuenimi"] = sql_tulos["joukkuenimi"]
            session['kilpailu'] = kilpailu
        except:
            pass
        finally:
            yhteys.close()

        if sql_tulos != None:
            #id = sql_tulos[0]['id']
            id = sql_tulos['id']
            salasana = sha(id, ssana)
            #salasanan ja tunnuksen tarkistus
            if (tunnus.strip().upper() == sql_tulos["joukkuenimi"].strip().upper() and salasana == sql_tulos["salasana"]):
                session["kirjautunut"] = kirj_statukset[0]
                #session["kilpailu"] = kilpailu
                virhe = "Uudelleen ohjataan..."
                return redirect(url_for("joukkuelistaussivu"))

        #return redirect(url_for("kirjautumissivu"))
        virhe = "Kirjautuminen ei onnistunut, annoithan tiedot oikein?"
    else:
        virhe = ""
    return render_template(x_html[0], virhe=virhe, form=form, kilpailut=kilpailut, mimetype="application/xhtml+xml;charset=UTF-8")

#id, ssana
def sha(v1, v2):
    m = hashlib.sha512()
    v1_1 = str(v1).encode("UTF-8")
    v2_1 = str(v2).encode("UTF-8")
    m.update(v1_1)
    m.update(v2_1)
    return m.hexdigest()

def auth_kirj(f):

    @wraps(f)
    def decorated(*args, **kwargs):
        #tähän mahdollisesti muita tarkistuksia
        if not kirj_statukset[0] in session:
            #takaisin kirjautumissivulle
            #return redirect(url_for('kirjautumissivu'))
            return redirect(url_for('joukkuelistaussivu'))
        return f(*args, **kwargs)
    return decorated

# adminsivun auth
def auth_admin(f):

    @wraps(f)
    def decorated(*args, **kwargs):
        #tähän mahdollisesti muita tarkistuksia
        #if not kirj_statukset[1] in session:
        if session.get('kirjautunut') != kirj_statukset[1]:
            return redirect(url_for('adminsivu'))
        return f(*args, **kwargs)
    return decorated

@app.route('/joukkuelistaussivu', methods=[P, G])
#@app.route('/joukkuelistaussivu')
@auth_kirj
def joukkuelistaussivu():
    yhteys, data, joukkue, kilpailu = None, None, None, None
    try:
        #kilpailu, johon kirjauduttiin
        kilpailu = session['kilpailu']
        joukkue = session['joukkuenimi']
        yhteys = pool.get_connection()
        osoitin = yhteys.cursor(buffered=True, dictionary=True)
        osoitin.execute(sqllause3, (kilpailu,))
        data = osoitin.fetchall()
        for ind in range(len(data)):
            data[ind]['jasenet'] = json.loads(data[ind]['jasenet'])
    except:
        pass
    finally:
        yhteys.close()
        #tällä templatelle kokeilin perintää
        if data != None and joukkue != None and kilpailu != None:
            return render_template(x_html[1], data=data, joukkue=joukkue, kilpailu=kilpailu, mimetype="application/xhtml+xml;charset=UTF-8")
        else:
            # varmaan syytä palata kirjautumissivulle, jos jo tässä mentiin metsään
            return redirect(url_for("kirjautumissivu"))

@app.route('/joukkuelistaussivu/logoutsivu')
def logoutsivu():
    # "siivotaan" sessio ja ohjataan käyttäjä kirjautumisen sivulle
    session.clear()
    return redirect(url_for('kirjautumissivu'))

# palauttaa polyglotformin tekstikentän, validaattoreilla tai ilman jne.
def palauta_strField(par1, par3, x, jasenet):
    sF = [None]*len(par1)

    for i in range(len(par1)):
        jas_tunniste = "Jäsen " + str(i+1)
        if par1[i] == 1:
            sF[i] = StringField(jas_tunniste)
        elif par1[i] == 2:
            sF[i] = StringField(jas_tunniste,validators=[pituus_tarkistin])
        else:
            sF[i] = StringField(jas_tunniste,validators=[pituus_tarkistin], default=jasenet[0]['jasenet'][x-(x-par3[i])])

    return sF


def jas_lista_gen(x, jasenet):
    #ottaa luotavien kenttien lukumaaran, seka sen, montako validoidaan (2-5), palauttaa listan kentista
    #nyt en parempaa keksi tähän
    #jasenet[0]['jasenet'] = json.loads(jasenet[0]['jasenet'])
    logic2 = [[0,0,0,0,0],[0,0,0,0,0],[1,0,0,0,0,], [1,2,0,0,0], [1,2,3,0,0], [1,2,3,4,0]]# kaytossa, jos x < 2
    lg1 = [[2,2,1,1,1],[3,2,1,1,1],[3,3,1,1,1],[3,3,3,1,1],[3,3,3,3,1],[3,3,3,3,3]]

    if x == 0:
        lista = palauta_strField(lg1[0], logic2[0], x, jasenet)

    elif x == 1:
        lista = palauta_strField(lg1[1], logic2[1], x, jasenet)

    elif x == 2:
        lista = palauta_strField(lg1[2], logic2[2], x, jasenet)

    elif x == 3:
        lista = palauta_strField(lg1[3], logic2[3], x, jasenet)

    elif x == 4:
        lista = palauta_strField(lg1[4], logic2[4], x, jasenet)

    else:
        lista = palauta_strField(lg1[5], logic2[5], x, jasenet)

    return lista

def pituus_tarkistin_ssana(form, field):
    #olkoon oletuksena vakio 5 merkkia, kun käytetään adminillekin
    if len(field.data.strip()) < 5:
        raise ValidationError('Salasanan oltava väh. 7-merkkiä')

def pituus_tarkistin(form, field):
    if len(field.data.strip()) < 2:
        raise ValidationError('Anna vähintään kaksi (2) merkkiä')

# palauttaa boolin, riiippuen haun tuloksesta
def iteroi_joukkueet(j_nimi, j_id):
    try:
        yhteys = pool.get_connection()
        osoitin = yhteys.cursor(buffered=True, dictionary=True)
        osoitin.execute(sqllause7, (session['kilpailu'], j_id))
        j_nimet = osoitin.fetchall()
    except:
        pass
    finally:
        yhteys.close()
    t_or_f = True
    for i in range(len(j_nimet)):
        if j_nimet[i]['joukkuenimi'].lower().strip() == j_nimi.lower().strip():
            t_or_f = False
    return t_or_f


@app.route('/joukkuelistaussivu/muokkaussivu', methods=[P,G])
def muokkaussivu():

    #TODO, korjaa tämä sekoilu käyttämään Nonetype taulukkoa
    #tmp = [{}] * 3
    j_id = None
    sarjat = None
    jasenet = None

    try:
        #sql_lauseet_msivu
        for i in range(len(sql_lauseet_msivu)):
            yhteys = pool.get_connection()
            osoitin = yhteys.cursor(buffered=True, dictionary=True)
            if i == 1:
                osoitin.execute(sql_lauseet_msivu[i], (session['kilpailu'],)) #1
                sarjat = osoitin.fetchall()
            else:
                osoitin.execute(sql_lauseet_msivu[i], (session['kilpailu'], session["joukkuenimi"])) #0,2
                if i == 0:
                    j_id = osoitin.fetchall()
                else:
                    jasenet = osoitin.fetchall()
            yhteys.close()
    except:
        pass


    #j_id = tmp[0]
    #sarjat = tmp[1]
    #jasenet = tmp[2]

    #=============================================
    j_id = int(j_id[0]['id'])
    #=============================================
    sarjan_valinta = []
    for i in sarjat:
        sarjan_valinta.append((i['id'],i['sarjanimi']))
    #=============================================
    jasenet[0]['jasenet'] = json.loads(jasenet[0]['jasenet'])
    x = len(jasenet[0]['jasenet'])
    #=============================================

    # Olioita sen verran, että tehdäänpäs luokka
    class j_data(PolyglotForm):

        jnimi = StringField("Nimi", validators=[pituus_tarkistin], default=session["joukkuenimi"])
        sarja = SelectField("Sarja", choices=sarjan_valinta)
        salasana = PasswordField("Salasana", validators=[pituus_tarkistin_ssana])
        #------------montako jasenta, 5-jasenelle mahdollisuus
        jas_lista = jas_lista_gen(x,jasenet)
        jas1 = jas_lista[0]
        jas2 = jas_lista[1]
        jas3 = jas_lista[2]
        jas4 = jas_lista[3]
        jas5 = jas_lista[4]

    form = j_data()

    if request.method == P:
        j_nimi = request.form.get("jnimi")
        j_sarja = request.form.get("sarja")
        salasana = request.form.get("salasana")
        jas1 = request.form.get("jas1")
        jas2 = request.form.get("jas2")
        jas3 = request.form.get("jas3")
        jas4 = request.form.get("jas4")
        jas5 = request.form.get("jas5")
        form.validate()

        joukkue = iteroi_joukkueet(j_nimi, j_id)
        ja1, ja2, ja3, ja4, ja5 = jas1.strip(), jas2.strip(), jas3.strip(), jas4.strip(), jas5.strip()
        jasenet = laj_logiikka(ja1, ja2, ja3, ja4, ja5)

        # haetaan kilpailun joukkueet, tarkistetaan löytyykö "osumia"
        if joukkue == True and len(j_nimi.strip()) > 0:
            try:
                yhteys = pool.get_connection()
                osoitin = yhteys.cursor(buffered=True, dictionary=True)

                if len(salasana.strip()) > 0:
                    ssana = sha(str(j_id), salasana)  #id, ssana

                    osoitin.execute(sqllause8, (j_nimi, jasenet, j_sarja, ssana, session['kilpailu'], j_id))

                if len(salasana.strip()) < 1:
                    osoitin.execute(sqllause9, (j_nimi, jasenet, j_sarja, session['kilpailu'], j_id))
                try:
                    #kokeillaan tehdä muutokset pysyviksi
                    yhteys.commit()
                    session['joukkuenimi'] = j_nimi
                except:
                    pass
                finally:
                    pass

            except:
                pass
            finally:
                yhteys.close()


    return render_template(x_html[2], form=form, jnimi=session["joukkuenimi"],  mimetype="application/xhtml+xml;charset=UTF-8")



@app.route('/admin_esivu/logoutsivu_adm', methods=[P,G])
@auth_admin
def logoutsivu_adm():
    session.clear()
    return redirect(url_for('adminsivu'))

@app.route('/admin_esivu', methods=[P,G])
@auth_admin
def admin_esivu():
    try:
        yhteys = pool.get_connection()
        osoitin = yhteys.cursor(buffered=True, dictionary=True)
        osoitin.execute(sqllause10)
        kilpailut = osoitin.fetchall()
    except:
        pass
    finally:
        yhteys.close()
    """tässä vaiheessa taulukon alkiot vakiintuneissa paikoissa ja stringiä ei voi
    tallentaa datetime.datetime - objektin paikalle, joten tehdään samassa järjestykssä oleva lista
    alkuaikojan merkkijonoille, ilman kellonaikaa

    kai tähän jokin järkevämikin tapa olisi


    for ind in kilpailut:
        tmp = ind['alkuaika']
        ind['alkuaika'] = tmp[:9]

    edit. olihan siihen
    """
    return render_template(x_html[6], kilpailut=kilpailut, mimetype="application/xhtml+xml;charset=UTF-8")

@app.route('/admin_main', methods=[P,G])
def admin_main():
    return render_template(x_html[5], mimetype="application/xhtml+xml;charset=UTF-8")

# adminin kirjautuminen
#lisätty tietokantaann oma taulu adminin dataa varten, muuten se on vakio, taulu ei myöskään ole relaatiossa muihin
@app.route('/adminsivu', methods=[P,G])
def adminsivu():
    ssana_tmp = None
    salasana_annettu = None
    salasana_db = None
    v=""
    class adm_kirj(PolyglotForm):
        salasana = PasswordField("Salasana", validators=[pituus_tarkistin_ssana])
    form = adm_kirj()
    #app.config['WTF_CSRF_ENABLED'] = False

    if request.method == P:

        ssana_tmp = request.form.get('salasana', "")

        try:
            yhteys = pool.get_connection()
            osoitin = yhteys.cursor(buffered=True, dictionary=True)
            osoitin.execute(sqllause11,)
            salasana_dp = osoitin.fetchall()
        except:
            pass
        finally:
            yhteys.close()
        salasana_annettu = sha(ssana_tmp,ssana_tmp)
        #if salasana_db != None:
        #v = str(salasana_annettu) + " # " + str(salasana_dp[0]["salasana"])
        if salasana_annettu == salasana_dp[0]["salasana"]:
            #session["kirj_admin"] = kirj_statukset[1]

            session.clear()

            session['kirjautunut'] = kirj_statukset[1]
            return redirect(url_for('admin_main'))
        v = "Salasana väärin"
    else:
        v = ""
    return render_template(x_html[4], v=v, form=form, mimetype="application/xhtml+xml;charset=UTF-8")

#kilpalun valinta adminina admin
@app.route('/admin_esivu/<kilpailu>')
@auth_admin
def sarjat(kilpailu):

    session["kilpailu"] = kilpailu
    try:
        yhteys = pool.get_connection()
        osoitin = yhteys.cursor(buffered=True, dictionary=True)
        osoitin.execute(sqllause12, (session['kilpailu'],))
        sarjat = osoitin.fetchall()
    except:
        pass
    finally:
        yhteys.close()

    return render_template(x_html[7], sarjat=sarjat, kilpailu=session['kilpailu'], mimetype="application/xhtml+xml;charset=UTF-8")


# Sarjan valinta, mikäli kilpailu valittuna
@app.route('/admin_esivu/<kilpailu>/<sarja>', methods=[P,G])
@auth_admin
def sarj_joukkueet(kilpailu,sarja):
    joukkueet = []
    #lkm = 2
    tmp2 = []
    #===========================================================================
    session['sarja'] = sarja
    try:
        yhteys = pool.get_connection()
        osoitin = yhteys.cursor(buffered=True, dictionary=True)
        osoitin.execute(sqllause13, (session['sarja'], session['kilpailu']))
        sarja_id = osoitin.fetchall()
        session['sarja_id'] = sarja_id[0]['id']
    except:
        pass
    finally:
        yhteys.close()

    try:
        #jos en olisi näin laiska, tekisin jonkin yleis-funktion tälle
        yhteys = pool.get_connection()
        osoitin = yhteys.cursor(buffered=True, dictionary=True)
        osoitin.execute(sqllause14, (session['kilpailu'], session['sarja']))
        joukkueet = osoitin.fetchall()
    except:
        pass
    finally:
        yhteys.close()
    #===========================================================================

    class j_data(PolyglotForm):

        jnimi = StringField("Nimi", validators=[pituus_tarkistin])
        salasana = PasswordField("Salasana", validators=[pituus_tarkistin_ssana])

        jas_lista = jas_lista_gen(0,[])
        jas1 = jas_lista[0]
        jas2 = jas_lista[1]
        jas3 = jas_lista[2]
        jas4 = jas_lista[3]
        jas5 = jas_lista[4]

    form = j_data()

    if request.method == 'POST':
        jnimi = request.form.get("joukkuenimi")
        salasana = request.form.get("salasana")
        jas1 = request.form.get("jas1")
        jas2 = request.form.get("jas2")
        jas3 = request.form.get("jas3")
        jas4 = request.form.get("jas4")
        jas5 = request.form.get("jas5")
        tmp= [jas1,jas2,jas3,jas4,jas5]

        for ind in tmp:
            if ind.strip() != "":
                tmp2.append(ind)
            else:
                continue

        jasenet = json.dumps(tmp2)

        # lisätään muutokset tietokantaan
        if request.method == P and form.validate():

            try:
                yhteys = pool.get_connection()
                osoitin = yhteys.cursor(buffered=True, dictionary=True)
                osoitin.execute(sqllause15, (jnimi, salasana, session['sarja_id'], jasenet))
                session['joukkuenimi'] = jnimi
                yhteys.commit()
            except:
                pass
            finally:
                yhteys.close()

            try:
                yhteys = pool.get_connection()
                osoitin = yhteys.cursor(buffered=True, dictionary=True)
                osoitin.execute(sqllause16, (session['kilpailu'],jnimi))
                tiedot = osoitin.fetchall()
                joukkue_id = tiedot[0]['id']
            except:
                pass
            finally:
                yhteys.close()

            try:
                ssana = sha(str(joukkue_id), salasana)
                yhteys = pool.get_connection()
                osoitin = yhteys.cursor(buffered=True, dictionary=True)
                osoitin.execute(sqllause17, (ssana, session['kilpailu'], joukkue_id))
                yhteys.commit()
            except:
                pass
            finally:
                yhteys.close()

            try:
                yhteys = pool.get_connection()
                osoitin = yhteys.cursor(buffered=True, dictionary=True)
                osoitin.execute(sqllause18, (session['kilpailu'], session['sarja']))
                joukkueet = osoitin.fetchall()
            except:
                pass
            finally:
                yhteys.close()



    return render_template(x_html[8],sarja=session['sarja'],kilpailu=session['kilpailu'],form=form,joukkueet=joukkueet, mimetype="application/xhtml+xml;charset=UTF-8")


def laj_logiikka(ja1,ja2,ja3,ja4,ja5):
    j1, j2, j3, j4, j5 = len(ja1), len(ja2), len(ja3), len(ja4), len(ja5)
    if j1 > 0 and j2 > 0 and j3 > 0 and j4 > 0 and j5 > 0:
        return json.dumps((ja1, ja2, ja3, ja4, ja5))
    if j1 > 0 and j2 > 0 and j3 > 0 and j4 > 0:
        return json.dumps((ja1, ja2, ja3, ja4))
    if j1 > 0 and j2 > 0 and j3 > 0:
        return json.dumps((ja1, ja2, ja3))
    if j1 > 0 and j2 > 0:
        return json.dumps((ja1, ja2))

#Mahdollistetaan joukkueen datan muokkaus adminin kautta
@app.route('/admin_esivu/<kilpailu>/<sarja>/<jnimi>', methods=[P,G])
@auth_admin
def admin_muokkaus(kilpailu,sarja,jnimi):
    session['joukkuenimi'] = jnimi
    joukkue_id = None
    T = False
    try:
        yhteys = pool.get_connection()
        osoitin = yhteys.cursor(buffered=True, dictionary=True)
        osoitin.execute(sqllause19, (session['kilpailu'],session['joukkuenimi']))
        j_tiedot = osoitin.fetchall()
        j_tiedot[0]['jasenet'] = json.loads(j_tiedot[0]['jasenet'])
        joukkue_id = j_tiedot[0]['id']
        k = len(j_tiedot[0]['jasenet'])
    except:
        pass
    finally:
        yhteys.close()

    try:
        yhteys = pool.get_connection()
        osoitin = yhteys.cursor(buffered=True, dictionary=True)

        osoitin.execute(sqllause20, (session['kilpailu'],))
        sarjat = osoitin.fetchall()
        sarja_valinta = []
        for i in sarjat:
            sarja_valinta.append((i['id'],i['sarjanimi']))
    except:
        pass
    finally:
        yhteys.close()

    class j_data(PolyglotForm):

        joukkueenpoisto = BooleanField('Poista joukkue')
        j_nimi = StringField('Joukkueen nimi', validators=[pituus_tarkistin], default=jnimi)
        salasana = PasswordField('Salasana', validators=[pituus_tarkistin_ssana])
        sarja = SelectField('Sarja', choices=sarja_valinta)
        try:
            jas1 = StringField('Jäsen 1', validators=[pituus_tarkistin],default=j_tiedot[0]['jasenet'][0])
        except:
            jas1 = StringField('Jäsen 1', validators=[pituus_tarkistin],default="")
        try:
            jas2 = StringField('Jäsen 2', validators=[pituus_tarkistin],default=j_tiedot[0]['jasenet'][1])
        except:
            jas2 = StringField('Jäsen 2', validators=[pituus_tarkistin],default="")
        try:
            jas3 = StringField('Jäsen 3',default=j_tiedot[0]['jasenet'][2])
        except:
            jas3 = StringField('Jäsen 3',default="")
        try:
            jas4 = StringField('Jäsen 4',default=j_tiedot[0]['jasenet'][3])
        except:
            jas4 = StringField('Jäsen 4',default="")
        try:
            jas5 = StringField('Jäsen 5',default=j_tiedot[0]['jasenet'][4])
        except:
            jas5 = StringField('Jäsen 5',default="")

    form = j_data()

    if request.method == P:
        joukkueenpoisto = request.form.get("joukkueenpoisto")
        j_nimi = request.form.get("j_nimi")
        jsarja = request.form.get("sarja")
        jas1 = request.form.get("jas1")
        jas2 = request.form.get("jas2")
        jas3 = request.form.get("jas3")
        jas4 = request.form.get("jas4")
        jas5 = request.form.get("jas5")
        salasana = request.form.get("salasana")

        if joukkueenpoisto == Y:
            try:
                yhteys = pool.get_connection()
                osoitin = yhteys.cursor(buffered=True, dictionary=True)
                osoitin.execute(sqllause21, (joukkue_id,))
                rastit = osoitin.fetchall()
            except:
                pass
            finally:
                yhteys.close()

            """Joukkuetta ei kuitenkaan saa poistaa, jos joukkueella on jo rastileimauksia.
            Anna selkeä virheilmoitus, jos joukkueen poistaminen ei onnistu."""

            if len(rastit) > 0:
                ilmoitus = "Joukkueella on rastileimauksia"
                return render_template(x_html[9], form=form, ilmoitus=ilmoitus, jatko="sitä ei voida poistaa", mimetype="application/xhtml+xml;charset=UTF-8")
            else:
                try:
                    yhteys = pool.get_connection()
                    osoitin = yhteys.cursor(buffered=True, dictionary=True)
                    osoitin.execute(sqllause22, (joukkue_id,))
                    yhteys.commit()
                except:
                    pass
                finally:
                    yhteys.close()
                    return redirect(url_for('admin_esivu'))

        ja1, ja2, ja3, ja4, ja5 = jas1.strip(), jas2.strip(), jas3.strip(), jas4.strip(), jas5.strip()

        jasenet = laj_logiikka(ja1, ja2, ja3, ja4, ja5)

        form.validate()
        if joukkue_id != None:
            T = iteroi_joukkueet(j_nimi,joukkue_id)

        if len(j_nimi.strip()) > 0 and T == True:
            try:
                yhteys = pool.get_connection()
                osoitin = yhteys.cursor(buffered=True, dictionary=True)
                if len(salasana.strip()) > 0:

                    s_sana = sha(str(joukkue_id), salasana)
                    osoitin.execute(sqllause23, (j_nimi, jasenet, jsarja, s_sana, session['kilpailu'], joukkue_id))

                if len(salasana.strip()) < 1:
                    osoitin.execute(sqllause24, (jnimi, jasenet, jsarja, session['kilpailu'], joukkue_id))

                try:
                    yhteys.commit()
                    session['joukkuenimi'] = j_nimi
                except:
                    pass
                finally:
                    pass

            except:
                pass
            finally:
                yhteys.close()
    ilmoitus="Tiedot ajantasalla / päivitetty!"
    return render_template(x_html[9],form=form, ilmoitus=ilmoitus, jatko="", mimetype="application/xhtml+xml;charset=UTF-8")


@app.route('/admin_esivu/kilpailut', methods=[P,G])
@auth_admin
def kilpailujen_sivu():
    try:
        yhteys = pool.get_connection()
        osoitin = yhteys.cursor(buffered=True, dictionary=True)
        osoitin.execute(sqllause10)#TODO poista ->28
        kilpailut = osoitin.fetchall()
    except:
        pass
    finally:
        yhteys.close()
    return render_template(x_html[10], kilpailut=kilpailut, mimetype="application/xhtml+xml;charset=UTF-8")


@app.route('/admin_esivu/sarjat', methods=[P,G])
@auth_admin
def sarjojen_sivu():
    if session.get('kilpailu') == "":
        return redirect(url_for('kilpailujen_sivu'))
    if session.get('kilpailu') != session['kilpailu']:
        session.pop('sarja',None)
        session.pop('sarja_id',None)
        session.pop('jnimi',None)
        try:
            yhteys = pool.get_connection()
            osoitin = yhteys.cursor(buffered=True, dictionary=True)
            osoitin.execute(sqllause29, (session['kilpailu'],))
            sarjat = osoitin.fetchall()
        except:
            pass
        finally:
            yhteys.close()


        return render_template(x_html[11], sarjat=sarjat, mimetype="application/xhtml+xml;charset=UTF-8")
    else:
        try:
            yhteys = pool.get_connection()
            osoitin = yhteys.cursor(buffered=True, dictionary=True)
            osoitin.execute(sqllause29, (session['kilpailu'],))
            sarjat = osoitin.fetchall()
        except:
            pass
        finally:
            yhteys.close()


        return render_template(x_html[11], sarjat=sarjat, mimetype="application/xhtml+xml;charset=UTF-8")
