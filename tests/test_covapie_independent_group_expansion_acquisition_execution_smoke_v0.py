from __future__ import annotations
import sys
from pathlib import Path
SRC=Path(__file__).resolve().parents[1]/'src'
if str(SRC) not in sys.path:sys.path.insert(0,str(SRC))
from covalent_ext import covapie_independent_group_expansion_acquisition_execution_smoke as gate
def payload(pdb):return f"data_{pdb}\n_entry.id {pdb}\n_atom_site.group_PDB\n"+('x'*1200)
def fake(url,part):part.write_text(payload(Path(url).stem));return 0,'200'
def test_fake_download_atomic_rename_and_integrity(tmp_path):
 raw=tmp_path/'raw';downloads,integrities,failures=gate.acquire(True,raw,fake)
 assert len(downloads)==len(integrities)==8 and failures[0]['failure_id']=='NO_ACQUISITION_FAILURES'
 assert all(r['download_status']=='downloaded' and r['final_atomic_rename_completed'] for r in downloads)
 assert all(r['integrity_status']=='passed' and len(r['sha256'])==64 for r in integrities)
 assert not list(raw.glob('*.part'))
def test_reuse_html_rejection_and_no_network(tmp_path):
 raw=tmp_path/'raw';raw.mkdir();(raw/'1aec.cif').write_text(payload('1aec'))
 calls=[]
 def never(url,part):calls.append(url);return 0,'200'
 downloads,integrities,failures=gate.acquire(False,raw,never)
 assert not calls and downloads[0]['download_status']=='reused_existing_valid_raw' and len(failures)==7
 bad=tmp_path/'bad.cif';bad.write_text('<html>bad</html>')
 assert gate.integrity(bad)['passed'] is False
