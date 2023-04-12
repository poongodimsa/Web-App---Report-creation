#Imports
import os,sys, subprocess


from config import *
import pymysql
import pandas as pd
#from paramiko import SSHClient
#from sshtunnel import SSHTunnelForwarder
import mysql.connector

from io import StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from datetime import datetime
import PyPDF2
import camelot


#-------------------------------------------------------------------------------------
def readpdf(file):

    ''' Reads pdf file using pdfminer and retruns the whole content in a string'''
    
    output_string = StringIO()
    with open(file, 'rb') as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)
    #print(output_string.getvalue())
    return output_string.getvalue()
    
#-------------------------------------------------------------------------------------

def readcol15 (file):
    #Column 15 - Note = concatenation of the lines of text starting with the text 
    #“Titolare di pensione cat. “ under the text “NOTE:” at the end of the PDF file.
    col15=''
    content = readpdf(file)
    ''' Return column 15 value'''
    ind = content.find('NOTE:')  #find the occurence of 'NOTE:'
    if ind == -1:
        return ''
    else:
        
        ind1=ind

        for x in range(5):
            ind2 = ind1
            ind1=content.find("Titolare di pensione cat. ", ind2+x)
            if x == 0: #Store the starting index
                startind=ind1
            if ind1 == -1:
                break
        ind3 = content.find("\n", ind2) #Stop at newline
        col15 = content[startind-2 : ind3]
        
        return col15

#-------------------------------------------------------------------------------------
        
def readpdftable(file):
    
    lastrow=0
    cm=""
    tables = camelot.read_pdf(file, pages = "1-end")
   
    #total number of tables
    ntables = len(tables)
    
    #tables.export("camelot_tables1.xlsx", f = "excel")
    
    #FInd last row of the main table and return it
    for i in range (ntables):
        df1 = tables[i].df
        
        if len(df1.columns) == 14:
            continue
        else: #get the last row
            if i-1 >=0:
                lasttable = i-1
                dflast = tables[i-1].df
                if len((dflast.columns) == 14):
                    lsttmp  = dflast.values[-1].tolist()
                    
                    trc = lsttmp[4]                            #check if "TIPOLOGIA RAPPORTO / CONTRIBUZIONE"  contains 
                    trc = trc.replace('\n','')
                    
                    if trc in ['Lavoro dipendente','Lav. dipend.  part-time']:
                        cm = lsttmp[12]
                    break
    #####################################################################################################################
    #If last row of "TIPOLOGIA RAPPORTO / CONTRIBUZIONE" contains "Lavoro dipendente” or !Lav. dipend. part- time”,
    #identify the corresponding the" CODICE MATRICOLA". Find first occurence of the same and update DAL from that row
    #####################################################################################################################
    
    #find first occurence of cm in CODICE MATRICOLA column 
    if cm != "":
        
        newtable = lasttable                    #it may span across previous table. so check all the tables 
        for i in range (ntables-1):
            dfnew = tables[newtable].df
            
            if newtable != 0:
                if dfnew[12][0] == cm:
                    newtable = newtable -1
                else:
                    break
                
        indnew = (dfnew[12].values == cm).argmax()        #returns first index of value
        #ser = dfnew[[dfnew[12] == cm]]
        dt = dfnew[1][indnew]                              #date from new row
        newdal = dt.split(' ')[0]                          #get only dal from new row, get al from last row
        oldal = lsttmp[1].split(' ')[1]
        newdt = newdal + ' ' + oldal
        
        lsttmp[1] = newdt

    return lsttmp

#-------------------------------------------------------------------------------------

def readcols_5to14(file):
    
    col5= col6 = col7 = col8 = col9 = col10 = col11 = col12 = col13 = col14 = ''
    #Get last row of 'Quadro A' 
    lstcols = readpdftable(file)
    if len(lstcols)==14:

        #5 n 12
        col5 = col12 = lstcols[4]

        #6
        col6 = lstcols[2]

        #7 n 13
        col7 = col13 = lstcols[-1]

        #8 n 9 n 14
        tmp = lstcols[1].split(' ')
        if len(tmp)==2:
            col8=tmp[0]
            col9=tmp[1]

        else:
            col8 = col9 = ""

        col14 = col9

        #10
        col10 = lstcols[-4]

        #11
        col11 = lstcols[6]+lstcols[5]
    
        return col5,col6,col7,col8,col9,col10,col11,col12,col13,col14
    else:
        return ""

