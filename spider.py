#!/usr/bin/pyhon

import argparse
import urllib2
from StringIO import StringIO
import gzip
from urlparse import urlparse
from BeautifulSoup import BeautifulSoup
import re
import Queue
from threading import Thread

class WorkerGetHtml(Thread):
    def __init__(self, queueUrl, queueHtml):
        Thread.__init__(self)
        self.queueUrl = queueUrl
        self.queueHtml = queueHtml

    def run(self):
        while True:
            url = self.queueUrl.get()
            print "[get] %s %s" % (url[0], url[1])
            response = urllib2.urlopen(url[1], timeout=5)

            if response.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(response.read())
                f = gzip.GzipFile(fileobj=buf)
                html = f.read()
            else:
                html = response.read()

            self.queueHtml.put([url[0], html])
            self.queueUrl.task_done()

class WorkerParserHtml(Thread):
    def __init__(self, queueHtml, queueUrl):
        Thread.__init__(self)
        self.queueHtml = queueHtml
        self.queueUrl = queueUrl

    def run(self):
        while True:
            html = self.queueHtml.get()
            deep = html[0] + 1
            soup = BeautifulSoup(html[1])
            count = 0
            for link in soup.findAll('a', attrs={'href': re.compile("^http://")}):
                href = link.get('href')
                count = count + 1
                self.queueUrl.put([deep, href])
                print "[href] %s %s" % (deep, href)
            print count
            self.queueHtml.task_done()

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', dest="url", default="http://www.sina.com.cn", help="")
    parser.add_argument("-d", type=int, dest="deep", default=1, help="")  
    parser.add_argument("--thread", type=int, dest="deep", default=10, help="")  
    parser.add_argument('--dbfile', dest="dbfile", default="page.db", help="")
    parser.add_argument('--key', dest="key", default="", help="")
    parser.add_argument('-l', dest="loglevel", default="1", help="")
    parser.add_argument('--testself', dest="key", default="", help="")
    args = parser.parse_args()

    queueUrl = Queue.Queue()
    queueUrl.put([0, args.url])
    queueHtml = Queue.Queue()

    t = WorkerGetHtml(queueUrl, queueHtml)
    t.setDaemon(True)
    t.start()

    t1 = WorkerParserHtml(queueHtml, queueUrl)
    t1.setDaemon(True)
    t1.start()

    queueUrl.join()
    queueHtml.join()

if __name__ == "__main__":
    main()
