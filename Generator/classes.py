import urllib
import requests

url = "http://beatconnect.io/b/1030134"
req = urllib.request.Request(url, method='HEAD')
r = urllib.request.urlopen(req)
filename = urllib.parse.unquote(r.info().get_filename())  # decode the encoded non ASCII chars (e.g !)
filesize = r.headers['Content-Length']
print(filesize)