# Warhead-Only Bond-Order Trial QA Summary

This is a QA report only.

- It does not modify raw ligand SDF files.
- It does not modify repaired trial SDF files.
- It does not create pre-reaction graphs.
- It does not modify manifest files.
- It does not mark samples as training-ready.

| sample_id | total_rows | passed_rows | failed_rows | transferred_rows | kept_rows | blocked_rows | coordinate_hash_same_all | raw_sdf_hash_same_all | blocked_bonds_unchanged | boundary_touches_blocked |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTK_C481_6DI9 | 35 | 35 | 0 | 2 | 1 | 32 | true | true | true | true |
| KRAS_G12C_5F2E | 33 | 33 | 0 | 2 | 1 | 30 | true | true | true | true |
| KRAS_G12C_6OIM | 45 | 45 | 0 | 1 | 2 | 42 | true | true | true | true |

## Global Conclusion

- All QA passed: true.
- Repaired trial SDF files remain derived curation artifacts only.
- No sample is training-ready yet.
