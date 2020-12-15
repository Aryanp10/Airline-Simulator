# set schema 'gkrhgi';
    # command = "set schema 'gkrhgi'; "
    # cursor2.execute(command)


from flask import Flask
from flask import render_template, request, url_for, redirect, g, session, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import random, string
from decimal import Decimal

app = Flask(__name__)
app.secret_key = "123"
# pg_password = input("password do bhaisahab: ")
# port = input("port do bhaisahab 5432 or 5433: ")

outfile = open('airline_web_log.sql', 'w')


# app.config['postgreSQL_pool'] = psycopg2.pool.SimpleConnectionPool(1, 20,
#                                                                    user="postgres",
#                                                                    password=pg_password,
#                                                                    host="localhost",
#                                                                    port=port,
#                                                                    database="myDB")



app.config['postgreSQL_pool'] = psycopg2.pool.SimpleConnectionPool(1, 20,
                                                                   user="postgres",
                                                                #    password=pg_password,
                                                                   host="code.cs.uh.edu",
                                                                #    port=port,
                                                                   database="COSC3380")



def get_db():
    if 'db' not in g:
        g.db = app.config['postgreSQL_pool'].getconn()
    return g.db




@app.teardown_appcontext
def close_conn(e):
    db = g.pop('db', None)
    if db is not None:
        app.config['postgreSQL_pool'].putconn(db)




def genID(length):
    id = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(length)])
    return id


@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        from_city = request.form["from"]
        to_city = request.form["to"]
        dep_date = request.form["dep_date"]
        arrival_date = request.form["arrival_date"]
        flight_class = request.form.get('flight_class_selection')
        round_trip = request.form.get('round_trip')

        # CAN ADD MORE KEYS TO SESSION
        session['from_city'] = from_city.upper()
        session['to_city'] = to_city.upper()
        session['dep_date'] = dep_date
        session['arrival_date'] = arrival_date
        session['flight_class_selection'] = flight_class
        session['round_trip'] = round_trip

        if round_trip:
            session['round_yn'] = 'Y'
        else:
            session['round_yn'] = 'N'

        
        count = 0

        if from_city:
            count += 1
        if to_city:
            count += 1
        if dep_date:
            count += 1
        if arrival_date:
            count += 1 
        if flight_class:
            count += 1

        if count < 2:
            flash('You need to provide at least two conditions!')
            return render_template("index.html")

        return redirect(url_for("available_flights"))

    else:
        return render_template("index.html")


