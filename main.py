from urllib.parse import urlparse, urljoin

import boto3
from flask import Flask, render_template, request, redirect, url_for, Response, json, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from passlib.hash import pbkdf2_sha256

import Forms.web_forms as web_forms
from User.user import User
from Utils import util_basic
from Utils.config import db
from Utils.driver_generation import generate_cars, modified_k_means
from Utils.log import log
from Utils.util_basic import bucket_name
from Utils.util_basic import create_workout, build_graph_data

application = Flask(__name__)
# TODO Update secret key and move to external file
application.secret_key = 'super secret string'  # Change this!
application.debug = True

login_manager = LoginManager()
login_manager.init_app(application)

# redirect unauthorized view to login page
login_manager.login_view = 'new_signup'


def sign_certificate(resource_name):
    client = boto3.client('s3')
    url = client.generate_presigned_url('get_object', Params={'Bucket': bucket_name,
                                                              'Key': resource_name}, ExpiresIn=60)
    return url


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@login_manager.user_loader
def load_user(user_id):
    try:
        return User(user_id)
    except ValueError:
        return None


@application.route('/', methods=['GET', 'POST'])
def new_signup():
    # forms to handle sign up and sign in
    signup_form = web_forms.SignUpForm()
    signin_form = web_forms.SignInForm()

    login = True

    if request.method == 'POST':
        if signin_form.data['submit_bttn']:
            if signin_form.validate_on_submit():
                username = signin_form.data['username_field']
                password = signin_form.data['password_field']

                result = db.select('users', ['password', 'user_id'], ['username'], [username])

                if result:
                    hash = result['password']
                    password_match = pbkdf2_sha256.verify(password, hash)
                    if password_match:
                        curr_user = User(result['user_id'])
                        login_user(curr_user)

                        next_url = request.args.get('next')

                        if not is_safe_url(next_url):
                            return abort(400)

                        return redirect(next_url or url_for('profile'))

                signin_form.username_field.errors.append("Invalid Username or Password.")

        elif signup_form.data['submit']:
            if signup_form.validate():
                # log new user in
                curr_user = User.user_from_form(signup_form.data)
                login_user(curr_user)

                # redirect user to their new profile page
                return redirect(url_for('profile'))

            login = False

    return render_template('new_signup.html', sign_up=signup_form, sign_in=signin_form, login=login,
                           _url=sign_certificate('defaults/login_photo.jpg'))


@application.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():

    form = web_forms.ProfileForm()

    if form.validate_on_submit():
        user_attrs = ['address', 'city', 'state', 'zip', 'phone', 'team', 'num_seats']
        profile_attrs = ['bio']
        user_cols = []
        profile_cols = []
        for attribute in user_attrs:
            user_cols.append(form.data[attribute])
            setattr(current_user, attribute, form.data[attribute])

        for attribute in profile_attrs:
            profile_cols.append((form.data[attribute]))

        db.update('users', user_attrs, user_cols, ['user_id'], [current_user.user_id])

        db.update('profile', profile_attrs, profile_cols, ['user_id'], [current_user.user_id])

    # gather user profile
    user_profile = db.select('profile', ['ALL'], ['user_id'], [current_user.get_id()])

    if current_user.num_seats > 0:
        form.num_seats.data = int(current_user.num_seats)
    if form.team:
        form.team.data = current_user.team
    if current_user.address:
        form.address.data = current_user.address
    if current_user.state:
        form.state.data = current_user.state
    if current_user.city:
        form.city.data = current_user.city
    if current_user.zip:
        form.zip.data = current_user.zip
    if current_user.phone:
        form.phone.data = current_user.phone

    form.num_seats.data = current_user.num_seats
    form.bio.data = user_profile['bio']

    return render_template('profile_5.html', form=form, profile=user_profile, sign_certificate=sign_certificate)


@application.route('/userlist')
@login_required
def userlist():
    users = db.select('users', ['ALL'], order_by=['username'])

    return render_template('userlist.html', user_list=users)


