from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from covalent_ext import covapie_independent_group_expansion_struct_conn_crosscheck_smoke as g
def text(a='CYS',b='E64',atom='C1',typ='covale'):
 atom = "''" if atom == '' else atom
 return f"loop_\n_struct_conn.id\n_struct_conn.conn_type_id\n_struct_conn.ptnr1_label_comp_id\n_struct_conn.ptnr1_label_atom_id\n_struct_conn.ptnr2_label_comp_id\n_struct_conn.ptnr2_label_atom_id\n1 {typ} {a} SG {b} {atom}\n#\n"
def test_parser_helper_and_partner_direction():
 tags,rows,status=g.parser.parse_struct_conn_loop(text())
 assert status=='parsed_loop' and len(rows)==1
 a,b=g.partner(rows[0],'ptnr1'),g.partner(rows[0],'ptnr2')
 assert a['comp']=='CYS' and a['atom']=='SG' and b['comp']=='E64'
 tags,rows,status=g.parser.parse_struct_conn_loop(text('E64','CYS','SG'))
 a,b=g.partner(rows[0],'ptnr1'),g.partner(rows[0],'ptnr2')
 assert b['comp']=='CYS' and b['atom']=='SG'
def test_no_struct_conn_and_normalization():
 tags,rows,status=g.parser.parse_struct_conn_loop('data_x\n_entry.id x\n')
 assert status=='loop_not_found' and rows==[]
 assert g.clean('?')=='' and g.clean('e64')=='E64'
def test_classification_branches_and_missing_ligand_atom():
 _,rows,status=g.parser.parse_struct_conn_loop(text())
 assert g.classify_struct_conn_candidate(rows,status,'E64')['classification']=='confirmed_unique_exact_match'
 _,rows,status=g.parser.parse_struct_conn_loop(text('CYS','BAD'))
 assert g.classify_struct_conn_candidate(rows,status,'E64')['classification']=='blocked_expected_het_not_present_in_covalent_rows'
 _,rows,status=g.parser.parse_struct_conn_loop(text('CYS','E64','C1','metalc'))
 assert g.classify_struct_conn_candidate(rows,status,'E64')['classification']=='blocked_no_covalent_struct_conn_rows'
 _,rows,status=g.parser.parse_struct_conn_loop(text('CYS','E64',''))
 assert g.classify_struct_conn_candidate(rows,status,'E64')['classification']=='blocked_missing_ligand_covalent_atom_name'
 multi = text().replace('1 covale CYS SG E64 C1', '1 covale CYS SG E64 C1\n2 covale CYS SG E64 C2')
 _,rows,status=g.parser.parse_struct_conn_loop(multi)
 assert g.classify_struct_conn_candidate(rows,status,'E64')['classification']=='requires_manual_disambiguation_multiple_exact_matches'
 assert g.classify_struct_conn_candidate([], 'loop_not_found', 'E64')['classification']=='blocked_no_struct_conn_category'
 assert g.classify_struct_conn_candidate([], 'parse_error', 'E64')['classification']=='blocked_parse_error'
 assert g.classify_struct_conn_candidate(rows,status,'E64',False)['classification']=='blocked_raw_fingerprint_mismatch'
