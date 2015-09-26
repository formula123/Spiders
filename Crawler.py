import bs4
import re
import os
import sys
import urllib
import urllib.request
import http.client

class Retriever(object):
    __slots__ = ('url', 'file')
    def __init__(self, url):
        self.url, self.file = self.get_file(url)

    def get_file(self, url, default = 'index.html'):
        '''Create usable local filename form url'''
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.split('@')[-1].split(':')[0]
        filepath = "%s%s" % (host, parsed.path)
        '''if not exist file,use default index.html'''
        if not os.path.splitext(parsed.path)[1]:
            filepath = os.path.join(filepath,default)
            linkdir = os.path.dirname(filepath)
            if not os.path.isdir(linkdir):
                if os.path.exists(linkdir):
                    os.unlink(linkdir)
        path = os.path.dirname(filepath)
        if not os.path.exists(path):
            os.makedirs(path)
        return url, filepath

    def download(self):
        '''download url to specific named file'''
        try:
            retval = urllib.request.urlretrieve(self.url, self.file)
        except(IOError, http.client.InvalidURL) as e:
            retval = ('**** Error: bad URL "%s":%s' % (self.url, e),)
        return retval

    def parse_links(self):
        '''Parse out the links found in downloaded HTML file'''
        try:
            with open(self.file, 'r') as f:
                soup = bs4.BeautifulSoup(f, 'html.parser')
                return [link.get('href') for link in soup.findAll('a')]
        except :
            print('could not link:')
            return []

class Crawler(object):
    count = 0

    def __init__(self, url):
        self.q = [url]
        self.seen  = set()
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.split('@')[-1].split(':')[0]
        self.dom = '.'.join(host.split('.')[-2:])

    def get_page(self, url, media = False):
        '''Download page & parse links, add to queue if nec'''
        r = Retriever(url)
        fname = r.download()[0]
        if fname[0] == '*':
            print(fname,'... skipping parse')
            return
        Crawler.count += 1
        print('\n(', Crawler.count, ')')
        print('URL:',url)
        print('FILE:',fname)
        self.seen.add(url)
        ftype = os.path.splitext(fname)[1]
        if ftype not in ('.html', 'htm','.asp','.aspx'):
            return

        for link in r.parse_links():
            if not media:
                ftype = os.path.splitext(link)[1]
                if ftype in ('.mp3', '.mp4', '.m4v', '.wav'):
                    print('discarded, media file')
                    continue
            if not link.startswith('http://'):
                link = urllib.parse.urljoin(url, link)
            print('*',link)
            if link not in self.seen:
                if self.dom not in link:
                    print('....discard, not in domain')
                else:
                    if link not in self.q:
                        self.q.append(link)
                        print('...new, added to Q')
                    else:
                        print('...discard, already in Q')
            else:
                print('...discard, already processed')
                
    def go(self, media = False):
        'Process next page in queue (if any)'
        while self.q:
            url = self.q.pop()
            self.get_page(url, media)


def main():
    if len(sys.argv) >1:
        url = sys.argv[1]
    else:
        try:
            url = input('Enter starting URL:')
        except (KeyboardInterrupt, EOFError):
            url = ''
    if not url:
        return
    if not url.startswith('http://') and \
       not url.startswith('ftp://'):
        url = 'http://%s/' %url
    robot = Crawler(url)
    robot.go()

if __name__ == '__main__':
    main()
