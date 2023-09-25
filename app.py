from flask import Flask, render_template, request, url_for, redirect, flash, jsonify
from pymysql import connections
import boto3
from config import *
from datetime import datetime
app = Flask(__name__)

bucket = 'ongmingzheng-bucket' # Need to change the bucket name follow assignment specification
region = 'us-east-1'

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
    cursor = db_conn.cursor()
    cursor.execute('SELECT CompanyName, RequiredSkillSet, InternshipBenefit, ApplicationDate, CompanyApplicationID, ApplicationStatus, S3Key FROM Company C, CompanyApplication CA, Admin A WHERE C.CompanyID = CA.CompanyID AND CA.AdminID = A.AdminID;')
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
    return jsonify(status="success", action="approved")

@app.route('/reject_application', methods=['POST'])
def reject_application():
    application_id = request.form.get('application_id')
    cursor = db_conn.cursor()
    cursor.execute('UPDATE CompanyApplication SET ApplicationStatus = %s WHERE CompanyApplicationID = %s;', ('Rejected', application_id,))
    db_conn.commit()
    cursor.close()
    return jsonify(status="success", action="rejected")

@app.route('/company-application.html')
def company_application():
    # Render the admin.html template from a templates folder in your project directory
    return render_template('company-application.html')


@app.route('/submit_company_application', methods=['POST'])
def submit_company_application():
    #Fetch the last companyID from database
    cursor = db_conn.cursor()
    search_sql = "SELECT max(CompanyID) from Company"
    cursor.execute(search_sql)
    fetched_comp_id = cursor.fetchone()[0]
    cursor.close()
    
    #Fetch admin ID from database
    cursor = db_conn.cursor()
    search_sql = "SELECT AdminID from Admin"
    cursor.execute(search_sql)
    admin_id = cursor.fetchone()[0]
    cursor.close()

    #Fetch company application ID from database
    cursor = db_conn.cursor()
    search_sql = "SELECT max(CompanyApplicationID) from CompanyApplication"
    cursor.execute(search_sql)
    fetched_comp_app_id = cursor.fetchone()[0]
    if fetched_comp_app_id is None:
        fetched_comp_app_id = 0
    cursor.close()

    comp_id = int(fetched_comp_id) + 1
    comp_app_id = int(fetched_comp_app_id) + 1
    comp_name = request.form['companyName']
    comp_add = request.form['companyAddress']
    comp_email = request.form['companyEmailAddress']
    comp_size = request.form['companySize']
    comp_desc = request.form['companyDesc']
    required_quali = request.form['requiredQual']
    internship_pos = request.form['internshipPosition']
    internship_allowance = request.form['internshipAllowance']
    app_status = 'F'
    curr_date = datetime.utcnow().date()
    # comp_img = request.files['uploadCompany']

    # Insert values into Company table
    cursor = db_conn.cursor()
    insert_sql1 = "INSERT INTO Company VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.execute(insert_sql1, (str(comp_id), comp_name, comp_add, comp_email, comp_size, comp_desc))
    db_conn.commit()
    cursor.close()

    #Insert values into CompanyApplication table
    cursor = db_conn.cursor()
    insert_sql2 = "INSERT INTO CompanyApplication VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    cursor.execute(insert_sql2, (str(comp_app_id), str(comp_id), required_quali, internship_pos, internship_allowance, 'Pending', admin_id, str(curr_date), 'null'))
    cursor.execute("SET FOREIGN_KEY_CHECKS=1") 
    db_conn.commit()
    cursor.close()

    # File upload
    uploaded_file = request.files['uploadCompany']
    print(request.files)

    if uploaded_file and uploaded_file.filename != '':
        try:
            # Initialize the S3 client
            s3 = boto3.resource('s3', region_name='us-east-1', 
                                aws_access_key_id='ASIA2RKLRXNIPBQCAP6M',
                                aws_secret_access_key='nxDxJ9jcUN03eTHV72/h/+O/O9RbH2bMSb5hH+gU',
                                aws_session_token='FwoGZXIvYXdzEHMaDElgMTBUFQMNYaid4CLPAXB4Q3dtjqrcWRWjHEh9IYrul8qxBomCWwS2cAJDEq2HlhjE/G0PXbDbQZqcmn9uqAhhqTa29ovYwT52RyJnv8QJ/zoGyfogp/acnUxaVWqrkZhLGhXI6BgQIGVSrxXLj++wZmP8h9M0Jzc3Vt7e1/KYiLcPdCOV7fKqdrCWWglGtjon/R/jVjTLen0r17Rgs/6/OGBkqf6/1HGxWoqA6ZKInXcajrSKI+Qx14s6KZmHoS+0RWOhvANXUwQC/dgRptUhHVMpWFsZ9GHVEoDVLyj0tMWoBjItB2yylrodJaSoM0pYypCeCM/+d0I0FZEuFhsbX27hJmkgRUIyb+PGldYfRdRR'
                                ) 

            # Set a unique key for the uploaded file in S3
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            s3_key = f'company_images/{timestamp}_{uploaded_file.filename}'
            
            # Upload the file
            s3.Bucket(bucket).put_object(Key=s3_key, Body=uploaded_file) 

            # Store S3 Key in database
            cursor = db_conn.cursor()
            update_sql = "UPDATE CompanyApplication SET S3Key = %s WHERE CompanyApplicationID = %s"
            cursor.execute(update_sql, (s3_key, str(comp_app_id)))
            db_conn.commit()
            cursor.close()

        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('index'))
    else:
        flash('No file selected!', 'error')
        return redirect(url_for('index'))

    return render_template('/template.html')

