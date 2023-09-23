#!/bin/bash
sudo su
dnf install git -y
git clone https://github.com/ongmz/FlaskInternshipSystem.git
ls
cd aws-live
dnf install python3-pip -y
pip3 install flask pymysql boto3
ls
cd FlaskInternshipSystem
ls
python3 app.py