import pdb
import sys
import json

import rdflib
from rdflib import RDF, RDFS, URIRef
from rdflib.plugins.parsers.notation3 import BadSyntax

def get_tagset(raw):
    assert isinstance(raw, URIRef)
    return str(raw).split('#')[-1]

def parse_topclass(tagset):
    return tagset.split('_')[-1]

with open('config.json', 'r') as fp:
    config = json.load(fp)

BRICK_VERSION = config['version']
BRICK = 'https://brickschema.org/schema/{0}/Brick#'.format(BRICK_VERSION)
BF = 'https://brickschema.org/schema/{0}/BrickFrame#'.format(BRICK_VERSION)

query_prefix = """
prefix rdf: <{0}>
prefix rdfs: <{1}>
prefix brick: <{2}>
prefix bf: <{3}>
""".format(RDF, RDFS, BRICK, BF)

################### Check schema files are well-formatted ###########
basedir = './dist/'
filenames = [basedir + filename for filename in
             ['Brick.ttl', 'BrickFrame.ttl', 'BrickUse.ttl', 'BrickTag.ttl']]
for filename in filenames:
    g = rdflib.Graph()
    try:
        g.parse(filename, format='turtle')
    except BadSyntax as e:
        print('Wrong syntax in {0}'.format(filename))
        print(e.message)
        sys.exit()


g = rdflib.Graph()
g.parse('./dist/Brick.ttl', format='turtle')

################### Check if Point names are correct ###################
point_topclasses = ['Meter', 'Sensor', 'Setpoint',
                    'Alarm', 'Status', 'Command']
point_topclass_dict = {topclass:[topclass] for topclass in point_topclasses}
postfixes = {topclass: [topclass] for topclass in point_topclasses}
postfixes['Status'].append('LED')
postfixes['Setpoint'].append('Factor')
postfixes['Setpoint'].append('Step')
# Should I add 'Resource' here?
for topclass in point_topclasses:
    q = query_prefix + """
    select ?s where {{
      ?s rdfs:subClassOf+ brick:{0}.
      }}
    """.format(topclass)
    res = g.query(q)
    for row in res:
        tagset = get_tagset(row[0])
        extracted_topclass = parse_topclass(tagset)
        try:
            assert extracted_topclass in postfixes[topclass]
        except:
            print('INCORRECT: {0} in {1}'.format(tagset, topclass))
        point_topclass_dict[topclass].append(tagset)

################### Check all Points are well classifier ###################
qstr_alltagsets = query_prefix + """
select ?s where {
  ?s rdfs:subClassOf+ bf:TagSet.
}
"""
res = g.query(qstr_alltagsets)
curr_tagsets = [get_tagset(row[0]) for row in res]
for tagset in curr_tagsets:
    topclass = parse_topclass(tagset)
    if topclass in point_topclass_dict:
        try:
            assert tagset in point_topclass_dict[topclass]
        except:
            print('INCORRECT: {0} is not in {1}'.format(tagset, topclass))

###### Compare it to the previous version in origin/master ######
prev_g = rdflib.Graph()
prev_g.parse('https://raw.githubusercontent.com/BuildSysUniformMetadata/Brick/master/dist/Brick.ttl', format='turtle')
res = prev_g.query(qstr_alltagsets)
prev_tagsets = [get_tagset(row[0]) for row in res]

removed_tagsets = [tagset for tagset in prev_tagsets
                   if tagset not in curr_tagsets]
new_tagsets = [tagset for tagset in curr_tagsets
               if tagset not in prev_tagsets]

print('Removed: {0}'.format(removed_tagsets))
print('Added: {0}'.format(new_tagsets))


print('Test complete.')
