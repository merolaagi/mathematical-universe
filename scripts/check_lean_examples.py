"""Check only the repository's maintained examples; never an HTTP execution endpoint."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'dist'
examples=[
 ('Implication','Compose two proof steps',['reason:deep:gronwall','concept:logic'],'This checks composition of explicit hypotheses, not the truth of either hypothesis.'),
 ('Contradiction','Incompatible integer bounds',['reason:bounds','reason:catalan','college:limsup'],'An integer teaching model. It does not formalize the manuscript’s real limits or numerical estimates.'),
 ('Nonvanishing','A finite valuation implies nonzero',['reason:nonzero','reason:deep:source-nonzero','reason:deep:finite-valuation'],'Uses an abstract Option-valued model. The finite-valuation hypothesis is supplied, not proved for a research determinant.'),
 ('Induction','The finite-sum formula by induction',['reason:sum','reason:induction','concept:induction'],'Checks the exact natural-number identity 2·sumTo n=n(n+1), including n=0.'),
 ('SharedLemma','Reuse a lemma in two proofs',['concept:integers','concept:graphs'],'An elementary example of two results sharing the same proved prerequisite.')]
library=json.loads((R/'lean-library.json').read_text())
examples.extend((e['id'],e['title'],e['nodeIds'],e['scope']) for e in library)
categories={e['id']:e['category'] for e in library}
assert len({e[0] for e in examples})==len(examples)
node_ids={n['id'] for filename in ['foundations','reasoning','paths','decomposition','catalogue'] for n in json.loads((R/(filename+'.json')).read_text())['nodes']}
assert all(node in node_ids for e in examples for node in e[2])
version=subprocess.check_output(['lean','--version'],text=True).strip();result=[]
for file,title,ids,scope in examples:
 path=R/'lean'/f'{file}.lean';code=path.read_text()
 assert not re.search(r'\b(sorry|admit|axiom|unsafe)\b',code),file
 check=subprocess.run(['lean',str(path)],capture_output=True,text=True,timeout=30)
 output=check.stdout+check.stderr
 assert check.returncode==0 and 'sorryAx' not in output and 'warning:' not in output,(file,output)
 result.append(dict(id=file,title=title,category=categories.get(file,'Getting started'),nodeIds=ids,scope=scope,code=code,file='lean/'+file+'.lean',sha256=hashlib.sha256(code.encode()).hexdigest(),compilerOutput=output.strip()))
# Ensure a failed proof and an admitted proof are not confused with completed proofs.
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'Bad.lean';p.write_text('example : False := by\n  exact True.intro\n')
 bad=subprocess.run(['lean',str(p)],capture_output=True,text=True,timeout=30);assert bad.returncode!=0
 p.write_text('theorem unfinished : False := by\n  sorry\n#print axioms unfinished\n')
 admitted=subprocess.run(['lean',str(p)],capture_output=True,text=True,timeout=30);assert 'sorryAx' in admitted.stdout
(R/'lean-examples.json').write_text(json.dumps(dict(compiler=version,scope='Local check of bundled file bytes only. Live editor changes are checked separately by Lean Web.',examples=result),ensure_ascii=False,indent=2))
print(f'PASS: {len(result)} bundled files checked; failed and admitted proofs distinguished.');print(version)