@app.route('/lecturer.html')
def lecturer():
    # Render the admin.html template from a templates folder in your project directory
    cursor = db_conn.cursor()
    cursor.execute('SELECT S.StudentName, S.StudentID, S.Programme, S.S3Key FROM Lecturer L, StudentInternship SI, Student S WHERE L.LecturerID = SI.LecturerID AND SI.StudentID = S.StudentID;')
    student_list = cursor.fetchall()
    cursor.close()
    # Render the admin.html template from a templates folder in your project directory
    return render_template('lecturer.html', student_list=student_list )

@app.route('/student.html', methods=['GET'])
def student():
    # Render the admin.html template from a templates folder in your project directory
    cursor = db_conn.cursor()
    cursor.execute("SELECT StudentName, S.StudentID, Programme, StartDate, EndDate, InternshipStatus FROM Student S, StudentInternship SI WHERE S.StudentID = SI.StudentID AND S.StudentID='12WMR0001';")
    student_info = cursor.fetchall()
    cursor.close()
    return render_template('student.html' ,student_info_rows=student_info)

@app.route('/portfolio.html')
def portfolio():
    # Render the student.html template from a templates folder in your project directory
    return render_template('portfolio.html')

@app.route('/template.html')
def template():
    # Render the student.html template from a templates folder in your project directory
    return render_template('template.html')

@app.route('/lecturer-approve-this')
def lecturer_approve_this():
    studentID = request.args.get('studentID')
    imageUrl = request.args.get('imageUrl')
    print(studentID)
    internship_progress = ()
    try:
        # Query for student information
        InternshipID = ''
        with db_conn.cursor() as cursor:
            sqlQuery1 = f"""SELECT S.StudentName, S.StudentID, S.Programme, SI.StartDate, SI.EndDate, S.StudyStatus, SI.InternshipID FROM Student S, StudentInternship SI WHERE S.StudentID = SI.StudentID AND S.StudentID = '{studentID}';"""
            cursor.execute(sqlQuery1)
            student_record = cursor.fetchall()

            if not student_record:
                # Handle the case where no student record is found
                return "Student not found"

            student_info = {
                'StudentName': student_record[0][0],
                'StudentID': student_record[0][1],
                'Programme': student_record[0][2],
                'StartDate': student_record[0][3],
                'EndDate': student_record[0][4],
                'StudyStatus': student_record[0][5]
            }
            InternshipID = student_record[0][6]

            # Query for internship progress (reuse the same cursor)
            sqlQuery2 = f"""SELECT SP.Date, SP.Description, SP.ApprovalStatus, SP.StudentProgressID FROM StudentInternship SI, StudentProgress SP WHERE SI.InternshipID = SP.InternshipID AND SP.InternshipID = '{InternshipID}';"""
            cursor.execute(sqlQuery2)
            internship_progress = cursor.fetchall()

    except Exception as e:
        # Handle database errors or exceptions
        return f"An error occurred: {str(e)}"
    print('Done reading from Database')
    print(f'Internship ID: {InternshipID}')
    print(internship_progress)
    # Render the student.html template from a templates folder in your project directory
    return render_template('lecturer-approve.html', internship_progress=internship_progress, student_info=student_info, imageUrl=imageUrl)


@app.route('/approved.html')
def lecturer_approve():
    StudentProgressID = request.args.get('StudentProgressID')
    sqlQuery = f""" UPDATE StudentProgress
                    SET ApprovalStatus = 'Approved'
                    WHERE StudentProgressID = '{StudentProgressID}';
"""
    cursor = db_conn.cursor()
    cursor.execute(sqlQuery)
    db_conn.commit()
    cursor.close()
    return render_template('approved.html')

