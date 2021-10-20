import os
from flask import Flask
from flask import render_template, url_for, flash, request, redirect, Response, session
import sqlite3
import pprint
import json
import pusher

app = Flask(__name__)
app.debug=True


@app.route('/election_list', methods=['GET'])
def election_list():
    conn = sqlite3.connect('./cluecon_elections.db')
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    curs.execute("SELECT * from election")
    rows = curs.fetchall()
    return render_template("election_list.html", rows=rows)

@app.route('/save_election_details', methods=['POST'])
def save_election_details():
     msg=''
     if request.method == "POST":
        try:
            election_name = request.form["election_name"]
            election_number=request.form["election_number"]

            print(election_number)
            with sqlite3.connect('./cluecon_elections.db') as con:
                cur = con.cursor()
                cur.execute(
                    "INSERT into election (election_name,sms_number) values (?,?)", [election_name,election_number])
                con.commit()
                msg = "Election successfully Added"
        except Exception as e:
            #con.rollback()
            msg = "We can not add the Election to the list Error: "
            print(e)
        finally:
            print(msg)
            return redirect('/election_list')


def get_election_by_election_id(election_id):
    conn = sqlite3.connect('./cluecon_elections.db')
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    curs.execute("SELECT * FROM election where election_id=?",[election_id])
    rows = curs.fetchone()
    return rows

def get_nominee_by_election_id(election_id):
    conn = sqlite3.connect('./cluecon_elections.db')
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    curs.execute("SELECT * FROM nominee where election_id=?",[election_id])
    rows = curs.fetchall()
    return rows


def get_election_results_by_election_id(election_id):
    conn = sqlite3.connect('./cluecon_elections.db')
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    #curs.execute("select  count(1) as vote_count, v.nominee_id, n.nominee_name, n.nominee_code from nominee n left join vote v  on v.election_id =n.election_id  where v.election_id=? group by v.nominee_id",[election_id])
    curs.execute("select count(1) as vote_count, nominee_id from vote where election_id=? group by nominee_id",[election_id])
    rows = curs.fetchall()
    return rows


def get_votes_list(election_id):
     votes_listt=[]
     backgtound_colors=['rgba(255, 99, 132, 0.2)','rgba(54, 162, 235, 0.2)','rgba(255, 206, 86, 0.2)','rgba(75, 192, 192, 0.2)','rgba(153, 102, 255, 0.2)','rgba(255, 159, 64, 0.2)']
     border_colours=['rgba(255, 99, 132, 1)','rgba(54, 162, 235, 1)','rgba(255, 206, 86, 1)','rgba(75, 192, 192, 1)','rgba(153, 102, 255, 1)','rgba(255, 159, 64, 1)']
     election_result=get_election_results_by_election_id(election_id)
     nominees=get_nominee_by_election_id(election_id)
     i=0
     for nominee in nominees:
        nom={}
        nom["nominee_id"]=nominee["nominee_id"]
        nom["vote_count"]=0
        nom["nominee_name"]=nominee["nominee_name"]
        nom["nominee_code"]=nominee["nominee_code"]
        nom["backgtound_color"]=backgtound_colors[i]
        nom["border_colour"]=border_colours[i]
        for votes_count in election_result:
           if nominee["nominee_id"] == votes_count["nominee_id"]:
              nom["vote_count"]=votes_count["vote_count"]
              break
        votes_listt.append(nom)
        
        i=i+1
        if (len(backgtound_colors)  == i):
           i=0
     return votes_listt



@app.route('/view_election/<election_id>',methods = ["GET"])
def view_election(election_id):
    votes_list=get_votes_list(election_id)
    chart_data=""
    background_colors=""
    for vote in votes_list:
        chart_data = chart_data + vote['nominee_name'] + "@@" + str(vote['vote_count']) + ","
        background_colors= background_colors + vote['backgtound_color'] + "@@" + vote['border_colour'] + "$$"
    print(background_colors)
    return render_template("election_details.html",election_details=get_election_by_election_id(election_id),election_id=election_id,votes_list=votes_list,chart_data=chart_data,background_colors=background_colors)


