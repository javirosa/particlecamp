import socket
import time
import psycopg2

conn = psycopg2.connect(database='mydb', user='melissa', password='postgres')
cur = conn.cursor()
Insert = "INSERT INTO dusttrak (dusttraktime, dtconc) VALUES (%s,%s)"

def ReadDustTrak():
    """First need to find the status of the instrument.  If the instrument is running,
    it's fair game to get data from it.  Currently, data is being logged every
    2 minutes so I'll update the database every 2 mintues.  In the future, it might
    make more sense to poll the instrument heavily and average data ourselves. We
    can initiate the zero function ourselves.
    """
#    HOST = '169.254.162.97'    # The remote host
    HOST = '169.254.162.245'    # The remote host
    PORT =  3602             # The same port as used by the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    s.sendall("MSTATUS\r")
    data = s.recv(1024)
    Received = repr(data).strip("'\\r\\n")

    if Received == 'Running':
        s.sendall("RDSN\r")
        data = s.recv(1024)
        SerialNum = repr(data).strip("'\\r\\n")
        
        s.sendall("RMLOGGEDMEAS\r")
        data = s.recv(1024)
        Received = repr(data).strip("'\\r\\n")
        RArray = Received.split(',')
        
        
        
    elif Received == 'Idle':
        s.sendall("MSTART\r")
        s.close()
        return
        
    print "DustTrak: {},{} mg/m3".format(time.strftime("%Y-%m-%d %H:%M:%S"), RArray[1])
    cur.execute(Insert, (
        time.strftime("%Y-%m-%d %H:%M:%S"), 
        float(RArray[1]))
        )
    conn.commit()
    s.close()

def ZeroDustTrak():
    """This puts the DustTrak into zero mode and then returns the instrument
    back to logging mode.
    """
    #HOST = '169.254.162.97'    # The remote host
    HOST = '169.254.162.165'
    PORT =  3602             # The same port as used by the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    #Stop the instrument and then start the zero function
    print "Stopping DustTrak"
    while 1:
        s.sendall("MSTOP\r")
        data = s.recv(1024)
        Received = repr(data).strip("'\\r\\n")
        
        if Received == 'OK':
            break
        
        time.sleep(1)
    
    #Start the zero process
    print "Start Zero Operation"
    while 1:
        s.sendall("MZERO\r")
        data = s.recv(1024)
        Received = repr(data).strip("'\\r\\n")
        
        if Received == 'OK':
            break
        
        time.sleep(1)
    
    #Now wait for the zero function to complete
    print "Waiting for Zero to complete"
    Counter = 1
    while 1:
        s.sendall("MSTATUS\r")
        data = s.recv(1024)
        Received = repr(data).strip("'\\r\\n")
        
        if Received == 'Idle':
            break
        
        time.sleep(1)
    
        print "Seconds since Zero start: {}".format(Counter)
        Counter = Counter + 1
    
    #Start the instrument back up
    print "Zero COMPLETE.  Restarting Instrument"
    while 1:
        s.sendall("MSTART\r")
        data = s.recv(1024)
        Received = repr(data).strip("'\\r\\n")
        
        if Received == 'OK':
            break
        
        time.sleep(1)
    
    s.close()

Recorded = 0
while 1:
    CurrentTime = time.localtime()
    
    if CurrentTime.tm_hour == 11 and CurrentTime.tm_min == 2 and CurrentTime.tm_sec == 0:
        ZeroDustTrak()
        time.sleep(1)
    elif CurrentTime.tm_sec in range(0,60,5) and Recorded == 0:
        ReadDustTrak()
        Recorded = 1
    elif Recorded == 1 and CurrentTime.tm_sec not in range(0,60,5):
        Recorded = 0