@app.route("/available_flights", methods=["POST", "GET"])
def available_flights():
    # if "from_city" in session or "to_city" in session:
    user_dict = session

    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor2 = db.cursor()

    command = "set schema 'gkrhgi'; "
    cursor2.execute(command)

    #TODO: Add date constraints
    # flights.scheduled_departure::date >= '2020-11-11' and flights.scheduled_departure::date < '2021-1-11';

    command = ""
    command2 = ""
    dep_city = ""
    arrival_city =""

    #TODO: if the user doesn't input any city!! - squash the bug, son!

    if user_dict['from_city'] and user_dict['to_city']:
        command += f"SELECT flight_id, flight_no, departure_airport, arrival_airport, status, "\
                    f"scheduled_departure::date, scheduled_arrival::date FROM flights " \
                    f"INNER JOIN airport AS dep_air ON " \
                    f"flights.departure_airport = dep_air.airport_code " \
                    f"INNER JOIN airport AS arr_air ON " \
                    f"flights.arrival_airport = arr_air.airport_code " \
                    f"WHERE "\
                    f"LOWER(dep_air.city) LIKE LOWER('%{user_dict['from_city']}%') " \
                    f"AND " \
                    f"LOWER(arr_air.city) LIKE LOWER('%{user_dict['to_city']}%') "\
                    f"ORDER BY flights.scheduled_departure ASC; "
        #f"SELECT * FROM flights " \

    elif user_dict['from_city']:    # gets all flights that match the departure city
        command += f"SELECT flight_id, flight_no, departure_airport, arrival_airport, status, "\
                    f"scheduled_departure::date, scheduled_arrival::date FROM flights " \
                    f"INNER JOIN airport ON " \
                    f"flights.departure_airport = airport.airport_code " \
                    f"WHERE LOWER(airport.city) LIKE LOWER('%{user_dict['from_city']}%'); "
    
    elif user_dict['to_city']:      # gets all flights that match the arrival city
        command += f"SELECT flight_id, flight_no, departure_airport, arrival_airport, status, "\
                    f"scheduled_departure::date, scheduled_arrival::date FROM flights " \
                    f"INNER JOIN airport ON " \
                    f"flights.arrival_airport = airport.airport_code " \
                    f"WHERE LOWER(airport.city) LIKE LOWER('%{user_dict['to_city']}%'); "

    cursor.execute(command)
    print(command, file=outfile)
                 
    flights_avail = cursor.fetchall()

    cursor2.execute(command)
    print(command, file=outfile)
    
    flight_city = list(cursor2.fetchall())

    '''connection flight '''
    '''
    if user_dict['from_city'] and user_dict['to_city']:
        command = "SELECT f1.flight_id, dep_air.city, arr_air.city, f2.flight_id, dep_air2.city, arr_air2.city FROM flights as f1 "\
                    "INNER JOIN flights as f2 ON "\
                    "f1.arrival_airport = f2.departure_airport "\
                    "INNER JOIN airport AS arr_air ON f1.arrival_airport = arr_air.airport_code "\
                    "INNER JOIN airport AS dep_air ON f1.departure_airport = dep_air.airport_code "\
                    "INNER JOIN airport AS arr_air2 ON f2.arrival_airport = arr_air2.airport_code "\
                    "INNER JOIN airport AS dep_air2 ON f2.departure_airport = dep_air2.airport_code "\
                    f"WHERE LOWER(dep_air.city) = LOWER('{user_dict['from_city']}') AND LOWER(arr_air2.city) = LOWER('{user_dict['to_city']}'); "
        
        cursor2.execute(command)
        flights_conn = cursor2.fetchall()) '''
        # print(command)
        
        # print(cursor2.fetchall())

    if not dep_city:
        dep_cities = []

        for fl in flight_city:
            command2 =  f"SELECT city FROM airport "\
                        f"INNER JOIN flights ON "\
                        f"flights.departure_airport = airport.airport_code "\
                        f"WHERE "\
                        f"LOWER(airport.airport_code) LIKE LOWER('%{fl[2]}%'); "
            # print(command2)
            cursor2.execute(command2)
            print(command2, file=outfile)
            dep_cities.append(cursor2.fetchone())

   
    if not arrival_city:
        arrival_cities = []

        for fl in flight_city:
            command2 =  f"SELECT city FROM airport "\
                        f"INNER JOIN flights ON "\
                        f"flights.arrival_airport = airport.airport_code "\
                        f"WHERE "\
                        f"LOWER(airport.airport_code) LIKE LOWER('%{fl[3]}%'); "
            cursor2.execute(command2)
            print(command2, file=outfile)
            arrival_cities.append(cursor2.fetchone())

  
    # these are the flight ids whose data is displayed on the screen
    flight_ids = []
    for fl in flight_city:
        flight_ids.append(fl[0])    
        
    cursor.close()
    # return render_template("available_flights.html", flights_avail=flights_avail,
    #                                     dep_cities=dep_cities, arrival_cities=arrival_cities)


    # when the person clicks on 'Select', the flight_id is printed in the console
    if request.method == 'POST':
        for f_id in flight_ids:
            if f"{f_id}-submit" in request.form:
                session['user_f_id'] = f_id

                # print(f"{f_id}")
                command = "SELECT "\
                            "scheduled_departure::date, scheduled_arrival::date, departure_airport, arrival_airport "\
                            "FROM flights "\
                            f"WHERE flight_id = {f_id}; "
                cursor2.execute(command)
                print(command, file=outfile)

                fl_details = cursor2.fetchall()
                
                command = "SELECT city, airport_name "\
                            "FROM airport "\
                            f"WHERE airport_code = '{fl_details[0][2]}'; "
                cursor2.execute(command)
                print(command, file=outfile)

                dep_details = cursor2.fetchall()

                command = "SELECT city, airport_name "\
                            "FROM airport "\
                            f"WHERE airport_code = '{fl_details[0][3]}'; "
                cursor2.execute(command)
                print(command, file=outfile)

                arr_details = cursor2.fetchall()

                command= f"SELECT scheduled_departure, scheduled_arrival FROM flights WHERE flight_id = '{f_id}'"
                cursor2.execute(command)
                print(command, file=outfile)

                dates = cursor2.fetchall()

                dep_time = dates[0][0]
                arr_time = dates[0][1]

                session['dep_city_'] = dep_details[0][0]
                session['arrival_city_'] = arr_details[0][0]
                session['dep_date_'] = fl_details[0][0]
                session['dep_time_'] = dep_time
                session['arr_time_'] = arr_time
                session['dep_airport_'] = dep_details[0][1]
                # print(dep_time, arr_time)
                return redirect(url_for('precheckout'))     

    return render_template("available_flights.html", flights=enumerate(flights_avail), dep_cities=dep_cities, arrival_cities=arrival_cities,
     from_city=session['from_city'], to_city=session['to_city'], round_yn = session['round_yn'])


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/precheckout", methods=["POST", "GET"])
def precheckout():
    if request.method == "POST":
        ''' Personal Info '''
        session['fname'] = request.form['fname']
        session['mname'] = request.form['mname']
        session['lname'] = request.form['lname']

        session['dob'] = request.form['dob']
        session['num_child'] = request.form['num_child']
        session['num_adult'] = request.form['num_adult']
        session['num_senior'] = request.form['num_senior']
        
        session['total_seats'] = int(session['num_child']) + int(session['num_adult']) + int(session['num_senior'])
        session['baggage'] = request.form.get('baggage')
        session['social_seats'] = request.form.get('social_seats')

        if session['social_seats']:
            session['social_yn'] = 'Y'
        else:
            session['social_yn'] = 'N'

        # print(session['total_seats'])
        # print(session['baggage'])

        # SKIPPED AMENITIES STUFF FOR NOW
        ''' Amenities '''
        session['meal'] = request.form.get('meal')
        session['smoking'] = request.form.get('smoking')
        session['movie'] = request.form.get('movie')
        session['wifi'] = request.form.get('WiFi')
        session['shower'] = request.form.get('shower')
        session['hot_towel'] = request.form.get('hot_towel')

        db = get_db()
        cursor = db.cursor()

        command = "set schema 'gkrhgi'; "
        cursor.execute(command)

        ''' BAGGAGE FEE!!!!!! '''

        command = "SELECT price "\
                  "FROM prices "\
                  "WHERE item = 'eco_flight'; "

        if session['flight_class_selection']:
            if session['flight_class_selection'] == 'First Class':
                command = "SELECT price "\
                  "FROM prices "\
                  "WHERE item = 'first_cls_flight'; "

            elif session['flight_class_selection'] == 'Business':
                command = "SELECT price "\
                  "FROM prices "\
                  "WHERE item = 'business_flight'; "

        
        cursor.execute(command)
        print(command, file=outfile)
        flight_amt = float(cursor.fetchone()[0])

        flight_amt = flight_amt * session['total_seats']

        all_amenities = ['meal', 'smoking', 'movie', 'wifi', 'shower', 'hot_towel']
        amenities_amt = 0
        baggage_cost = 0

        if int(session['baggage']) > 1:
            command = "SELECT price FROM prices "\
                        f"WHERE item = 'baggage'; "
            cursor.execute(command)
            print(command, file=outfile)

            baggage_cost += int(session['baggage']) * cursor.fetchone()[0]



        for am in all_amenities:
            if session[am]:
                command = "SELECT price "\
                            "FROM prices "\
                            f"WHERE item = '{am}'; "
                # print(command)
                cursor.execute(command)
                print(command, file=outfile)
                amenities_amt += cursor.fetchone()[0]
        
        tax_rate = 10
        # print(amenities_amt)
        
        total_tax = (flight_amt + float(amenities_amt) + float(baggage_cost))*(tax_rate/100)

        total_amt = float(flight_amt) + float(amenities_amt) + float(baggage_cost) + float(total_tax)
        total_amt = round(total_amt, 2)

        session['flight_amt'] = float(flight_amt) 
        session['amenities_amt'] = float(amenities_amt)
        session['tax_rate'] = float(tax_rate)
        session['total_tax'] = float(total_tax)
        session['total_amt'] = float(total_amt)
        session['baggage_cost'] = float(baggage_cost)

        if session['round_trip']:
            session['flight_amt'] = 2 * float(flight_amt) 
            session['amenities_amt'] = 2 * float(amenities_amt)
            session['total_tax'] = 2 * float(total_tax)
            session['total_amt'] = 2 * float(total_amt)
            session['baggage_cost'] = 2 * float(baggage_cost)





        ''' Need to make sure that the input is valid, otherwise ask user to reenter their details. '''

        ''' After reading the information from the user, redirect to the checkout page! '''

        # return redirect(url_for('checkout'))
        return redirect(url_for('payment'))
        

    return render_template('precheckout.html', dep_city=session['dep_city_'], arrival_city=session['arrival_city_'],
                                dep_date=session['dep_date_'], dep_airport=session['dep_airport_'] )