@app.route("/delete_election/<election_id>",methods = ["POST"])
def delete_delete_election(election_id):
    msg="POST request"
    try:
        with sqlite3.connect('./cluecon_elections.db') as con:
            cur = con.cursor()
            cur.execute("DELETE FROM election where election_id=?",[election_id])
            con.commit()
            msg = "Election deleted sucessfully"
    except Exception as e:
        msg = "We can not delete the Election from the list Error: " + e 
    finally:
        con.close()
        return  redirect(url_for('election_list'))


@app.route("/save_nominee_details/<election_id>",methods = ["POST"])
def save_nominee_details(election_id):
     msg=''
     if request.method == "POST":
        try:
            nominee_name = request.form["nominee_name"]
            nominee_code=request.form["nominee_code"]
            with sqlite3.connect('./cluecon_elections.db') as con:
                cur = con.cursor()
                cur.execute(
                    "INSERT into nominee (nominee_name,nominee_code,election_id) values (?,?,?)", [nominee_name,nominee_code.upper().strip(),election_id])
                con.commit()
                msg = "Nominee successfully Added"
        except Exception as e:
            #con.rollback()
            msg = "We can not add the Election to the list Error: "
            print(e)
        finally:
            print(msg)
            return redirect('/view_election/'+election_id)

def get_nominees_by_enection_id_and_nominee_code(body,election_id):
    conn = sqlite3.connect('./cluecon_elections.db')
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    curs.execute("SELECT * FROM nominee where election_id=? and nominee_code=?",[election_id,body.upper().strip()])
    row = curs.fetchone()
    return row

def get_election_by_number(to_number):
    conn = sqlite3.connect('./cluecon_elections.db')
    conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    curs.execute("SELECT * FROM election where sms_number=?",[to_number])
    row = curs.fetchone()
    return row


def check_already_voted(form_data,election_id):
   conn = sqlite3.connect('./cluecon_elections.db')
   conn.row_factory = sqlite3.Row
   curs = conn.cursor()
   curs.execute("SELECT * FROM vote where to_number=? and from_number=? and election_id=?",[form_data['To'],form_data['From'],election_id])
   row = curs.fetchone()
   return row


def pusn_to_websocket(election_id,to_number):
    votes_list=get_votes_list(election_id)
    chart_data=""
    background_colors=""
    for vote in votes_list:
        chart_data = chart_data + vote['nominee_code'] + "@@" + str(vote['vote_count']) + ","

    pusher_client = pusher.Pusher(
        app_id='1284957',
        key='e4229bc4dffdc9ccb3eb',
        secret='e01ea4764d7f4c9b99f8',
        cluster='ap2',
        ssl=False
    )
    pusher_client.trigger('sharp-cow-343', to_number, {'message': chart_data})


@app.route("/cluecon_election_webhook",methods = ["POST"])
def cluecon_election_webhook():
   print(request.form)
   election_details=get_election_by_number(request.form['To'])
   xml="<Response/>"
   if election_details == None:
      xml="<Response><Message>Not a election number</Message></Response>"
   else:
     vote_for=get_nominees_by_enection_id_and_nominee_code(request.form['Body'],election_details[0]) 
     nominee_id=None
     if vote_for==None:
        nominees=get_nominee_by_election_id(election_details[0])
        xml="<Response><Message>You enterd an invalid code,"
        for row in nominees: 
           xml=xml +" To vote " + row["nominee_name"] + " reply with  code :" +  row["nominee_code"]  + "\n"
           xml=xml+"</Message></Response>"
     else:
        already_voted=check_already_voted(request.form,election_details[0])
        try:
           if already_voted == None:
              with sqlite3.connect('./cluecon_elections.db') as con:
                 cur = con.cursor()
                 cur.execute("INSERT into vote (to_number,from_number,body,sid,nominee_id,election_id) values (?,?,?,?,?,?)", 
                    [request.form['To'],
                    request.form['From'],
                    request.form['Body'],
                    request.form['MessageSid'],
                    vote_for[0],election_details[0]])
                 con.commit()
              xml="<Response><Message>Thank you for your vote</Message></Response>"
              pusn_to_websocket(election_details[0],request.form['To'])
           else:
              xml="<Response><Message>Your vote aleady registred for  "+ already_voted[3] + "</Message></Response>"
        except Exception as e:
            #con.rollback()
            print(e)

   return Response(xml, mimetype='text/xml')


SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY


if __name__ == "__main__":
  app.run(host='0.0.0.0',port=8031,threaded=True)
