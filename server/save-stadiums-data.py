from config import config
from lookup import lookup
import requests, json
import oauth2
import urllib2
from datetime import timedelta, date
import sqlite3
import sys
from date_config import date_config
import smtplib

con = sqlite3.connect('list.db')

def id_lookup(service, db_id):
    return lookup[db_id][service]

def get_metrics(db_id):

    metrics = {}

    id = str(db_id)

    # social metrics
    ylp_stats = get_ylp_stats(id)
    goog_stats = get_goog_stats(id)
    fs_stats = get_fs_stats(id)

    metrics['composite_rating'] = (ylp_stats[0]*2 + goog_stats[0]*2 + fs_stats[0]) / 3
    metrics['total_ratings'] = ylp_stats[1] + goog_stats[1] + fs_stats[1]
    metrics['total_visits'] = fs_stats[2]

    # ticket cost metrics
    ticket_stats = get_ticket_stats(id)

    metrics['avg_ticket_price'] = ticket_stats[0]
    metrics['num_games_price'] = ticket_stats[1]

    # attendance metrics
    metrics['avg_attendance'] = '0'
    metrics['num_games_atten'] = '0'

    return metrics


# get SeatGeek stats
def get_ticket_stats(id):

    today = date.today()
    a_week_from_today = today + timedelta(days=6)
    today = today.strftime('%Y-%m-%d')
    a_week_from_today = a_week_from_today.strftime('%Y-%m-%d')

    resp = requests.get('https://api.seatgeek.com/2/events?venue.id='+ id_lookup('sg', id) +'&datetime_utc.gte='+ today +'&datetime_utc.lte='+ a_week_from_today)
    data = resp.json()

    avg_price = 0
    num_games = 0

    for event in data['events']:
        avg_price += event['stats']['average_price']
        num_games += 1

    if num_games == 0:
        return [ 0, 0 ]

    return [ (avg_price / num_games), num_games ]


# get Yelp stats
def get_ylp_stats(id):

    url = 'https://api.yelp.com/v2/business/' + id_lookup('ylp', id)

    consumer = oauth2.Consumer(config['ylp_ck'], config['ylp_cs'])
    oauth_request = oauth2.Request(
        method="GET", url=url, parameters=None)

    oauth_request.update(
        {
            'oauth_nonce': oauth2.generate_nonce(),
            'oauth_timestamp': oauth2.generate_timestamp(),
            'oauth_token': config['ylp_t'],
            'oauth_consumer_key': config['ylp_ck']
        }
    )

    token = oauth2.Token(config['ylp_t'], config['ylp_ts'])
    oauth_request.sign_request(
        oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
    signed_url = oauth_request.to_url()

    conn = urllib2.urlopen(signed_url, None)
    try:
        data = json.loads(conn.read())
    finally:
        conn.close()

    # return rating, total ratings
    return [ data['rating'], data['review_count'] ]
    

# get Google stats
def get_goog_stats(id):
    resp = requests.get('https://maps.googleapis.com/maps/api/place/details/json?placeid=' + id_lookup('goog', id) + '&key=' + config['goog_key'])
    
    if resp.status_code != 200:
        raise RuntimeError('goog places error')

    data = resp.json()
    # return rating, total ratings
    return [ data['result']['rating'], data['result']['user_ratings_total'] ]


# get FourSquare stats
def get_fs_stats(id):
    resp = requests.get('https://api.foursquare.com/v2/venues/' + id_lookup('fs', id) + '?client_id='+ config['fs_cid'] +'&client_secret='+ config['fs_cs'] +'&v=20160220')

    if resp.status_code != 200:
        raise RuntimeError('fs error')

    data = resp.json()
    # return rating, total ratings, total visits to venue
    return [ data['response']['venue']['rating'], data['response']['venue']['ratingSignals'] or 0, data['response']['venue']['stats']['visitsCount'] or 0]
    
def add_row_to_table(db_id, week, year, data):
    with con:
        cur = con.cursor()   
        cur.execute("INSERT INTO weeks VALUES("+ str(db_id) +", '"+ str(week) +"', "+ str(year) +", "+ 
            str(data['composite_rating']) +", "+ str(data['total_ratings']) +", "+ str(data['total_visits']) +", "+ 
            str(data['avg_ticket_price']) +", "+ str(data['num_games_price']) +", "+ 
            str(data['avg_attendance']) +", "+ str(data['num_games_atten']) +")")


# These dates will need to be changed every offseason
# Final date needs to be last sunday, unless last game is on a sunday, 
# bc we dont want postseason games included
def in_season(week):
    return date_config['2016']['season_start'] < str(week) < date_config['2016']['season_end']

# send myself an email if the script gets sandy
def sendTheCourier(msg): 
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login( config['email'], config['pass'] )
    server.sendmail( config['email'], config['email'], msg)
    server.quit()

def main():

    sendTheCourier("stadium db updating ... ")

    # this script will run every sunday morning
    # this script will only run during the regular season
    # for each MLB stadium, a new row will be entered into the table
    
    week = date.today()
    year = date.today().year

    if in_season(week) == False:
        sendTheCourier("... [*] [*] [*] Sir, I'm afraid that variety is not in season.")
        return

    for db_id in range(1, 31):
        try:
            metrics = get_metrics(db_id)
            add_row_to_table(db_id, week, year, metrics)
        except RuntimeError:
            print 'db_id: ' + str(db_id)
            sendTheCourier("[!] [!] [!] runtime error for stad: " + str(db_id))
        
    sendTheCourier("... script completed. what a beautiful back door breaking curve. buster really brushed that one by 'em")

if __name__ == '__main__':
    main()