@app.route("/payment", methods=["POST", "GET"])
def payment():
    if request.method == "POST":
        session['name_bnk'] = request.form['name_bnk']
        session['email'] = request.form['email']
        session['phone'] = request.form['phone']

        session['address'] = request.form['address']
        session['city'] = request.form['city']
        session['state'] = request.form.get('state')
        session['zip'] = request.form['zip']

        session['cc_num'] = request.form['cc_num']
        session['cvv'] = request.form['cvv']
        session['exp_date'] = request.form['exp_date']

        return redirect(url_for('checkout'))

    return render_template('payment.html', flight_amt=session['flight_amt'], amenities_amt=session['amenities_amt'],
                    baggage_cost=session['baggage_cost'], tax_rate=session['tax_rate'], total_tax=session['total_tax'], total_amt=session['total_amt'])

@app.route("/checkout", methods=["POST", "GET"])
def checkout():

    
    amenities = []

    if session['meal']:
        amenities.append('Meal')
    if session['smoking']:
        amenities.append('Smoking Privilege')
    if session['movie']:
        amenities.append('Movie')
    if session['wifi']:
        amenities.append('WiFi')
    if session['shower']:
        amenities.append('Shower')
    if session['hot_towel']:
        amenities.append('Hot Towel')
    am_size = len(amenities)

    name = session['fname'] + ' ' + session['lname']
    addr = session['address'] + ', ' + session['city'] + ', ' + session['state'] + ' ' + session['zip']

    if request.method == "POST":
        ''' Insert user info into the db. '''

        db = get_db()
        cursor = db.cursor()

        command = "set schema 'gkrhgi'; "
        cursor.execute(command)


        ''' Generating IDs '''

        user_id = genID(18)
        add_id = genID(20)
        email_id = genID(15)
        card_id = genID(20)  # credit card id
        book_ref = genID(10)
        boarding_pass_id = genID(15)


        # user_id check
        id_num = 1

        while id_num != 0:
            user_id = genID(18)
            command = "SELECT COUNT(*) "\
                        f"FROM users WHERE user_id = '{user_id}'; "
            cursor.execute(command)
            print(command, file=outfile)
            id_num = cursor.fetchall()[0][0]

        # add_id check
        id_num = 1

        while id_num != 0:
            add_id = genID(20)
            command = "SELECT COUNT(*) "\
                        f"FROM address WHERE add_id = '{add_id}'; "
            cursor.execute(command)
            print(command, file=outfile)
            id_num = cursor.fetchall()[0][0]

        # email_id check
        id_num = 1

        while id_num != 0:
            email_id = genID(15)
            command = "SELECT COUNT(*) "\
                        f"FROM email WHERE email_id = '{email_id}'; "
            cursor.execute(command)
            id_num = cursor.fetchall()[0][0]

        # card_id check
        id_num = 1

        while id_num != 0:
            card_id = genID(20)  # credit card id
            command = "SELECT COUNT(*) "\
                        f"FROM credit_card WHERE card_id = '{card_id}'; "
            cursor.execute(command)
            print(command, file=outfile)
            id_num = cursor.fetchall()[0][0]
        
        # book_ref check
        id_num = 1

        while id_num != 0:
            book_ref = genID(10)
            command = "SELECT COUNT(*) "\
                        f"FROM bookings WHERE book_ref = '{book_ref}'; "
            cursor.execute(command)
            print(command, file=outfile)
            id_num = cursor.fetchall()[0][0]

    
        ''' End ID generation '''



        if not session['mname']:
            command = "INSERT INTO users VALUES "\
                    f"('{user_id}', '{session['fname']}', ' ', '{session['lname']}'); "
        else:
            command = "INSERT INTO users VALUES "\
                    f"('{user_id}', '{session['fname']}', '{session['mname']}', '{session['lname']}'); "
        cursor.execute(command)
        print(command, file=outfile)
        # ticket_no, flight_id, fare_condo, amount, user_id

        for _ in range(int(session['total_seats'])):
            id_num = 1
            t_no = 0
            while id_num != 0:
                t_no = genID(13)
                command = "SELECT COUNT(*) "\
                            f"FROM ticket_flights WHERE ticket_no = '{t_no}'; "
                cursor.execute(command)
                print(command, file=outfile)
                id_num = cursor.fetchall()[0][0]
            
        
            if session['flight_class_selection']:
                command = "INSERT INTO ticket_flights VALUES "\
                        f"('{t_no}', '{session['user_f_id']}', '{session['flight_class_selection']}', '1', '{user_id}'); "
                cursor.execute(command)
                print(command, file=outfile)
            else:
                command = "INSERT INTO ticket_flights VALUES "\
                        f"('{t_no}', '{session['user_f_id']}', 'Economy', 1, '{user_id}'); "
                cursor.execute(command)
                print(command, file=outfile)


            # boarding_pass_id
            id_num = 1 
            
            while id_num != 0:
                boarding_pass_id = genID(15)
                command = "SELECT COUNT(*) "\
                            f"FROM boarding_passes WHERE boarding_pass_id = '{boarding_pass_id}'; "
                cursor.execute(command)
                print(command, file=outfile)
                id_num = cursor.fetchall()[0][0]

            ''' Insert boarding_pass ''' 
            command = "INSERT INTO boarding_passes VALUES "\
                    f"('{boarding_pass_id}', '{t_no}', '{user_id}'); "
            cursor.execute(command)
            print(command, file=outfile)


        command = "INSERT INTO misc VALUES "\
                    f"('{user_id}', '{session['social_yn']}', '{session['total_seats']}','{session['baggage']}'); "
        cursor.execute(command)
        print(command, file=outfile)
        
        command = "INSERT INTO flight_id VALUES "\
                    f"('{user_id}', '{session['user_f_id']}'); "
        cursor.execute(command)
        print(command, file=outfile)

        command = "UPDATE flights\n" \
              "SET seats_available = seats_available - 1,\n" \
              "seats_booked = seats_booked + 1\n" \
              f"WHERE flight_id = {session['user_f_id']};\n"
        cursor.execute(command)
        print(command, file=outfile)

        command = "INSERT INTO bookings VALUES "\
                    f"('{book_ref}', NOW(), '{session['total_amt']}', '{session['round_yn']}', '{user_id}'); "
        cursor.execute(command)
        print(command, file=outfile)

        command = "INSERT INTO address VALUES "\
                f"('{add_id}', '{session['address']}', '{session['city']}', '{session['state']}', '{user_id}'); "
        cursor.execute(command)
        print(command, file=outfile)

        command = "INSERT INTO email VALUES "\
                f"('{email_id}', '{session['email']}', '{user_id}'); "
        cursor.execute(command)
        print(command, file=outfile)

        command = "INSERT INTO credit_card VALUES "\
                f"('{card_id}', '{session['cc_num']}', '{session['cvv']}', '{session['exp_date']}', '{user_id}'); "
        cursor.execute(command)
        print(command, file=outfile)


        db.commit()
        cursor.close()

        
        return redirect(url_for('confirmation'))
    else:
        return render_template("checkout.html", dep_city=session['dep_city_'], arrival_city=session['arrival_city_'], f_id=session['user_f_id'],
                    name=name, dob=session['dob'], num_tickets=session['total_seats'], 
                    num_bag=session['baggage'], name_bnk=session['name_bnk'], addr=addr,
                    cc_num=session['cc_num'], cvv=session['cvv'], exp=session['exp_date'],
                    amenities=enumerate(amenities), am_size=am_size, email=session['email'], phone=session['phone'],
                    dep_date=session['dep_time_'], arr_date=session['arr_time_'], social_yn = session['social_yn'])