#-------------------------------------------------------------------------------------

def get_val(content, key):
    ind = content.find(key)
    if not ind == -1:
        
        inds = content.find('\n',ind) #starting index
        inde = content.find("\n", inds + 2) #ending index
        return (content[inds + 2:inde ])
    else:
        return ''
#-------------------------------------------------------------------------------------

def readcol1to4 (file):
    
    ''' Return column 1 to 4 values'''
    col1 =col2 = col3 = col4 = ''

    content = readpdf(file)

    ##### col 1 - last name + first name #############
    lastname = get_val(content, 'COGNOME:')
    
    indfn = content.find('NOME:', content.find('NOME:')+1)  #find the occurence of 'NOME:' - first name (find second occurence of NOME)
    indfns = content.find("\n",indfn) #last name starting
    indfne = content.find("\n",indfns+2) #last name ending
    firstname = content[indfns+2:indfne]

    col1 = lastname + ' ' + firstname
        
    ########  col 2 - Codice Fiscale “Codice Fiscale: “ from the top part of the first page in PDF  #########
    col2 = get_val(content, 'CODICE FISCALE:') 
    
    
    ########### col 3 - Data Di Nascita - dob - found under the “Codice Fiscale” field after the text “IL:  and has a DD/MM/YYYY structure #####
    col3 =get_val(content, 'IL:')
   
    ########## col 4 - Luogo Di Nascita -place of birth - In the PDF file it’s found under the “COGNOME” field after the text “NATO A: “. ###
    col4 = get_val(content, 'NATO A:')
    
    return col1,col2,col3,col4

#-------------------------------------------------------------------------------------

def check_fiscal_code(col2,excelfile):
    ''' Check if fiscal code found in excel file'''
    dfx = pd.read_excel(excelfile,header=None)

    if col2 in dfx.iloc[:,0].to_list():
        return True
    else:
        return False

#-------------------------------------------------------------------------------------
def check_fc_notin_pdf(excelfile,lstpdffc):
    ''' Return the list of fiscal codes that are not in the passed list'''
    dfx = pd.read_excel(excelfile,header=None)
    lstexcelfc = dfx.iloc[:,0].to_list()
    lstnotinpdf = []
    #Compare two list and return items that are present only in excel list
    for item in lstexcelfc:
        if item not in lstpdffc:
            lstnotinpdf.append(item)
    
    return lstnotinpdf,lstexcelfc

#-------------------------------------------------------------------------------------

def  update_report_info(repname, df):
    
    ''' Insert report fields to tblcontent table in mysql'''
    
    if (not df.empty) and (df.shape[1] == 15):
        for i in range(df.shape[1]):
            df.iloc[0,i] = str(df.iloc[0,i]).replace('"',"'")
            
        '''
        with SSHTunnelForwarder(
                    (ssh_host, ssh_port),
                    ssh_username=ssh_user,
                    ssh_pkey=mypkey,
                    remote_bind_address=(MySQL_hostname, sql_port)) as tunnel:

                    conn = pymysql.connect(host=MySQL_hostname, user=sql_username,
                        passwd=sql_password, db=sql_main_database,
                        port=tunnel.local_bind_port) '''
        conn = mysql.connector.connect(
                  host=MySQL_hostname,
                  user=sql_username,
                  passwd=sql_password,
                  database=sql_main_database
                )
        iquery = 'INSERT INTO tblContent values("% s", "% s", "% s",' \
                    '"% s", "% s", "% s", "% s", "% s", "% s", "% s", "% s", "% s", "% s", "% s", "% s",'\
                    ' "% s")' % (repname, df.iloc[0,0], df.iloc[0,1], df.iloc[0,2], df.iloc[0,3], df.iloc[0,4], 
                                df.iloc[0,5], df.iloc[0,6], df.iloc[0,7], df.iloc[0,8], df.iloc[0,9], df.iloc[0,10], 
                                df.iloc[0,11], df.iloc[0,12], df.iloc[0,13], df.iloc[0,14])


        mycursor=conn.cursor()
        mycursor.execute(iquery)
        conn.commit()

        conn.close()

