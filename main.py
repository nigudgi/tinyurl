from flask import Flask, request, render_template, redirect
from sqlite3 import OperationalError
import uuid, sqlite3, urllib2
import os
import time, datetime, logging
from flask import send_from_directory
from imp import find_module
from imp import load_module
from datetime import datetime

try:
    from urllib.parse import urlparse  # Python 3

    str_encode = str.encode
except ImportError:
    from urlparse import urlparse  # Python 2

    str_encode = str
try:
    from string import ascii_lowercase
    from string import ascii_uppercase
except ImportError:
    from string import lowercase as ascii_lowercase
    from string import uppercase as ascii_uppercase

# Assuming urls.db is in your app root folder
app = Flask(__name__)
app.config['SERVER_NAME'] = "localhost:8080"
host = 'http://localhost:8080/'

# Module name to be imported

# Location of the config file ./config.py
config_module = {'name': 'config', 'path': './config/'}

# Find the named module
fp, path_name, description = find_module(config_module['name'], [config_module['path']])

# load the module into a module variable
config = load_module(config_module['name'], fp, path_name, description)

logging.basicConfig(filename=config.logfile_path, level=logging.INFO)
logger = logging.getLogger(__name__)
hdlr = logging.FileHandler(config.logfile_path)
logger.addHandler(hdlr)


######################### Create a a SQLlite DB and Table if its not created################################
# GIVEN:
# EFFECT: Creates a DB and a Table
def table_check():
    create_table = '''CREATE TABLE IF NOT EXISTS WEB_URL
             (ID INTEGER PRIMARY KEY, URL TEXT NOT NULL, RSTRING TEXT NOT NULL)'''
    with sqlite3.connect(config.dbname) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(create_table)
        except OperationalError:
            pass

    # GIVEN: no arguments
    # EFFECT: Routes the requests coming to home page, Either creates a db entry or fetches the old entry


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        urlCheck = request.form.get('url')

        if not urlCheck:
            print "The url is an empty string"
            logger.info(
                "Not a Valid String" + str(datetime.utcnow()))
            return render_template(config.home_url)


        if valid_url_check(urlCheck) == False:
            print "Not a Valid String"
            logger.info(
                "Not a Valid String" + str(datetime.utcnow()))
            return render_template('home.html', not_url=urlCheck)

        url = urlCheck

        with sqlite3.connect('urls.db') as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT rowid FROM WEB_URL WHERE ID = ?", (onebyte_hash(url),))
            data = cursor.fetchone()
            if data is None:
                logger.info(
                    " Entry not found in the database, creating a new entry " + str(datetime.utcnow()))
                rstring = my_random_string(config.rstring_number)
                res = cursor.execute(
                    'INSERT INTO WEB_URL (ID, URL, RSTRING) VALUES (?, ?, ?)',
                    [onebyte_hash(url), urlencode(url), rstring]
                )
                encoded_string = str(res.lastrowid)
                logger.info(
                    encoded_string + " is the Encoded string " + str(datetime.utcnow()))

            else:
                logger.info(
                    " Entry found in the database, fetchin an old entry " + str(datetime.utcnow()))
                encoded_string = str(data[0])
                cursor.execute("SELECT RSTRING FROM WEB_URL WHERE ID = ?", (onebyte_hash(url),))
                data = cursor.fetchone()
                rstring = data[0]

            logger.info(
                host + rstring + encoded_string + " is the short url " + str(datetime.utcnow()))

        return render_template(config.home_url, short_url=host + rstring + encoded_string)
    return render_template(config.home_url)




    # GIVEN: Number of alphabets for combinations
    # EFFECT: Routes the requests coming to home page, Either creates a db entry or fetches the old entry

def my_random_string(string_length=10):
    """Returns a random string of length string_length."""
    random = str(uuid.uuid4())  # Convert UUID format to a Python string.
    random = random.upper()  # Make all characters uppercase.
    random = random.replace("-", "")  # Remove the UUID '-'.
    return random[0:string_length]  # Return the random string.



    # GIVEN: The short url substring
    # EFFECT: Routes the requests coming to the orignal url
@app.route('/<short_url>')
def redirect_short_url(short_url):
    # try:
    end = None
    short_url_row_id = short_url[6:end]
    decoded = int(short_url_row_id)
    # except ValueError:
    #    print('Non-numeric data found in the file.')

    url = host  # fallback if no URL is found

    with sqlite3.connect('urls.db') as conn:
        cursor = conn.cursor()
        res = cursor.execute('SELECT URL FROM WEB_URL WHERE ID=?', [decoded])
        try:
            short = res.fetchone()
            if short is not None:
                url = urldecode(short[0])
        except Exception as e:
            print(e)
    return redirect(url)

    # GIVEN: url string
    # EFFECT: Checks for a valid url
def valid_url_check(url):
    min_attr = ('scheme', 'netloc')
    try:
        result = urlparse(url)
        if all([result.scheme, result.netloc]):
            return True
        else:
            return False
    except:
        return False


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


def onebyte_hash(s):
    return hash(s) % 256


def urlencode(s):
    return urllib2.quote(s)


def urldecode(s):
    return urllib2.unquote(s).decode('utf8')


# This is the main function
def main():
    # This code checks whether database table is created or not
    table_check()
    app.run(debug=True)


if __name__ == '__main__':
    main()