@app.route("/confirmation")
def confirmation():
    db = get_db()
    cursor = db.cursor()

    command = "set schema 'gkrhgi'; "
    cursor.execute(command)


    
    # command = f"SELECT user_id from users WHERE f_name LIKE '%{session['fname']}%' limit 1;"
    command = "SELECT user_id from bookings ORDER BY book_date DESC limit 1;"
    cursor.execute(command)
    print(command, file=outfile)
    uID = cursor.fetchone()[0]

    command = f"SELECT total_amount from bookings WHERE user_id LIKE '%{uID}%'"
    cursor.execute(command)
    print(command, file=outfile)
    total = cursor.fetchone()[0]

    db.commit()
    cursor.close()

    name = session['fname'] + ' ' + session['lname']
    return render_template("confirmation.html", user_id=uID, name = name, total = total)

@app.route("/cancel", methods=["POST", "GET"])
def cancel():
    if request.method == "POST":
        db = get_db()
        cursor = db.cursor()

        command = "set schema 'gkrhgi'; "
        cursor.execute(command)


        session['cancel_id'] = request.form['cancel_id']
        session['cancel_email'] = request.form['cancel_email']

        cancel_id = session['cancel_id']
        cancel_email = session['cancel_email']       

        if cancel_id:
            command = f"SELECT COUNT(*) FROM users WHERE user_id LIKE '%{cancel_id}%'"
            cursor.execute(command)
            print(command, file=outfile)
            count = cursor.fetchone()[0]
            if count>=1:
                command = f"SELECT f_name FROM users WHERE user_id LIKE '%{cancel_id}%' limit 1"
                cursor.execute(command)
                print(command, file=outfile)
                name = cursor.fetchone()[0]

                command = f"SELECT total_amount FROM bookings WHERE user_id LIKE '%{cancel_id}%' limit 1"
                cursor.execute(command)
                print(command, file=outfile)
                total = cursor.fetchone()[0]

                command = f"SELECT flight_id FROM flight_id WHERE user_id LIKE '%{cancel_id}%' limit 1"
                cursor.execute(command)
                f_id = cursor.fetchone()[0]
                
                command = f"DELETE FROM address WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command = f"DELETE FROM boarding_passes WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command = f"DELETE FROM email WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command = f"DELETE FROM misc WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command = f"DELETE FROM flight_id WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command = f"DELETE FROM credit_card WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command =  f"DELETE FROM bookings WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command =  f"DELETE FROM ticket_flights WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command =  f"DELETE FROM users WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command = "UPDATE flights\n" \
                    "SET seats_available = seats_available + 1,\n" \
                    "seats_booked = seats_booked - 1\n" \
                    f"WHERE flight_id = {f_id};\n"
                cursor.execute(command)
                print(command, file=outfile)

                db.commit()
                cursor.close()

                flash(f'Cancellation Successful! Order Number: {cancel_id} by {name} has been cancelled. A total amount of ${total} will be refunded  within the next 3-7 business days.')
            else:
                flash(f'Order Number {cancel_id} DOES NOT EXIST')

        elif cancel_email:
            command = f"SELECT COUNT(*) FROM email WHERE email LIKE '%{cancel_email}%';"
            cursor.execute(command)
            print(command, file=outfile)
            count = cursor.fetchone()[0]
            if count>=1:
                command = f"SELECT user_id FROM email WHERE email LIKE '%{cancel_email}%' limit 1;"
                cursor.execute(command)
                print(command, file=outfile)
                cancel_id = cursor.fetchone()[0]

                command = f"SELECT f_name FROM users WHERE user_id LIKE '%{cancel_id}%' limit 1"
                cursor.execute(command)
                print(command, file=outfile)
                name = cursor.fetchone()[0]

                command = f"SELECT total_amount FROM bookings WHERE user_id LIKE '%{cancel_id}%' limit 1"
                cursor.execute(command)
                print(command, file=outfile)
                total = cursor.fetchone()[0]

                command = f"SELECT flight_id FROM flight_id WHERE user_id LIKE '%{cancel_id}%' limit 1"
                cursor.execute(command)
                f_id = cursor.fetchone()[0]
                
                command = f"DELETE FROM address WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command = f"DELETE FROM boarding_passes WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command = f"DELETE FROM email WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command = f"DELETE FROM misc WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command = f"DELETE FROM flight_id WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command = f"DELETE FROM credit_card WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command =  f"DELETE FROM bookings WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command =  f"DELETE FROM ticket_flights WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command =  f"DELETE FROM users WHERE user_id LIKE '%{cancel_id}%'"
                cursor.execute(command)
                print(command, file=outfile)
                command = "UPDATE flights\n" \
                    "SET seats_available = seats_available + 1,\n" \
                    "seats_booked = seats_booked - 1\n" \
                    f"WHERE flight_id = {f_id};\n"
                cursor.execute(command)
                print(command, file=outfile)

                db.commit()
                cursor.close()

                flash(f'Cancellation Successful! Ticket under {cancel_email} by {name} has been cancelled. A total amount of ${total} will be refunded  within the next 3-7 business days.')
            else:
                flash(f'Email {cancel_email} DOES NOT EXIST')
        return render_template("cancel.html")
    return render_template("cancel.html")

