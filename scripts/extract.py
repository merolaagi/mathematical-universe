"""Conservative source graph: references are not asserted logical dependencies."""
import re, json, sys, hashlib, html, subprocess, gzip
from pathlib import Path
from collections import Counter
root=Path(sys.argv[1]).resolve(); out=Path(__file__).resolve().parents[1]/'dist'
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
base=f'https://github.com/openai/math/blob/{sha}/'
nodes={}; edges=[]; edgekeys=set(); details={}
def clean(s):
 s=html.unescape(re.sub(r'<[^>]+>','',s)).replace('$`','$').replace('`$','$')
 s=re.sub(r'\\(?:label|index)\{[^}]*\}','',s)
 return re.sub(r'\s+',' ',s).strip()
def short(s,n=300):
 s=clean(s); return s[:n]+('…' if len(s)>n else '')
def add(id,kind,title,summary='',detail='',**kw):
 if id not in nodes:
  nodes[id]=dict(id=id,kind=kind,title=clean(title),summary=short(summary),**kw)
  if detail: details[id]=detail
 return id
def edge(a,b,t,evidence=''):
 if a==b:return
 k=(a,b,t)
 if k not in edgekeys: edges.append(dict(source=a,target=b,type=t,evidence=evidence));edgekeys.add(k)
def key(s):return hashlib.sha1(s.encode()).hexdigest()[:16]
subjects={}; subject=''
for ln in (root/'overview.tex').read_text().splitlines():
 m=re.match(r'\\cataloguesection\{([^}]+)\}',ln)
 if m:subject=m[1]
 m=re.match(r'\\resultentry\{(\d+)\}',ln)
 if m:subjects[m[1]]=subject
contents=(root/'CONTENTS.md').read_text(); family=None; papers=[]
for block in re.findall(r'<td>(.*?)</td>',contents,re.S):
 m=re.search(r'\*\*(\d+)\. (.*?)\*\*\s*(.*)',block,re.S)
 if m:
  fid,title,summary=m.groups(); family='f'+fid
  add(family,'Family',fid+' · '+title,summary,summary,subject=subjects.get(fid,''),url=base+'CONTENTS.md',formalization='Scope documented' if '(Lean)' in summary or '[Lean]' in summary else 'Not catalogued')
  doc=root/f'lean/docs/{fid}.md'
  if doc.exists():
   scope=add('lean'+fid,'Formalization','Lean scope · '+fid,doc.read_text(),doc.read_text(),url=base+str(doc.relative_to(root)),family=family)
   edge(family,scope,'HAS_FORMALIZATION')
  for ref in re.findall(r'\bresult[s]? (\d{3})\b',summary):edge(family,'f'+ref,'CATALOGUE_REFERENCE',short(summary,600))
 else:
  m=re.search(r'\[([^\n]+?)\]\((preprints/[^\n]+?\.pdf)\)\s*(.*)',block,re.S)
  if m and family:
   title,path,abstract=m.groups(); pid='m'+key(path)
   add(pid,'Manuscript',title,abstract,clean(abstract),url=base+path,family=family,subject=nodes[family]['subject'])
   edge(family,pid,'HAS_MANUSCRIPT');papers.append((pid,path))
def braced(s,start):
 depth=0
 for i in range(start,len(s)):
  if s[i]=='{':depth+=1
  if s[i]=='}':
   depth-=1
   if depth==0:return s[start+1:i]
 return ''
