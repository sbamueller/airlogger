import datetime

def info(text):
    print('[ INFO] ' + datetime.datetime.now().strftime('%Y.%m.%d %H.%M.%S') + ' : ' + text)

def error(text):
    print('[ERROR] ' + datetime.datetime.now().strftime('%Y.%m.%d %H.%M.%S') + ' : ' + text)

def warn(text):
    print('[ WARN] ' + datetime.datetime.now().strftime('%Y.%m.%d %H.%M.%S') + ' : ' + text)

def debug(text):
    print('[DEBUG] ' + datetime.datetime.now().strftime('%Y.%m.%d %H.%M.%S') + ' : ' + text)