@app.route("/details", methods=["POST", "GET"])
def details():
    if request.method == "POST":
        db = get_db()
        cursor = db.cursor()

        command = "set schema 'gkrhgi'; "
        cursor.execute(command)


        session['detail_email'] = request.form['details_email']
        detail_email = session['detail_email']

        command = f"SELECT COUNT(*) FROM email WHERE email LIKE '%{session['detail_email']}%';"
        cursor.execute(command)
        print(command, file=outfile)
        count = cursor.fetchone()[0]
        if count>=1:
            command = f"SELECT user_id FROM email WHERE email LIKE '%{session['detail_email']}%' limit 1;"
            cursor.execute(command)
            print(command, file=outfile)
            details_id = cursor.fetchone()[0]

            command = f"SELECT f_name, l_name FROM users WHERE user_id LIKE '%{details_id}%';"
            cursor.execute(command)
            print(command, file=outfile)           
            table = cursor.fetchone()
            # table spits out a list of lists where each list is a column i think
            name = table[0] + ' '  + table[1]

            command = f"SELECT social_distance, num_seats, num_bags FROM misc WHERE user_id LIKE '%{details_id}%';"
            cursor.execute(command)
            print(command, file=outfile)
            table = cursor.fetchall()
            social_yn = table[0][0]
            num_seats = table[0][1]
            num_bags = table[0][2]

            command = f"SELECT flight_id FROM flight_id WHERE user_id LIKE '%{details_id}%';"
            cursor.execute(command)
            print(command, file=outfile)
            f_id = cursor.fetchone()[0]

            command = f"SELECT scheduled_departure, scheduled_arrival, departure_airport, arrival_airport, status FROM flights WHERE flight_id = '{f_id}';"
            cursor.execute(command)
            print(command, file=outfile)           
            table = cursor.fetchall()
            dep_date = table[0][0]
            arr_date = table[0][1]
            dep_airport = table[0][2]
            arr_airport = table[0][3]
            status = table[0][4]
            db.commit()
            cursor.close()
            return render_template("passenger_details.html", uID=details_id, name=name, social_yn =social_yn, num_seats=num_seats, num_bags=num_bags, f_id=f_id,
                                    dep_date=dep_date, arr_date=arr_date, dep_airport=dep_airport, arr_airport=arr_airport, status=status)
        else:
            flash(f'Email {detail_email} DOES NOT EXIST')

        
        

    return render_template("details.html")

@app.route("/passenger_details")
def passenger_details():
    return render_template("passenger_details.html")

@app.route("/passengers")
def passengers():
    db = get_db()
    
    cursor = db.cursor(cursor_factory=RealDictCursor)

    command = "set schema 'gkrhgi'; "
    cursor.execute(command)

    
    passenger_list = []



    command = f"SELECT f_name, l_name, flight_id, book_date::date FROM users INNER JOIN bookings ON users.user_id = bookings.user_id INNER JOIN flight_id ON users.user_id = flight_id.user_id"
    cursor.execute(command)
    print(command, file=outfile)
    passenger_list = cursor.fetchall()
    for passenger in passenger_list:
        passenger['l_name'] = str(passenger['l_name'][0])
        passenger['book_date'] = str(passenger['book_date'])

    db.commit()
    cursor.close()
    return render_template("passengers.html", passenger_list = passenger_list)


if __name__ == "__main__":
    app.run()
