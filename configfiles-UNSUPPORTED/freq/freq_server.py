#freq_server.py by Mark Baggett
#Twitter @MarkBaggett
#github http://github.com/MarkBaggett/
#This scripts runs a web server to provide a callable API to use frequency tables.
#
#Start the server passing it a port and a frequecy table.  For example:
#python freq_server.py 8080 english_lowercase.freq
#
#Now you can query the API to measure the character frequency of its characters.  
#wget http://127.0.0.1:8080/cmd=measure\&tgt=measurethisstring
#
#You can also mark a string as normal.  NOTE: There is a performance impact to updating via the API.  Use CLI freq.py to update tables instead.
#wget http://127.0.0.1:8080/cmd=normal\&tgt=UpdateFreqWithTheseChars&weight=10
#
#Thanks to @securitymapper for Testing & suggestions

from __future__ import print_function
from freq import *
import BaseHTTPServer
import threading
import SocketServer
import urlparse
import re
import argparse


class freqapi(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        (ignore, ignore, ignore, urlparams, ignore) = urlparse.urlsplit(self.path)
        cmdstr=re.search("cmd=(?:measure|normal)",urlparams)
        tgtstr =  re.search("tgt=",urlparams)
        if not cmdstr or not tgtstr:
            self.wfile.write('<html><body>API Documentation<br> http://%s:%s/?cmd=measure&tgt=&ltstring&gt <br> http://%s:%s/?cmd=normal&tgt=&ltstring&gt <br> http://%s:%s/?cmd=normal&tgt=&ltstring&gt&weight=&ltweight&gt </body></html>' % (self.server.server_address[0], self.server.server_address[1],self.server.server_address[0], self.server.server_address[1],self.server.server_address[0], self.server.server_address[1]))
            return
        params={}
        try:
            for prm in urlparams.split("&"):
                key,value = prm.split("=")
                params[key]=value
        except:
            self.wfile.write('<html><body>Unable to parse the url. </body></html>')
            return
        if params["cmd"] == "normal":
            self.server.safe_print("cache cleared")
            try:
                self.server.cache_lock.acquire()
                self.server.cache ={}
            finally:
                self.server.cache_lock.release()
            try:
                self.server.fc_lock.acquire()
                weight = int(params.get("weight","1"))
                self.server.fc.tally_str(params["tgt"], weight=weight)
                self.server.dirty_fc = True
            finally:
                self.server.fc_lock.release()
            self.wfile.write('<html><body>Frequency Table updated</body></html>') 
        elif params["cmd"] == "measure":
            if self.server.cache.has_key(params["tgt"]):
                if self.server.verbose: self.server.safe_print ("Query from cache:", params["tgt"])
                measure =  self.server.cache.get(params["tgt"])
            else:
                if self.server.verbose: self.server.safe_print ( "Added to cache:", params["tgt"])
                measure = self.server.fc.probability(params["tgt"])
                try:
                    self.server.cache_lock.acquire()
                    self.server.cache[params["tgt"]]=measure
                finally:
                    self.server.cache_lock.release()
                if self.server.verbose>=2: self.server.safe_print ( "Server cache: ", str(self.server.cache))
            self.wfile.write(str(measure))
            return
    def log_message(self, format, *args):
        return

class ThreadedFreqServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer, BaseHTTPServer.HTTPServer):
    def __init__(self, *args,**kwargs):
        self.fc = FreqCounter()
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.screen_lock = threading.Lock()
        self.verbose = False
        self.fc_lock = threading.Lock()
        self.dirty_fc = False
        self.exitthread = threading.Event()
        self.exitthread.clear()
        BaseHTTPServer.HTTPServer.__init__(self, *args, **kwargs)

    def safe_print(self,*args,**kwargs):
        try:
            self.screen_lock.acquire()
            print(*args,**kwargs)
        finally:
            self.screen_lock.release()

    def save_freqtable(self,save_path,save_interval):
        if self.verbose: self.safe_print ( "Save interval reached.")
        if self.dirty_fc:
            if self.verbose: self.safe_print ("Frequency counter changed.  Saving to disk.",save_path)
            try:
                self.fc_lock.acquire()
                self.fc.save(save_path)
                self.dirty_fc = False
            finally:
                self.fc_lock.release()
        else:
            if self.verbose: self.safe_print ("Frequency counter not changed.  Not Saving to disk.")
        #Reschedule yourself
        if not self.exitthread.isSet():
            self.timer = threading.Timer(60*save_interval, self.save_freqtable, args = (save_path,save_interval))
            self.timer.start()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('-ip','--address',required=False,help='IP Address for the server to listen on.  Default is 127.0.0.1',default='127.0.0.1')
    parser.add_argument('-s','--save_interval',type=float,required=False,help='Number of minutes to wait before trying to save frequency table updates. Default is 10 minutes.  Set to 0 to never save.',default=10)
    parser.add_argument('port',type=int,help='You must provide a TCP Port to bind to')
    parser.add_argument('freq_table',help='You must provide the frequency table name (optionally including the path)')
    parser.add_argument('-v','--verbose',action='count',required=False,help='Print verbose output to the server screen.  -vv is more verbose.')

    #args = parser.parse_args("-s 1 -vv 8081 english_lowercase.freq".split())
    args = parser.parse_args()

    #Setup the server.
    server = ThreadedFreqServer((args.address, args.port), freqapi)
    server.fc.load(args.freq_table)
    server.verbose = args.verbose
    #Schedule the first save interval unless save_interval was set to 0.
    if args.save_interval:
        server.timer = threading.Timer(60 *args.save_interval, server.save_freqtable, args = (args.freq_table, args.save_interval))
        server.timer.start()
 
    #start the server
    print('Server is Ready. http://%s:%s/?cmd=measure&tgt=astring' % (args.address, args.port))
    print('[?] - Remember: If you are going to call the api with wget, curl or something else from the bash prompt you need to escape the & with \& \n\n')
    while True:
        try:
            server.handle_request()
        except KeyboardInterrupt:
            break
        
    server.safe_print("Control-C hit: Exiting server...")
    server.safe_print("Web API Disabled...")
    if server.dirty_fc:
        server.safe_print("The Frequency counter has changed since the last save interval. Saving final update.")
        server.exitthread.set()
        server.timer.cancel()
        try:
            server.fc_lock.acquire()
            server.fc.save(args.freq_table)
            server.fc_lock.release()
        except:
            server.safe_print("[!] An error occured during the final save.")
    else:
        server.safe_print( "No Changes made since last file save.  Canceling scheduled save...")
        server.timer.cancel()
    server.safe_print("Server has stopped.")
    
if __name__=="__main__":
    main()
