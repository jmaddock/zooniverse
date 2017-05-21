import datetime

def log(text,log_file=None):
    print('[%s] %s' % (str(datetime.datetime.now().time())[:-7],text))
    if log_file:
        write_log(text)
