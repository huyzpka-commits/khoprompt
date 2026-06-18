import urllib.request

html = urllib.request.urlopen('http://localhost:8080/').read().decode('utf-8')
print('index status:', 200)
print('pagination id:', 'id="pagination"' in html)
print('per-page id:', 'id="per-page"' in html)
print('prompts.json:', urllib.request.urlopen('http://localhost:8080/data/prompts.json').status)
print('app.js:', urllib.request.urlopen('http://localhost:8080/js/app.js').status)
print('style.css:', urllib.request.urlopen('http://localhost:8080/css/style.css').status)
