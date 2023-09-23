from flask import Flask, render_template, request, url_for, redirect
from pymysql import connections
import boto3
from config import *
from datetime import datetime
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

    cursor.execute('SELECT CompanyName, RequiredSkillSet, InternshipBenefit, ApplicationDate FROM Company C, CompanyApplication CA, Admin A WHERE C.CompanyID = CA.CompanyID AND CA.AdminID = A.AdminID;')
    company_application_rows = cursor.fetchall()
    cursor.close()
    print('Fetch from database')
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
    insert_sql2 = "INSERT INTO CompanyApplication VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    cursor.execute(insert_sql2, (str(comp_app_id), str(comp_id), required_quali, internship_pos, internship_allowance, app_status, admin_id, str(curr_date)))
    cursor.execute("SET FOREIGN_KEY_CHECKS=1") 
    db_conn.commit()
    cursor.close()

    # File upload
    uploaded_file = request.files['uploadCompany']
    print(request.files)

    if uploaded_file and uploaded_file.filename != '':
        try:
            # Initialize the S3 client
            s3 = boto3.resource('s3')

            # Set a unique key for the uploaded file in S3
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            s3_key = f'company_pdfs/{timestamp}_{uploaded_file.filename}'
            s3.Bucket(custombucket).put_object(Key=s3_key, Body=uploaded_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

        except Exception as e:
            return str(e)
    else:
        s3_file_url = None

    # #Upload image file to S3
    # img_file_name_in_s3 = "compID-" + str(comp_id) + '_img'
    # s3 = boto3.resource('s3')

    # try:
    #     # print("Uploading image into S3 bucket ...")
    #     s3.Bucket(custombucket).put_object(Key=img_file_name_in_s3, Body=comp_img)
    #     bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
    #     s3_loc = (bucket_location['LocationConstraint'])

    #     if s3_loc is None:
    #         s3_loc = ''
    #     else:
    #         s3_loc = '-' + s3_loc
        
    #     object_url = "https:..s3{0}.amazonaws.com/{1}/{2}".format(s3_loc,custombucket,img_file_name_in_s3)

    # except Exception as e:
    #     return str(e)

    # finally:
    #     cursor.close()
    return render_template('/template.html')

@app.route('/lecturer.html')
def lecturer():
    # Render the admin.html template from a templates folder in your project directory
    cursor = db_conn.cursor()

    cursor.execute('SELECT S.StudentName, S.StudentID, S.Programme FROM Lecturer L, StudentInternship SI, Student S WHERE L.LecturerID = SI.LecturerID AND SI.StudentID = S.StudentID;')
    student_list = cursor.fetchall()
    cursor.close()
    # Render the admin.html template from a templates folder in your project directory
    return render_template('lecturer.html', student_list=student_list)

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

@app.route('/lecturer-approve.html')
def lecturer_approve():
    # Render the student.html template from a templates folder in your project directory
    return render_template('lecturer-approve.html')

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
    insert_sql1 = "INSERT INTO Student VALUES (%s, %s, %s, %s, %s, %s)"
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