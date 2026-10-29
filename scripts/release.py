"""Publish frontend edits in this directory to the running Mac-hosted app."""
import hashlib,json,re,os
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'dist'
html=(root/'index.html').read_text()
html=re.sub(r'<meta name="mathuni-build" content="[^"]*">','',html)
html=re.sub(r'(style\.css|app\.js|panel\.js)\?v=[a-z0-9]+',r'\1',html)
digest=hashlib.sha256(html.encode()+b''.join((root/p).read_bytes() for p in ['style.css','app.js','panel.js','foundations.json','reasoning.json'])).hexdigest()[:16]
html=html.replace('</head>',f'<meta name="mathuni-build" content="{digest}"></head>')
for p in ['style.css','app.js','panel.js']:html=html.replace('"'+p+'"','"'+p+'?v='+digest+'"')
def write(path,content):
 temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(content);os.replace(temp,path)
write(root/'index.html',html)
write(root/'version.json',json.dumps({'build':digest}))
print('Published frontend build',digest,'to the live directory. Active tabs check for updates every 30 seconds.')
