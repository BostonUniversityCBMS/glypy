import glypy
from glypy.structure import constants, substituent, glycan
from glypy.structure import link, named_structures, structure_composition
from glypy.io import glycoct, linear_code
from glypy.utils import StringIO, identity as ident_op, multimap, pickle, ET, enum

structures = {}

monosaccharides = glypy.monosaccharides


def emit(arg):
    print(arg)
    return arg


def load(name):
    structure_composition.do_warn = False
    res = glycoct.loads(structures[name])
    structure_composition.do_warn = True
    return res


structures["common_glycan"] = '''
RES
1b:b-dglc-HEX-1:5
2b:b-dgal-HEX-1:5
3b:b-dglc-HEX-1:5
4s:n-acetyl
5b:a-lgal-HEX-1:5|6:d
6b:b-dgal-HEX-1:5
7b:b-dglc-HEX-1:5
8s:n-acetyl
9b:a-lgal-HEX-1:5|6:d
10b:b-dgal-HEX-1:5
LIN
1:1o(4+1)2d
2:2o(3+1)3d
3:3d(2+1)4n
4:3o(3+1)5d
5:3o(4+1)6d
6:6o(3+1)7d
7:7d(2+1)8n
8:7o(3+1)9d
9:7o(4+1)10d'''

structures["branchy_glycan"] = '''
RES
1b:x-dglc-HEX-x:x
2s:n-acetyl
3b:b-dman-HEX-1:5
4b:a-dman-HEX-1:5
5b:b-dglc-HEX-1:5
6s:n-acetyl
7b:b-dgal-HEX-1:5
8b:b-dglc-HEX-1:5
9s:n-acetyl
10b:b-dgal-HEX-1:5
11b:a-dman-HEX-1:5
12b:b-dglc-HEX-1:5
13s:n-acetyl
14b:b-dgal-HEX-1:5
LIN
1:1d(2+1)2n
2:1o(4+1)3d
3:3o(3+1)11d
4:3o(6+1)4d
5:4o(2+1)8d
6:4o(6+1)5d
7:5d(2+1)6n
8:5o(4+1)7d
9:8d(2+1)9n
10:8o(4+1)10d
11:11o(2+1)12d
12:12d(2+1)13n
13:12o(4+1)14d'''

structures["broad_n_glycan"] = '''
RES
1b:b-dglc-HEX-1:5
2s:n-acetyl
3b:b-dglc-HEX-1:5
4s:n-acetyl
5b:b-dman-HEX-1:5
6b:a-dman-HEX-1:5
7b:b-dglc-HEX-1:5
8s:n-acetyl
9b:b-dgal-HEX-1:5
10b:a-lgal-HEX-1:5|6:d
11b:b-dglc-HEX-1:5
12s:n-acetyl
13b:b-dgal-HEX-1:5
14b:a-dman-HEX-1:5
15b:b-dglc-HEX-1:5
16s:n-acetyl
17b:b-dgal-HEX-1:5
18b:b-dglc-HEX-1:5
19s:n-acetyl
20b:b-dgal-HEX-1:5
LIN
1:1d(2+1)2n
2:1o(4+1)3d
3:3d(2+1)4n
4:3o(4+1)5d
5:5o(3+1)14d
6:5o(6+1)6d
7:6o(2+1)11d
8:6o(6+1)7d
9:7d(2+1)8n
10:7o(3+1)10d
11:7o(4+1)9d
12:11d(2+1)12n
13:11o(4+1)13d
14:14o(2+1)18d
15:14o(4+1)15d
16:15d(2+1)16n
17:15o(4+1)17d
18:18d(2+1)19n
19:18o(4+1)20d'''

structures["sulfated_glycan"] = '''
RES
1b:o-dgal-HEX-0:0|1:aldi
2b:b-dglc-HEX-1:5
3s:n-acetyl
4b:b-dgal-HEX-1:5
5b:b-dglc-HEX-1:5
6s:n-acetyl
7b:b-dgal-HEX-1:5
8b:a-dgro-dgal-NON-2:6|1:a|2:keto|3:d
9s:n-acetyl
10s:sulfate
11s:sulfate
12s:sulfate
LIN
1:1o(3+1)2d
2:2d(2+1)3n
3:2o(4+1)4d
4:4o(3+1)5d
5:5d(2+1)6n
6:5o(4+1)7d
7:7o(6+2)8d
8:8d(5+1)9n
9:5o(6+1)10n
10:4o(6+1)11n
11:2o(6+1)12n
'''

