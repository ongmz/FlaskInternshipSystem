sudo su

dnf install git -y

git clone https://github.com/ongmz/FlaskInternshipSystem.git

cd aws-live

dnf install python-pip -y

pip3 install flask pymysql boto3

cd FlaskInternshipSystem

python3 app.py