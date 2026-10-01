# Dataset revisions used for verification

The datasets are not redistributed. The final metrics were re-run against these public repository revisions during reconciliation:

| Dataset | Repository commit | Evaluated CSV SHA-256 |
|---|---|---|
| SDCNL training split | `ddf995aabd028657385cac6cee92c5d53774992d` | `0549f99f98686ffa3daa07c1a396214a8519f36fee38e379d849e94eb39a3687` |
| SDCNL test split | `ddf995aabd028657385cac6cee92c5d53774992d` | `0524dc2956fa26632bb36e595f3c8c7200f8f4ee376fce1a3463970a5a01fb5d` |
| Twitter suicidal-intention corpus | `d800024117181614aa908c821400cede24e07355` | `e2abd725b4f1c3d758e4df0c9f04416954ac96d9be61dc25a6c73cdaeecc470e` |

Repositories:

- `https://github.com/ayaanzhaque/SDCNL.git`
- `https://github.com/laxmimerit/twitter-suicidal-intention-dataset.git`

Verify the CSV hashes after acquisition before treating a run as comparable.