structures["complex_glycan"] = '''
RES
1b:x-dglc-HEX-1:5
2s:n-acetyl
3b:b-dglc-HEX-1:5
4s:n-acetyl
5b:b-dman-HEX-1:5
6b:a-dman-HEX-1:5
7b:b-dglc-HEX-1:5
8s:n-acetyl
9b:a-lgal-HEX-1:5|6:d
10b:b-dgal-HEX-1:5
11b:a-dgro-dgal-NON-2:6|1:a|2:keto|3:d
12s:n-glycolyl
13b:b-dglc-HEX-1:5
14s:n-acetyl
15b:b-dgal-HEX-1:5
16s:n-acetyl
17b:b-dglc-HEX-1:5
18s:n-acetyl
19b:a-dman-HEX-1:5
20b:b-dglc-HEX-1:5
21s:n-acetyl
22b:a-lgal-HEX-1:5|6:d
23b:b-dgal-HEX-1:5
24b:a-dgro-dgal-NON-2:6|1:a|2:keto|3:d
25s:n-glycolyl
26b:b-dglc-HEX-1:5
27s:n-acetyl
28b:a-lgal-HEX-1:5|6:d
29b:b-dgal-HEX-1:5
30b:a-dgro-dgal-NON-2:6|1:a|2:keto|3:d
31s:n-acetyl
32b:a-lgal-HEX-1:5|6:d
LIN
1:1d(2+1)2n
2:1o(4+1)3d
3:3d(2+1)4n
4:3o(4+1)5d
5:5o(3+1)6d
6:6o(2+1)7d
7:7d(2+1)8n
8:7o(3+1)9d
9:7o(4+1)10d
10:10o(3+2)11d
11:11d(5+1)12n
12:6o(4+1)13d
13:13d(2+1)14n
14:13o(4+1)15d
15:15d(2+1)16n
16:5o(4+1)17d
17:17d(2+1)18n
18:5o(6+1)19d
19:19o(2+1)20d
20:20d(2+1)21n
21:20o(3+1)22d
22:20o(4+1)23d
23:23o(3+2)24d
24:24d(5+1)25n
25:19o(6+1)26d
26:26d(2+1)27n
27:26o(3+1)28d
28:26o(4+1)29d
29:29o(3+2)30d
30:30d(5+1)31n
31:1o(6+1)32d
'''


structures["complex_glycan_with_ambiguous_link"] = '''
RES
1b:x-dglc-HEX-1:5
2s:n-acetyl
3b:b-dglc-HEX-1:5
4s:n-acetyl
5b:b-dman-HEX-1:5
6b:a-dman-HEX-1:5
7b:b-dglc-HEX-1:5
8s:n-acetyl
9b:a-lgal-HEX-1:5|6:d
10b:b-dgal-HEX-1:5
11b:a-dgro-dgal-NON-2:6|1:a|2:keto|3:d
12s:n-glycolyl
13b:b-dglc-HEX-1:5
14s:n-acetyl
15b:b-dgal-HEX-1:5
16s:n-acetyl
17b:b-dglc-HEX-1:5
18s:n-acetyl
19b:a-dman-HEX-1:5
20b:b-dglc-HEX-1:5
21s:n-acetyl
22b:a-lgal-HEX-1:5|6:d
23b:b-dgal-HEX-1:5
24b:a-dgro-dgal-NON-2:6|1:a|2:keto|3:d
25s:n-glycolyl
26b:b-dglc-HEX-1:5
27s:n-acetyl
28b:a-lgal-HEX-1:5|6:d
29b:b-dgal-HEX-1:5
30b:a-dgro-dgal-NON-2:6|1:a|2:keto|3:d
31s:n-acetyl
32b:a-lgal-HEX-1:5|6:d
LIN
1:1d(2+1)2n
2:1o(4+1)3d
3:3d(2+1)4n
4:3o(4+1)5d
5:5o(3+1)6d
6:6o(2+1)7d
7:7d(2+1)8n
8:7o(3+1)9d
9:7o(4+1)10d
10:10o(3+2)11d
11:11d(5+1)12n
12:6o(4+1)13d
13:13d(2+1)14n
14:13o(4+1)15d
15:15d(2+1)16n
16:5o(4+1)17d
17:17d(2+1)18n
18:5o(6+1)19d
19:19o(2+1)20d
20:20d(2+1)21n
21:20o(3+1)22d
22:20o(4+1)23d
23:23o(3+2)24d
24:24d(5+1)25n
25:19o(6+1)26d
26:26d(2+1)27n
27:26o(3+1)28d
28:26o(4+1)29d
29:29o(3+2|6)30d
30:30d(5+1)31n
31:1o(6+1)32d
'''