@application.route('/workouts', methods=['GET', 'POST'])
@login_required
def workouts():
    if request.method == 'POST':

        # TODO implement other workouts

        # get the parameters from the form
        meters = request.form.getlist('meters[]')
        minutes = request.form.getlist('minutes[]')
        seconds = request.form.getlist('seconds[]')

        if meters != [''] and minutes != [''] and seconds != ['']:

            # is workout by distance or by time?
            by_distance = False
            if request.form.get('workout_type') == 'Distance':
                by_distance = True

            # add workout to database
            create_workout(current_user.user_id, db, meters, minutes, seconds, by_distance)

            return Response(json.dumps({}), status=201, mimetype='application/json')

    return render_template('workout.html')


@application.route('/logout')
@login_required
def logout():
    log.info('Logging out user id:%s' % current_user.user_id)
    logout_user()
    return redirect(url_for('new_signup'))


@application.route('/get_a_workout', methods=['POST'])
@login_required
def get_a_workout():
    workout_id = request.form.get('workout_id')
    result = db.get_workouts_by_id(current_user.user_id, workout_id)
    js = json.dumps(result)
    return Response(js, status=200, mimetype='application/json')


@application.route('/get_all_workouts', methods=['GET'])
@login_required
def get_all_workouts():
    workouts = db.get_aggregate_workouts_by_id(current_user.user_id)
    return Response(json.dumps(workouts), status=200, mimetype='application/json')


@application.route('/edit_workout', methods=['POST'])
@login_required
def edit_workout():
    util_basic.edit_erg_workout(request, db)
    return Response(json.dumps({}), status=201, mimetype='application/json')


@application.route('/generate_graph_data', methods=['POST'])
@login_required
def generate_graph_data():
    if request.method == 'POST':
        workout_name = request.form.get('share')

        if workout_name:
            results = db.get_aggregate_workouts_by_name(current_user.user_id, workout_name)

            if results and len(results) > 0:
                js = build_graph_data(results, workout_name)

                return Response(js, status=200, mimetype='application/json')

    return Response({}, status=400, mimetype='application/json')


@application.route('/get_workout_names', methods=['GET'])
@login_required
def get_workout_names():
    workout_names = db.find_all_workout_names(current_user.user_id)
    js = json.dumps(workout_names)
    return Response(js, status=200, mimetype='application/json')


@application.route('/delete_workout', methods=['POST'])
@login_required
def delete_workout():
    workout_id = request.form.get('workout_id')
    db.delete_entry('workout', 'workout_id', workout_id)
    return Response(json.dumps({}), 201, mimetype='application/json')


@application.route('/get_all_athletes', methods=['GET'])
@login_required
def get_all_athletes():
    users = db.select('users', ['ALL'], fetchone=False)
    js = json.dumps(users)
    return Response(js, status=200, mimetype='application/json')


@application.route('/roster')
@login_required
def roster():
    return render_template('roster_page.html')

  
@application.route('/save_img', methods=['POST'])
@login_required
def save_img():

    img = request.form.get('img')

    if img:
        pic_location = util_basic.upload_profile_image(img, current_user.user_id, current_user.picture)

        # update current user
        current_user.picture = pic_location

        # update the database
        db.update('profile', ['picture'], [pic_location], ['user_id'], [current_user.user_id])

        # sign certificate
        signed_url = sign_certificate(pic_location)

        return Response(json.dumps({'img_url': signed_url}), status=201, mimetype='application/json')

    return Response(json.dumps({}), status=400, mimetype='application/json')


@application.route('/drivers', methods=['GET', 'POST'])
@login_required
def drivers():
    if request.method == 'POST':
        athletes = request.form.getlist('athletes[]')
        drivers = request.form.getlist('drivers[]')
        print(athletes, drivers)

        drivers_arr, athelete_dict = generate_cars(athletes, drivers)
        modified_k_means(drivers_arr, athelete_dict)

        return render_template('drivers.html')
    else:
        print('ok')
        return render_template('drivers.html')


@application.route('/no_login')
def no_login():
    return 'no login required'
      

if __name__ == '__main__':
    log.info('Begin Main')
    application.run()
