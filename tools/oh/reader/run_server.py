import os
import sys
import datetime
import logging
import psutil
import cProfile
import pstats
import StringIO

from flask import Flask, request, render_template, redirect, url_for
from flask_login import LoginManager, login_required, login_user
from pymongo.errors import ServerSelectionTimeoutError

from arbi.constants import ROOT_PATH
from arbi.utils import get_memory_usage
from arbi.tools.oh.constants import OH_TOOL_VER
from arbi.tools.oh.reader.login import User
from arbi.tools.oh.mongodb.db_engine import DBEngine
from arbi.tools.oh.reader.price_sensor import PriceSensor, HEADERS
from arbi.tools.oh.reader.pagination import Pagination


app = Flask(__name__)
app.secret_key = "my jfklsjfdjlsjdljflkdjf598405 secret"
app.config.from_object(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())

http_server = None


@login_manager.user_loader
def user_loader(username):
    if username in User.user_dict:
        return User(username)


@login_manager.request_loader
def request_loader(req):
    username = req.form.get('username')
    if username in User.user_dict:
        user = User(username)
        user.is_authenticated = req.form.get('password') == User.user_dict[username]
        return user


def start_db_engine():
    try:
        return DBEngine()
    except ServerSelectionTimeoutError as e:
        logging.error('Mongo DB server not available: {}'.format(e))
        sys.exit(1)


db_engine = start_db_engine()
price_sensor = PriceSensor()


def setup_local_logfile():
    path = os.path.join(ROOT_PATH, 'logs')
    if not os.path.exists(path):
        os.mkdir(path)
    log_file_name = 'oh_reader_server_log_{0}.log'.format(datetime.datetime.utcnow().strftime('%Y%m%d_%H-%M-%S'))
    logging.basicConfig(filename=os.path.join(path, log_file_name),
                        level=logging.INFO,
                        format='%(asctime)s %(message)s')


@app.route('/tools/oh/shutdown')
@login_required
def shutdown():
    if http_server:
        http_server.close()
        return 'Server shutting down...'


@app.route('/tools/oh/hw')
def hello_world():
    return 'Hello OH Tool!'


@app.route('/tools/oh/index')
@login_required
def show_oh_tool_main_page():
    return render_template('index.html', ver=OH_TOOL_VER)


@app.route('/tools/oh/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'username' in request.form:
        username = request.form['username']
        if request.form['password'] == User.user_dict.get(username):
            user = User(username)
            login_user(user)
            return redirect('/tools/oh/index')

    return render_template("login.html", ver=OH_TOOL_VER)


@app.route('/tools/oh/result', methods=['POST'])
@login_required
def get_vol_results():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    price_vol = request.form.get('price_vol')
    time_period = request.form.get('time_period')
    res = find_vol_results(start_date, end_date, price_vol, time_period)
    return render_template('result.html', results=res, headers=HEADERS)


@app.route('/demo/', defaults={'page': 1})
@app.route('/demo/page/<int:page>')
def demo_pagination(page):
    count = 1000
    users = range(1000)[page * 100: (page + 1) * 100]
    pagination = Pagination(page, 100, count)
    return render_template('demos/pagination.html',
        pagination=pagination,
        users=users
    )

def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


def find_vol_results(start_date, end_date, price_vol, time_period):
    start_date = str(start_date)
    end_date = str(end_date)
    date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    month = date.strftime('%b').lower()
    db_engine.select_month(month)
    cursor = db_engine.get_data_in_date_range(start_date, end_date)

    # pr = cProfile.Profile()
    # s = StringIO.StringIO()
    # pr.enable()

    res = price_sensor.find_all_situations(cursor, float(price_vol), int(time_period))

    # pr.disable()
    # ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    # ps.print_stats()
    # print s.getvalue()

    return res


def set_high_priority():
    """On our Windows servers somehow it takes much longer to process requests (1.7s vs 32s) which might be related to process priority"""
    p = psutil.Process(os.getpid())
    p.nice(psutil.HIGH_PRIORITY_CLASS)



if __name__ == '__main__':
    from gevent.wsgi import WSGIServer
    #set_high_priority()
    #setup_local_logfile()
    # app.add_template_global(enumerate, name='enumerate')
    app.jinja_env.globals['url_for_other_page'] = url_for_other_page
    #app.run(debug=True, use_debugger=False, use_reloader=False, host='0.0.0.0', port=8081, threaded=True)
    http_server = WSGIServer(('0.0.0.0', 8081), app)
    http_server.serve_forever()
