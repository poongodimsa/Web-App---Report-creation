from flask import Flask, flash, request, redirect, render_template, url_for,session

import sys,os,re   
from werkzeug.utils import secure_filename
from config import *
import extract_data
import pastextractions

import pymysql
import pandas as pd
from paramiko import SSHClient
from sshtunnel import SSHTunnelForwarder

UploadApp = Flask(__name__)
UploadApp.secret_key = app_key


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def check_excel_ext(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in excelextensions

def get_login_info(username,password):
    #Establish Mysql connection using ssh host and ssh key
    with SSHTunnelForwarder(
        (ssh_host, ssh_port),
        ssh_username=ssh_user,
        ssh_pkey=mypkey,
        remote_bind_address=(MySQL_hostname, sql_port)) as tunnel:

        conn = pymysql.connect(host=MySQL_hostname, user=sql_username,
            passwd=sql_password, db=sql_main_database,
            port=tunnel.local_bind_port)
        query = "SELECT * FROM tblUser WHERE Userid = '% s' AND Password = '% s'" % (username, password )
        data = pd.read_sql_query(query, conn)
        conn.close()
    return data

@UploadApp.route('/')
@UploadApp.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        
        #fetch login details from database
        data = get_login_info(username,password)
        if data.shape[0]>0:
            session["user"] = data.iloc[0,1]
            return redirect(url_for('dashboard'))
        else:
            msg = 'Incorrect username or password. Please try again.'
            return render_template('login.html', msg = msg)
        

    else:
        return render_template('login.html', msg = msg)

    
@UploadApp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@UploadApp.route('/dashboard')
def dashboard():
     return render_template('dashboard.html')

@UploadApp.route('/dashboard', methods=['POST','GET'])
def mainpage():
    if request.method == "POST":
        if request.form["action"] == "New extraction":
            return redirect(url_for('upload'))

        elif request.form["action"] == "Past extractions":
            return redirect(url_for('pastextracts'))
            

@UploadApp.route('/pastextractions')
def pastextracts():
    
    msg_table = pastextractions.fetch_past_extractions()
    flash(msg_table)
    return render_template('pastextractions.html')
   
## on page '/upload' load display the upload file
@UploadApp.route('/upload')
def upload():
    return render_template('upload.html',msg='')

@UploadApp.route('/upload',  methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
       
        files = request.files.getlist('files[]')
        exfile = request.files.get('excelfile')
        repname = request.form['repname']
        
        #Check if the entered report name already exists
        with SSHTunnelForwarder(
                (ssh_host, ssh_port),
                ssh_username=ssh_user,
                ssh_pkey=mypkey,
                remote_bind_address=(MySQL_hostname, sql_port)) as tunnel:

                conn = pymysql.connect(host=MySQL_hostname, user=sql_username,
                    passwd=sql_password, db=sql_main_database,
                    port=tunnel.local_bind_port)
                query = "SELECT * FROM tblReports WHERE Reportname = '% s'" % (repname)
                datarep = pd.read_sql_query(query, conn)
                conn.close()
        if not datarep.empty:
            msg = 'Report name alreay exists. Please try with a different name.'
            return render_template('upload.html', msg = msg)
        
        
        #Upload pdf files
        if not os.path.isdir(upload_dest):
            os.mkdir(upload_dest)
        for npfile in  os.listdir(upload_dest):
            os.remove(os.path.join(upload_dest,npfile))
        flash(files)    
        flash(exfile)        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_dest, filename))

        #upload excel file
        if exfile and check_excel_ext(exfile.filename):
            if not os.path.isdir(excel_dest):
                os.mkdir(excel_dest)
            for nfile in  os.listdir(excel_dest):
                os.remove(os.path.join(excel_dest,nfile))
            exfilename = secure_filename('fiscal_codes.xlsx')
            exfile.save(os.path.join(excel_dest, exfilename))
        
        #Generate reports
        path = extract_data.extract_data(upload_dest,excel_dest,repname,session["user"])
        #path = path.replace('\\n', '\n')
        flash(path)
      
        return render_template('extract.html')
        #return redirect('/extract')

if __name__ == "__main__":
    print('To open the app navigate to http://127.0.0.1:4000/login')
    UploadApp.run(host='127.0.0.1',port=4000,debug=False,threaded=True)
    