#-------------------------------------------------------------------------------------
def  update_report_name(repname,username):
    
    ''' Insert report name, date and user to tblreport in mysql'''
    today = datetime.now()
    date = today.strftime("%Y/%m/%d %H:%M:%S")
    '''
    with SSHTunnelForwarder(
                (ssh_host, ssh_port),
                ssh_username=ssh_user,
                ssh_pkey=mypkey,
                remote_bind_address=(MySQL_hostname, sql_port)) as tunnel:

                conn = pymysql.connect(host=MySQL_hostname, user=sql_username,
                    passwd=sql_password, db=sql_main_database,
                    port=tunnel.local_bind_port)'''
    conn = mysql.connector.connect(
          host=MySQL_hostname,
          user=sql_username,
          passwd=sql_password,
          database=sql_main_database
        )
    iquery = "INSERT INTO tblReports values('% s', '% s', '% s')" % (repname,date,username)

    mycursor=conn.cursor()
    mycursor.execute(iquery)
    conn.commit()

    conn.close()                
                
#-------------------------------------------------------------------------------------
def extract_data(upload_dir,excel_dir,repname,user):
    '''Extract data from pdf into an excel file in specified format'''
    try:
        
        #Define input and output path here
        currdir=os.getcwd() 
        inpath = os.path.join(currdir, upload_dir)
        edir = os.path.join(currdir, excel_dir) 
        excelfile = os.path.join(edir, "fiscal_codes.xlsx") 
    
        repname = repname.replace(' ','_')
        #Return if files other than expected extensions found
        ext = excelfile.split('.')[-1]
        if ext not in ['xlsx','xls']:
            return("The fiscal codes excel file is invalid! Please choose files with extensions 'xlsx' or 'xls'")
        
        
        #output Header
        lstheaders = ["NOMINATIVO","CODICE FISCALE","DATA DI NASCITA","LUOGO DI NASCITA",
                      "TIPOLOGIA RAPPORTO","ENTE","DENOMINAZIONE","DATA INIZIO RAPPORTO",
                      "ULTIMA DATA NOTA","FASCIA IMPORTO REDDITO (AL DIRITTO)","GIORNI REDDITO",
                      "TIPOLOGIA CASSA INTEGRAZIONE","DENOMINAZIONE CASSA INTEGRAZIONE",
                      "ULTIMA DATA CASSA INTEGRAZIONE","NOTE"]
        
        #Out dataframe
        dfout = pd.DataFrame(columns = lstheaders)
    
        indir = os.listdir(inpath)
        if len(indir) == 0:
            return "No input files found. Please upload files to proceed."
       
        #holder for pdf fiscal codes
        lstpdffc_main = [] 
        #holder for uploaded pdf file list
        summ_pdfs_uploaded=[]
        #pdf files with fc
        summ_pdfs_with_fc = []
        #pdf files with fc and match in excel
        summ_pdfs_fcinexcel = []
        #pdf file with match and info extracted
        summ_pdfs_fcinexcel_with_info = []
        
        
        #Loop thorugh all the files that have been uploaded
        for file in indir:
            print(file)
            
            
            ext=file.split('.')[-1]
            if ext != 'pdf':
                return(" Please choose files with extension '.pdf'!")
        
            summ_pdfs_uploaded.append(file)
            
            #bfile = file.encode('utf-8')
            filep = os.path.join(inpath,file)
    
            #Col 1 to 4
            col1, col2, col3, col4 = readcol1to4(filep)
            
            ################ Validations as per specs #####################
            '''a. If the fiscal code of one or more PDF file does not match those in the Excel file, it will
            not be included in the results
            b. If a fiscal code is in the Excel file but not in the PDF files, the fiscal code must be
            shown in the results (not showing any information for it)
            c. If no information to extract is found in the PDF file but the fiscal code, this will be
            included in the results (not showing any information)
            d. If in the PDF file no fiscal code is found, it must not be considered and not included
            in the results'''
            
            
            lstpdffc_main.append(col2)         #keep appending fiscal codes to validate (b) 
            
            
            #point c. taken care by initializing the variables to '' in all functions
            
            if col2 == '':     #point d.
                continue
                
            #SUmmary of pdf files with fiscal code
            summ_pdfs_with_fc.append(file)
            
            if not check_fiscal_code(col2,excelfile): #point a.
                continue
            else:
                
                #pdf with fc and match in excel
                summ_pdfs_fcinexcel.append(file)
                #pdf with match and info extracted
                if (col1 != '') & (col3 != '') & (col4 != ''):
                    summ_pdfs_fcinexcel_with_info.append(file)
      
                col5,col6,col7,col8,col9,col10,col11,col12,col13,col14 = readcols_5to14(filep)
                col15 = readcol15(filep)
    
                dfout.loc[len(dfout)] = [col1,col2,col3,col4,col5,col6,col7,col8,col9,col10,col11,col12,col13,col14,col15]
    
                #os.remove(filep)
     
    except:
        msg = "Oops! Error occured while processing the file:  " + file + "<br>Error description: " +  sys.exec_info()[0] 
        return msg
        
        
        '''b. If a fiscal code is in the Excel file but not in the PDF files, the fiscal code must be
            shown in the results (not showing any information for it)
        '''
    
        
    try:    
        lstonlyinexcel,summ_fcs_inexcel = check_fc_notin_pdf(excelfile,lstpdffc_main)
        
        if len(lstonlyinexcel) > 0:
            for item in lstonlyinexcel:
                
                #lstrow.extend (('',item,'','','','','','','','','','','','','')) 
                dfout.loc[len(dfout)] = ['',item,'','','','','','','','','','','','','']
               
        
        filename = repname + ".xlsx" 
    
        outpath = os.path.join(currdir, 'Results')
        if not os.path.isdir(outpath):
            os.mkdir(outpath)
        
        #dfout = dfout.applymap(lambda x: x.encode('unicode_escape').
         #            decode('utf-8') if isinstance(x, str) else x)
                     
        outfile = os.path.join(outpath,filename)
        dfout.to_excel(outfile,index=False, header=True)
    
    except:
        msg = "Oops! Error occured while generating excel report. <br> Error description: " + sys.exec_info()[0]
        return msg
    
    try:
        
        ############ Update database ########################
        update_report_name(repname,user)
        update_report_info(repname,dfout)
    
    except:
        msg="Oops! Error oocured while writing to database. <br>Error description: " + sys.exec_info()[0]
        return msg
        
        #os.chmod(outfile, 0o0777)
        #open_file(outfile)
    
        ofilepath = "https://trascrizione.my-creditvision.it/UploadApp/Results/" + filename
        
        
        ##################### Return the summary #####################
        '''
        a. Fiscal codes found in the Excel file:summ_fcs_inexcel 
        b. Uploaded PDF files: summ_pdfs_uploaded
        c. Uploaded PDF files with fiscal code:summ_pdfs_with_fc
        d. Uploaded PDF files with fiscal code and match in the Excel file: summ_pdfs_fcinexcel
        e. Uploaded PDF files with fiscal code and match in the Excel file with info extracted: summ_pdfs_fcinexcel_with_info
    '''
         #Insert count of files at top for every summary
        summ_fcs_inexcel.insert(0, str(len(summ_fcs_inexcel)))
        summ_pdfs_uploaded.insert(0, str(len(summ_pdfs_uploaded)))
        summ_pdfs_with_fc.insert(0, str(len(summ_pdfs_with_fc)))
        summ_pdfs_fcinexcel.insert(0,  str(len(summ_pdfs_fcinexcel)))
        summ_pdfs_fcinexcel_with_info.insert(0, str(len(summ_pdfs_fcinexcel_with_info)))
    
        msg= 'Result generated successfully at: <a href=' + ofilepath + " class='alert-link'>" + ofilepath  + '</a><br><br>' + '<u><b>Fiscal codes found in the Excel file: </b></u>' + '<br>'.join(summ_fcs_inexcel) +'<br><br><u><b>Uploaded PDF files: </b></u>' + '<br>'.join(summ_pdfs_uploaded) + '<br><br><b><u>Uploaded PDF files with fiscal code: </u></b>' + '<br>'.join(summ_pdfs_with_fc) + '<br><br><b><u>Uploaded PDF files with fiscal code and match in the Excel file: </u></b>' + '<br>'.join(summ_pdfs_fcinexcel) + '<br><br><b><u>Uploaded PDF files with fiscal code and match in the Excel file with info extracted: </u></b>'  + '<br>'.join(summ_pdfs_fcinexcel_with_info)
        
        return msg


