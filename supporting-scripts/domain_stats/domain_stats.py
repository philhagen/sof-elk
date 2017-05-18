#!/usr/bin/python
#domain_stats.py by Mark Baggett
#Twitter @MarkBaggett

from __future__ import print_function
import BaseHTTPServer
import threading
import SocketServer
import urlparse
import re
import argparse
import sys
import time
import os
import datetime

try:
    import whois
except Exception as e:
    print(str(e))
    print("You need to install the Python whois module.  Install PIP (https://bootstrap.pypa.io/get-pip.py).  Then 'pip install python-whois' ")
    sys.exit(0)

class domain_api(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        if self.server.args.verbose: self.server.safe_print(self.path)
        (ignore, ignore, urlpath, urlparams, ignore) = urlparse.urlsplit(self.path)
        cmdstr = tgtstr = None
        if re.search("[\/](?:created|alexa|domain)[\/].*?", urlpath):
            cmdstr = re.search(r"[\/](created|alexa|domain)[\/].*$", urlpath)
            tgtstr = re.search(r"[\/](created|alexa|domain)[\/](.*)$", urlpath)
            if not cmdstr or not tgtstr:
                self.wfile.write('<html><body>API Documentation<br> http://%s:%s/cmd/tgt <br> cmd = domain, alexa or created <br> tgt = domain name </body></html>' % (self.server.server_address[0], self.server.server_address[1],self.server.server_address[0], self.server.server_address[1],self.server.server_address[0], self.server.server_address[1]))
                return
            params = {}
            params["cmd"] = cmdstr.group(1)
            params["tgt"] = tgtstr.group(2)
        else:
            cmdstr=re.search("cmd=(?:domain|alexa|created)",urlparams)
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
        if params["cmd"] == "alexa":
            if self.server.args.verbose: self.server.safe_print ("Alexa Query:", params["tgt"])
            if not self.server.alexa:
                if self.server.args.verbose: self.server.safe_print ("No Alexa data loaded. Restart program.")
                self.wfile.write("Alexa not loaded on server. Restart server with -a or --alexa and file path.")
            else:
                if self.server.args.verbose: self.server.safe_print ("Alexa queried for:%s" % (params['tgt']))              
                self.wfile.write(str(self.server.alexa.get(params["tgt"],"0")))
        elif params["cmd"] == "domain":
            fields=[]
            if "/" in params['tgt']:
                fields = params['tgt'].split("/")
                params['tgt'] = fields[-1]
                fields = fields[:-1]
            if params['tgt'] in self.server.cache:
                if self.server.args.verbose: self.server.safe_print("Found in cache!!")
                domain_info = self.server.cache.get(params['tgt'])
                #Update the time on the domain
                domain_info["time"] = time.time()
                try:
                    self.server.cache_lock.acquire()
                    self.server.cache[params['tgt']] = domain_info
                finally:
                    self.server.cache_lock.release()
            else:
                #Look it up on the web
                try:
                    if self.server.args.verbose: self.server.safe_print ("Querying the web", params['tgt'])
                    domain_info = whois.whois(params['tgt'])
                    if not domain_info.get('creation_date'):
                        self.wfile.write(str("No whois record for %s" % (params['tgt'])))
                        return
                except Exception as e:
                    if self.server.args.verbose: self.server.safe_print ("Error querying whois server: %s" % (str(e)))     
                    return
                #Put it in the cache
                self.server.safe_print("Caching whois record %s" % (domain_info.get("domain_name","incomplete record")))
                domain_info["time"] = time.time()
                if self.server.alexa:
                    domain_info['alexa'] = self.server.alexa.get(params["tgt"],"0")
                try:
                    self.server.cache_lock.acquire()
                    self.server.cache[params['tgt']] = domain_info
                finally:
                    self.server.cache_lock.release()
            if not fields:
                self.wfile.write(str(domain_info))
            else:
                if self.server.args.verbose: self.server.safe_print("processing fields %s" % (fields))
                for fld in fields:
                    #We only pull one value if multiple values exist unless the field name ends with an * or --all was on cli
                    retrieve_all = self.server.args.all
                    if fld.endswith("*"):
                        fld = fld[:-1]
                        retrieve_all = True
                    fld_value = domain_info.get(fld,"no field named %s found" % (fld))
                    if (not retrieve_all) and type(fld_value)==list:
                        fld_value = fld_value[-1]
                    self.wfile.write(str(fld_value)+"; ")              
        return

    def log_message(self, format, *args):
        return

class ThreadedDomainStats(SocketServer.ThreadingMixIn, SocketServer.TCPServer, BaseHTTPServer.HTTPServer):
    def __init__(self, *args,**kwargs):
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.args = ""
        self.screen_lock = threading.Lock()
        self.alexa = ""
        self.exitthread = threading.Event()
        self.exitthread.clear()
        BaseHTTPServer.HTTPServer.__init__(self, *args, **kwargs)

    def safe_print(self,*args,**kwargs):
        try:
            self.screen_lock.acquire()
            print(*args,**kwargs)
        finally:
            self.screen_lock.release()

    def clear_old_cache(self):
        if self.args.verbose: self.safe_print ( "Clearing old cache")
        for domain,domain_info in self.cache.items():
            #self.safe_print(domain, time.time() - domain_info.get('time',0), self.args.cache_time)
            if (time.time() - domain_info.get('time', 0)) > self.args.cache_time:
                try:
                    self.cache_lock.acquire()
                    del self.cache[domain]
                    self.safe_print("Removed expired cache entry for %s" % (domain))
                finally:
                    self.cache_lock.release()
        #Reschedule yourself to run again in 1 hour  (60*60)  Temporarily set to 60 for testing
        if not self.exitthread.isSet():
            self.timer = threading.Timer(self.args.garbage_cycle, self.clear_old_cache, args = ())
            self.timer.start()

def preload_domains(domain_list, server, delay):
    server.safe_print("Now preloading %d domains from alexa in the whois cache." %(len(domain_list)))
    dcount = 0
    dtenth = len(domain_list)/10
    for eachalexa,eachdomain in re.findall(r"^(\d+),(.*)", "".join(domain_list), re.MULTILINE):
        dcount += 1
        if (dcount % dtenth) == 0:
            server.safe_print("Loaded %d percent of whois cache." % (float(dcount)/len(domain_list)*100))
        try:
            domain_info = whois.whois(eachdomain)
            if not any(domain_info.values()):
                server.safe_print("No whois record for %s" % (eachdomain))
                continue
        except Exception as e:
            if args.verbose: server.safe_print("Error querying whois server: %s" % (str(e)))     
            continue
        domain_info["time"] = time.time()
        domain_info['alexa'] = eachalexa
        try:
            server.cache_lock.acquire()
            server.cache[eachdomain] = domain_info
        finally:
            server.cache_lock.release()
    server.safe_print("Domain Cache Fully Loaded")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('-ip','--address',required=False,help='IP Address for the server to listen on.  Default is 127.0.0.1',default='127.0.0.1')
    parser.add_argument('-c','--cache-time',type=float,required=False,help='Number of seconds to hold a whois record in the cache. Default is 3600 (1 hour). Set to 0 to save forever.',default=3600)
    parser.add_argument('port',type=int,help='You must provide a TCP Port to bind to')
    parser.add_argument('-v','--verbose',action='count',required=False,help='Print verbose output to the server screen.  -vv is more verbose.')
    parser.add_argument('-a','--alexa',required=False,help='Provide a local file path to an Alexa top-1m.csv')
    parser.add_argument('--all',action="store_true",required=False,help='Return all of the values in a field if multiples exist. By default it only returns the last value.')
    parser.add_argument('--preload',type=int,default=1000,help='preload cache with this number of the top Alexa domain entries.  Set to 0 to disable.  Default 1000')
    parser.add_argument('--delay',type=float,default=0.1,help='Delay between whois lookups while staging the initial cache.  Default is 0.1')
    parser.add_argument('--garbage-cycle',type=int,default=86400,help='Delete entries in cache older than --cache-time at this iterval (seconds).  Default is 86400')

    #args = parser.parse_args("-s 1 -vv 8081 english_lowercase.freq".split())
    args = parser.parse_args()

    #Setup the server.
    server = ThreadedDomainStats((args.address, args.port), domain_api)
    if args.alexa:
        if not os.path.exists(args.alexa):
            print("Alexa file not found %s" % (args.alexa))
        else:
            server.alexa = {}
            try:
                server.safe_print("Preloading %s alexa cache" % (args.preload))
                alexa_file = open(args.alexa).readlines()
                server.alexa = dict([(a,b) for b,a in re.findall(r"^(\d+),(.*)", "".join(alexa_file), re.MULTILINE)])
                if args.preload != 0:
                    th = threading.Thread(target=preload_domains, args = (alexa_file[:args.preload], server, args.delay))
                    th.start()
            except Exception as e:
                server.safe_print("Unable to parse alexa file:%s" % (str(e)))
            finally:
                del alexa_file

    server.args = args

    #Schedule the first save interval unless save_interval was set to 0.
    if args.cache_time:
        server.timer = threading.Timer(args.garbage_cycle, server.clear_old_cache, args = ())
        server.timer.start()

    #start the server
    server.safe_print('Server is Ready. http://%s:%s/cmd/[subcmd/,]target' % (args.address, args.port))
    while True:
        try:
            server.handle_request()
        except KeyboardInterrupt:
            break

    server.timer.cancel()    
    server.safe_print("Web API Disabled...")
    server.safe_print("Control-C hit: Exiting server.  Please wait..")

if __name__=="__main__":
    main()