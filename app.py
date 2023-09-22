from flask import Flask, render_template, request, url_for, redirect
from pymysql import connections
import boto3
from config import *
app = Flask(__name__)
bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb
)

@app.route('/')
def index():
    print('Hello')
    return render_template('index.html')

@app.route('/index.html')
def index2():
    return render_template('index.html')

@app.route('/admin.html' ,methods=['GET'])
def admin():
    # Render the admin.html template from a templates folder in your project directory
    cursor = db_conn.cursor()

    cursor.execute('SELECT CompanyName, ApplicationDate, CompanyApplicationID FROM Company C, CompanyApplication CA, Admin A WHERE C.CompanyID = CA.CompanyID AND CA.AdminID = A.AdminID;')
    company_application_rows = cursor.fetchall()
    cursor.close()
    return render_template('admin.html' ,company_application_rows=company_application_rows)

@app.route('/approve_application', methods=['POST'])
def approve_application():
    application_id = request.form.get('application_id')
    cursor = db_conn.cursor()
    cursor.execute('UPDATE CompanyApplication SET ApplicationStatus = %s WHERE CompanyApplicationID = %s;', ('Approved', application_id,))
    db_conn.commit()
    cursor.close()
    return redirect('/admin.html')

@app.route('/reject_application', methods=['POST'])
def reject_application():
    application_id = request.form.get('application_id')
    cursor = db_conn.cursor()
    cursor.execute('UPDATE CompanyApplication SET ApplicationStatus = %s WHERE CompanyApplicationID = %s;', ('Rejected', application_id,))
    db_conn.commit()
    cursor.close()

    cursor = db_conn.cursor()
    cursor.execute('SELECT * FROM CompanyApplication;')
    columns = [desc[0] for desc in cursor.description]
    company_application_rows = cursor.fetchall()
    print("\nContents of the CompanyApplication table:")
    print(columns)
    for row in company_application_rows:
        print(row)

    return redirect('/admin.html')


@app.route('/company-application.html')
def company_application():
    # Render the admin.html template from a templates folder in your project directory
    return render_template('company-application.html')

@app.route('/lecturer.html')
def lecturer():
    # Render the admin.html template from a templates folder in your project directory
    return render_template('lecturer.html')

@app.route('/student.html')
def student():
    # Render the admin.html template from a templates folder in your project directory
    return render_template('student.html')

@app.route('/portfolio.html')
def portfolio():
    # Render the student.html template from a templates folder in your project directory
    return render_template('portfolio.html')

@app.route('/template.html')
def template():
    # Render the student.html template from a templates folder in your project directory
    return render_template('template.html')

@app.route('/lecturer-approve.html')
def lecturer_approve():
    # Render the student.html template from a templates folder in your project directory
    return render_template('lecturer-approve.html')

@app.route('/student-internship-application.html')
def student_internship_application():
    # Render the student.html template from a templates folder in your project directory
    return render_template('student-internship-application.html')

@app.route('/student-view-progress.html')
def student_view_progress():
    # Render the student.html template from a templates folder in your project directory
    return render_template('student-view-progress.html')

@app.route('/student-add-record.html')
def student_add_progress():
    # Render the student.html template from a templates folder in your project directory
    return render_template('student-add-record.html')

if __name__ == '__main__':
    app.run(debug=True)