@app.route('/rejected.html')
def lecturer_reject():
    StudentProgressID = request.args.get('StudentProgressID')
    sqlQuery = f""" UPDATE StudentProgress
                    SET ApprovalStatus = 'Rejected'
                    WHERE StudentProgressID = '{StudentProgressID}';
"""
    cursor = db_conn.cursor()
    cursor.execute(sqlQuery)
    db_conn.commit()
    cursor.close()

    return render_template('rejected.html')

@app.route('/student-internship-application.html')
def student_internship_application():
    # Render the student.html template from a templates folder in your project directory
    return render_template('student-internship-application.html')

@app.route('/submit_internship_application', methods=['GET','POST'])
def submit_student_internship_application():

    stu_name = request.form['studentName']
    stu_id = request.form['studentID']
    stu_add = request.form['studentAddress']
    stu_email = request.form['studentEmailAddress']
    stu_prog = request.form['studentProgramme']
    stu_intern_co = request.form['studentInternCompany']
    stu_intern_start_date = request.form['studentInternStartDate']
    stu_intern_end_date = request.form['studentInternEndDate']
    stu_study_intern_status = 'T'
    stu_intern_pos = 'Intern'

    #Fetch last internship ID from database
    cursor = db_conn.cursor()
    search_sql = "SELECT max(InternshipID) from StudentInternship"
    cursor.execute(search_sql)
    fetched_intern_id = cursor.fetchone()[0]
    stu_intern_id = int(fetched_intern_id) + 1
    cursor.close()

    #Fetch lecture ID from database
    cursor = db_conn.cursor()
    search_sql = "SELECT max(LecturerID) from Lecturer"
    cursor.execute(search_sql)
    lec_id = cursor.fetchone()[0]
    cursor.close()

    #Find company ID with company name from database
    cursor = db_conn.cursor()
    stu_intern_co = stu_intern_co.lower()
    search_sql = "SELECT CompanyID FROM Company WHERE LOWER(CompanyName)=%s"
    cursor.execute(search_sql, (stu_intern_co))
    co_id = cursor.fetchone()[0]
    cursor.close()

    # Insert values into Student table
    cursor = db_conn.cursor()
    insert_sql1 = "INSERT INTO Student (StudentID, StudentName, StudentEmail, StudentAddress, Programme, StudyStatus) VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.execute(insert_sql1, (stu_id, stu_name, stu_email, stu_add, stu_prog, stu_study_intern_status))
    db_conn.commit()
    cursor.close()

    # Insert values into StudentInternship table
    cursor = db_conn.cursor()
    insert_sql2 = "INSERT INTO StudentInternship VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    cursor.execute(insert_sql2, (str(stu_intern_id), stu_id, lec_id, co_id, stu_intern_start_date, stu_intern_end_date, stu_intern_pos, stu_study_intern_status))
    cursor.execute("SET FOREIGN_KEY_CHECKS=1")
    db_conn.commit()
    cursor.close()

    return render_template('/template.html')

@app.route('/student-view-progress.html', methods=['GET'])
def student_view_progress():
    # Render the student.html template from a templates folder in your project directory

    # Student info display
    cursor = db_conn.cursor()
    cursor.execute("SELECT StudentName, S.StudentID, Programme, StartDate, EndDate, InternshipStatus FROM Student S, StudentInternship SI WHERE S.StudentID = SI.StudentID AND S.StudentID='12WMR0001';")
    student_info = cursor.fetchall()
    cursor.close()

    # Student progress display
    cursor = db_conn.cursor()
    cursor.execute("SELECT Date, Description, ApprovalStatus FROM StudentProgress;")
    stu_progress = cursor.fetchall()
    cursor.close()

    return render_template('student-view-progress.html' ,student_info_rows=student_info, stu_progress_rows=stu_progress)

@app.route('/student-add-record.html')
def student_add_progress():
    # Render the student.html template from a templates folder in your project directory
    return render_template('student-add-record.html')

@app.route('/add_new_record', methods=['POST'])
def add_progress_record():
    rec_date = request.form['recordDate']
    rec_assg = request.form['assignment']

    #Fetch last StudentProgress ID from database
    cursor = db_conn.cursor()
    search_sql = "SELECT max(StudentProgressID) from StudentProgress"
    cursor.execute(search_sql)
    fetched_stuprog_id = cursor.fetchone()[0]
    stu_intern_id = int(fetched_stuprog_id) + 1
    cursor.close()

    app_status = 'Pending'
    InternID = '1000'

    # Insert values into StudentProgress table
    cursor = db_conn.cursor()
    insert_sql = "INSERT INTO StudentProgress VALUES (%s, %s, %s, %s, %s)"
    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    cursor.execute(insert_sql, (str(stu_intern_id), rec_date, rec_assg, app_status, InternID))
    cursor.execute("SET FOREIGN_KEY_CHECKS=1")
    db_conn.commit()
    cursor.close()

    return render_template('/template.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)