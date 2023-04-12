import sys, os

INTERP = '/home/trascrizionemycr/public_html/UploadApp/virtenv/bin/python'
if sys.executable != INTERP: os.execl(INTERP, INTERP, *sys.argv)

from upload_file import UploadApp as application
