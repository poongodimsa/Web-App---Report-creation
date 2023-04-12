from config import *
import pymysql
import pandas as pd
from paramiko import SSHClient
from sshtunnel import SSHTunnelForwarder


def fetch_data():
    with SSHTunnelForwarder(
                (ssh_host, ssh_port),
                ssh_username=ssh_user,
                ssh_pkey=mypkey,
                remote_bind_address=(MySQL_hostname, sql_port)) as tunnel:

                conn = pymysql.connect(host=MySQL_hostname, user=sql_username,
                    passwd=sql_password, db=sql_main_database,
                    port=tunnel.local_bind_port)
            
                query = "SELECT * FROM tblReports"
                data = pd.read_sql_query(query, conn)
                conn.close()
    return data


#-------------------------------------------------------------------------------------


def fetch_past_extractions():
    dfdata = fetch_data()
    
    numrows = dfdata.shape[0]
    #Create html table format and pass the string
    msg = '<table><tr><th><u>Report Name</u></th><th><u>Date Created</u></th><th><u>User</th></u></tr>'

    rows = '<tr>'
    rowe= '</tr>'
    cols = '<td>'
    cole = '</td>'
    ofilepath = "https://trascrizione.my-creditvision.it/UploadApp/Results/"
    
    
    for i,row in dfdata.iterrows():
        link = "<a href=" + ofilepath + row[0] + ".xlsx class='alert-link'>" + row[0]  + "</a>"
        #temp = rows + cols + row[0] +cole + cols + str(row[1]) +cole + cols + row[2] +cole +rowe
        temp = rows + cols + link +cole + cols + str(row[1]) +cole + cols + row[2] +cole +rowe
        msg += temp
        temp = ''
    msg += '</table>'
    return msg
#-------------------------------------------------------------------------------------
