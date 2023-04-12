'''
Global arguments
'''
import os 
import datetime
import paramiko


# maximum filesize in megabytes
file_mb_max = 100
# encryption key
app_key = 'any_non_empty_string'
# full path destination for our upload files
#name = "Uploads\\uploads_" + str(datetime.datetime.now().strftime("%d-%H%M%S"))
upload_dest = os.path.join(os.getcwd(), 'uploads_dir')
excel_dest = os.path.join(os.getcwd(), 'fiscal_excel')
# list of allowed allowed extensions
extensions = set(['pdf'])
#for fiscal code file
excelextensions = set(['xlsx','xls'])

#Database credentials
mypkey = paramiko.RSAKey.from_private_key_file('D:\\.ssh\\id_rsa')
    
MySQL_hostname = '127.0.0.1' #MySQL Host
sql_username = 'trascrizionemycr_credit_andrea'#Username 
sql_password = 'Andreapw123' #Password
sql_main_database = 'trascrizionemycr_reportapp' #Database Name
sql_port = 3306
#ssh_host = 'trascrizione.my-creditvision.it:2288' #SSH Host
ssh_host = 'trascrizione.my-creditvision.it' #SSH Host
ssh_user = 'trascrizionemycr' #SSH Username
ssh_port = 2288
sql_ip = '1.1.1.1.1'
