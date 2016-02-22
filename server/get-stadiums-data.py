from flask import Flask, Response
from datetime import timedelta, date, datetime
import requests, json, sqlite3
import sys
from date_config import date_config

app = Flask(__name__)

@app.route("/table")
def get_table():

    list_set = []

    con = sqlite3.connect('list.db')
    with con:
        cur = con.cursor()    
        cur.execute("SELECT * FROM stadiums")
        rows = cur.fetchall()

        for row in rows:
            list_item = {}
            list_item['basics'] = row

            cur.execute("SELECT * FROM weeks WHERE `stadium-id`="+ str(row[0]) +" AND week='"+ str(get_cur_week()) +"' AND year="+ str(get_cur_year()) +";")
            row_2 = cur.fetchall()
            list_item['cur_week'] = row_2

            cur.execute("SELECT * FROM weeks WHERE `stadium-id`="+ str(row[0]) +" AND week='"+ str(get_prev_week()) +"' AND year="+ str(get_cur_year()) +";")
            row_3 = cur.fetchall()
            list_item['prev_week'] = row_3

            list_set.append(list_item)

    fin = json.dumps(list_set)
    resp = Response(fin, status=200, mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = "*"
    return resp    


def get_cur_week():
    if date_config['2016']['season_start'] < date.today().strftime('%Y-%m-%d') < date_config['2016']['season_end']:
        return date.today().strftime('%Y-%m-%d')
    else:
        return date_config['2016']['season_end']

def get_prev_week():
    return (  datetime.strptime(get_cur_week() , '%Y-%m-%d') - timedelta(days=6) ).strftime('%Y-%m-%d')


def get_cur_year():
    return date.today().year



if __name__ == "__main__":
    app.run(debug=True)