def normalized(s):return re.sub(r'[^a-z0-9]','',s.lower())
title_index={}
for pid,_ in papers:title_index.setdefault(normalized(nodes[pid]['title']),[]).append(pid)
for pi,(pid,pdf) in enumerate(papers):
 directory=root/Path(pdf).parent; files=sorted(directory.rglob('*.tex')); labels={}; blocks=[]; sources={}
 envs={'theorem':'Statement','lemma':'Statement','proposition':'Statement','corollary':'Statement','definition':'Definition','assumption':'Assumption','axiom':'Axiom','claim':'Statement','proof':'Proof'}
 for f in files:
  text=f.read_text(errors='replace');sources[f]=text
  for en,display in re.findall(r'\\newtheorem\*?\{([^}]+)\}(?:\[[^\]]*\])?\{([^}]+)\}',text):
   envs[en]='Definition' if 'definition' in display.lower() else ('Assumption' if 'assumption' in display.lower() else 'Statement')
 for f,text in sources.items():
  # Mask comments without changing offsets or line numbers.
  masked=re.sub(r'(?<!\\)%[^\n]*',lambda m:' '*len(m[0]),text)
  pattern=r'\\begin\{('+ '|'.join(re.escape(x) for x in envs)+r')\}(?:\[([^\]]*)\])?(.*?)\\end\{\1\}'
  last=None; lastend=0
  for ix,m in enumerate(re.finditer(pattern,masked,re.S)):
   en,heading,body=m.groups(); kind=envs[en]; line=text.count('\n',0,m.start())+1
   nid='n'+key(pid+str(f.relative_to(root))+str(m.start())); labs=re.findall(r'\\label\{([^}]+)\}',body)
   title=(heading or (labs[0] if labs else en.capitalize()+' · '+f.stem+':'+str(line)))
   url=base+str(f.relative_to(root))+'#L'+str(line)
   add(nid,kind,title,body,body,url=url,family=nodes[pid]['family'],manuscript=pid,extraction='Source excerpt; unreviewed')
   edge(pid,nid,'CONTAINS');blocks.append((nid,body))
   for lab in labs:labels.setdefault(lab,[]).append(nid)
   if kind=='Proof':
    if last and not masked[lastend:m.start()].strip():edge(last,nid,'FOLLOWED_BY_PROOF','Adjacent statement/proof environments; attachment unreviewed')
    # Paragraph passages are navigation units, not certified inference steps.
    paragraphs=[p for p in re.split(r'\n\s*\n',body) if clean(p)]
    for j,p in enumerate(paragraphs):
     sid=nid+'s'+str(j+1)
     add(sid,'Step','Passage '+str(j+1)+' · '+short(p,65),p,p,url=url,family=nodes[pid]['family'],manuscript=pid,extraction='Proof paragraph; not a verified inference')
     edge(nid,sid,'HAS_PASSAGE',str(j+1));blocks.append((sid,p))
   last=nid if kind!='Proof' else None;lastend=m.end()
  # Include labels outside theorem environments (equations, sections, etc.).
  for m in re.finditer(r'\\label\{([^}]+)\}',masked):
   lab=m[1]
   if lab in labels:continue
   line=text.count('\n',0,m.start())+1;nid='r'+key(pid+lab)
   excerpt=text[max(0,m.start()-350):m.end()+700]
   add(nid,'Reference',lab,excerpt,excerpt,url=base+str(f.relative_to(root))+'#L'+str(line),family=nodes[pid]['family'],manuscript=pid,extraction='Context excerpt around source label')
   labels[lab]=[nid];edge(pid,nid,'CONTAINS')
 bibliography={}
 for bf in sorted(directory.rglob('*.bib')):
  raw=bf.read_text(errors='replace')
  for bm in re.finditer(r'@\w+\s*\{\s*([^,]+),',raw):
   entry=braced(raw,raw.index('{',bm.start()));tm=re.search(r'\btitle\s*=\s*\{',entry,re.I)
   title=braced(entry,tm.end()-1) if tm else bm[1]
   bibliography[bm[1].strip()]=(title,entry,base+str(bf.relative_to(root))+'#L'+str(raw.count('\n',0,bm.start())+1))
 for nid,body in blocks:
  for refs in re.findall(r'\\(?:eqref|ref|cref|Cref|autoref)\*?\{([^}]+)\}',body):
   for lab in refs.split(','):
    lab=lab.strip(); targets=labels.get(lab,[])
    if len(targets)==1:target=targets[0]
    else:
     target='u'+key(pid+lab)
     add(target,'Prerequisite',lab,'Unresolved or ambiguous source reference. Derivation not imported.',url=nodes[pid]['url'],family=nodes[pid]['family'])
    edge(nid,target,'REFERENCES',r'\ref{'+lab+'}')
  for refs in re.findall(r'\\cite\w*\*?(?:\[[^\]]*\])*\{([^}]+)\}',body):
   for citation in refs.split(','):
    citation=citation.strip(); cid='c'+key(pid+citation)
    title,entry,url=bibliography.get(citation,(citation,'Bibliographic prerequisite. Citation key is scoped to this manuscript; proof not imported.',nodes[pid]['url']))
    add(cid,'Citation',title,entry,entry,url=url,family=nodes[pid]['family'])
    edge(nid,cid,'CITES',citation)
    matches=title_index.get(normalized(title),[])
    if len(matches)==1:edge(cid,matches[0],'BIBLIOGRAPHIC_MATCH','Exact normalized title match; not a verified deduction')
 if pi%100==0:print('Parsed',pi,'manuscripts',flush=True)
# Drop catalogue references outside the actual corpus; no dangling relationships.
edges=[e for e in edges if e['source'] in nodes and e['target'] in nodes]
out.mkdir(exist_ok=True,parents=True);(out/'details').mkdir(exist_ok=True)
# Shard long proof text by family to avoid a giant initial download.
for family in [n['id'] for n in nodes.values() if n['kind']=='Family']:
 subset={id:text for id,text in details.items() if id==family or nodes[id].get('family')==family}
 (out/'details'/f'{family}.json.gz').write_bytes(gzip.compress(json.dumps(subset,ensure_ascii=False).encode(),mtime=0))
metadata=dict(commit=sha,source='https://github.com/openai/math',counts=dict(Counter(n['kind'] for n in nodes.values())),edges=len(edges),note='Extracted source structure. Reference edges are not certified deductions. Lean scope is reported by the source, not rechecked here.')
(out/'graphs').mkdir(exist_ok=True)
catalogue=[n for n in nodes.values() if n['kind'] in ('Family','Manuscript','Formalization')]
catalogue_ids={n['id'] for n in catalogue}
(out/'catalogue.json').write_text(json.dumps(dict(meta=metadata,nodes=catalogue,edges=[e for e in edges if e['source'] in catalogue_ids and e['target'] in catalogue_ids]),ensure_ascii=False,separators=(',',':')))
for family in [n['id'] for n in nodes.values() if n['kind']=='Family']:
 subset=[n for n in nodes.values() if n['id']==family or n.get('family')==family]; ids={n['id'] for n in subset}
 related=[e for e in edges if e['source'] in ids and (e['target'] in ids or e['type']=='BIBLIOGRAPHIC_MATCH')]
 (out/'graphs'/f'{family}.json.gz').write_bytes(gzip.compress(json.dumps(dict(nodes=subset,edges=related),ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
(out/'LICENSE-source.txt').write_text((root/'LICENSE').read_text())
print(json.dumps(metadata,indent=2))