structures["cyclical_glycan"] = '''
RES
1b:a-dglc-HEX-1:5
2b:a-dglc-HEX-1:5
3b:a-dglc-HEX-1:5
4b:a-dglc-HEX-1:5
LIN
1:1o(3+1)2d
2:2o(6+1)3d
3:3o(3+1)4d
4:4o(6+1)1d
'''

structures["repeating_glycan"] = '''
RES
1b:a-dglc-HEX-1:5
2b:a-dglc-HEX-1:5
3r:r1
4b:b-dara-HEX-2:5|2:keto
LIN
1:1o(1+1)2d
2:2o(6+2)3n
3:3n(1+2)4d
REP
REP1:5o(1+2)5d=-1--1
RES
5b:b-dara-HEX-2:5|2:keto
'''

structures["big_repeating_glycan"] = '''
RES
1b:b-dglc-HEX-1:5
2s:n-acetyl
3b:b-dglc-HEX-1:5
4s:n-acetyl
5b:b-dman-HEX-1:5
6b:a-dman-HEX-1:5
7b:b-dglc-HEX-1:5
8s:n-acetyl
9b:b-dgal-HEX-1:5
10b:b-dglc-HEX-1:5
11s:n-acetyl
12b:b-dgal-HEX-1:5
13r:r1
14b:b-dglc-HEX-1:5
15s:n-acetyl
16b:b-dgal-HEX-1:5
17b:a-dgro-dgal-NON-2:6|1:a|2:keto|3:d
18s:n-acetyl
19b:a-dman-HEX-1:5
20b:b-dglc-HEX-1:5
21s:n-acetyl
22b:b-dgal-HEX-1:5
23r:r2
24b:b-dglc-HEX-1:5
25s:n-acetyl
26b:b-dgal-HEX-1:5
27b:a-dgro-dgal-NON-2:6|1:a|2:keto|3:d
28s:n-acetyl
29b:a-lgal-HEX-1:5|6:d
LIN
1:1d(2+1)2n
2:1o(4+1)3d
3:3d(2+1)4n
4:3o(4+1)5d
5:5o(3+1)6d
6:6o(2+1)7d
7:7d(2+1)8n
8:7o(4+1)9d
9:9o(3+1)10d
10:10d(2+1)11n
11:10o(4+1)12d
12:6o(4+1)13n
13:13n(3+1)14d
14:14d(2+1)15n
15:14o(4+1)16d
16:16o(3|6+2)17d
17:17d(5+1)18n
18:5o(6+1)19d
19:19o(2+1)20d
20:20d(2+1)21n
21:20o(4+1)22d
22:19o(6+1)23n
23:23n(3+1)24d
24:24d(2+1)25n
25:24o(4+1)26d
26:26o(3|6+2)27d
27:27d(5+1)28n
28:1o(6+1)29d
REP
REP1:32o(3+1)30d=-1--1
RES
30b:b-dglc-HEX-1:5
31s:n-acetyl
32b:b-dgal-HEX-1:5
33b:b-dglc-HEX-1:5
34s:n-acetyl
35b:a-dgal-HEX-1:5
36b:a-dgal-HEX-1:5
LIN
29:30d(2+1)31n
30:30o(4+1)32d
31:32o(6+1)33d
32:33d(2+1)34n
33:33o(4+1)35d
34:35o(3+1)36d
REP2:39o(3+1)37d=-1--1
RES
37b:b-dglc-HEX-1:5
38s:n-acetyl
39b:b-dgal-HEX-1:5
40b:b-dglc-HEX-1:5
41s:n-acetyl
42b:a-dgal-HEX-1:5
43b:a-dgal-HEX-1:5
LIN
35:37d(2+1)38n
36:37o(4+1)39d
37:39o(6+1)40d
38:40d(2+1)41n
39:40o(4+1)42d
40:42o(3+1)43d
'''