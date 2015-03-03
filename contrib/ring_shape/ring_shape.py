import itertools
import pygly2
from pygly2 import Composition
from pygly2.structure import structure_composition, Monosaccharide, Glycan, constants
from pygly2.utils.multimap import OrderedMultiMap

SuperClass = constants.SuperClass
modification_compositions = structure_composition.modification_compositions

class CrossRingFragment(Monosaccharide):

    def __init__(self, composition, cleave_1, cleave_2, contains, kind,
                 modifications=None, anomer=None,
                 stem=None, configuration=None, id=None):
        super(CrossRingFragment, self).__init__(
            modifications=modifications, ring_start=None, ring_end=None,
            substituent_links=None, links=None, superclass=None, anomer=anomer,
            stem=stem, configuration=configuration, id=id, composition=composition)
        self.kind = kind
        self.cleave_1 = cleave_1
        self.cleave_2 = cleave_2
        self.contains = contains

    def __repr__(self):
        return "CrossRingFragment({kind}({c1}, {c2}) {contains} {mass})".format(
            kind=self.kind, c1=self.cleave_1, c2=self.cleave_2, contains=self.contains, mass=self.mass())

# https://code.google.com/p/eurocarb/source/browse/trunk/application/GlycanBuilder/ringfragments/Cross-ring-data.xml?r=383
# for validation


def crossring_fragments(monosaccharide, c1, c2):
    # if c1 < monosaccharide.ring_start or c2 > monosaccharide.ring_end:
    #     raise IndexError("Cannot cross-ring cleave outside the ring")
    c1_segment, c1_include, c2_segment, c2_include = cleave_ring(
        monosaccharide, c1, c2)

    c1_fragment = pack_fragment(c1_segment, c1, c2, c1_include, monosaccharide)
    c2_fragment = pack_fragment(c2_segment, c1, c2, c2_include, monosaccharide)

    # If the ring_end is cleaved, then the O component of
    # the ring should go with the X ion
    ring_start = monosaccharide.ring_start
    ring_end = monosaccharide.ring_end

    a_fragment = x_fragment = None
    if ring_start in c1_fragment.contains:
        x_fragment = c1_fragment
        x_fragment.kind = "X"
        a_fragment = c2_fragment
        a_fragment.kind = "A"
    else:
        x_fragment = c2_fragment
        x_fragment.kind = "X"
        a_fragment = c1_fragment
        a_fragment.kind = "A"



    if ring_end == c2:
        c1_fragment.composition = Composition(c1_fragment.composition) - {"O": 1}
        c2_fragment.composition = Composition(c2_fragment.composition) + {"O": 1}

    return a_fragment, x_fragment


def enumerate_cleavage_pairs(monosaccharide):
    for c1, c2 in itertools.combinations(range(monosaccharide.ring_start,
                                               monosaccharide.ring_end + 1), 2):
        if c2 - c1 > 1:
            yield c1, c2


def pack_fragment(fragment_parts, c1, c2, include, monosaccharide):
    fragment_data = {
        "composition": sum((c['backbone'] for c in fragment_parts), {}),
        "modifications": OrderedMultiMap(),
        "substituent_links": OrderedMultiMap(),
        "links": OrderedMultiMap(),
        "contains": include
    }

    for i in fragment_parts:
        fragment_data['links'].update(i['links'])
        fragment_data['modifications'].update(i['modifications'])
        fragment_data['substituent_links'].update(i['substituent_links'])

    fragment_object = CrossRingFragment(
        fragment_data['composition'], c1, c2, fragment_data['contains'],
        '?', fragment_data['modifications'], stem=monosaccharide.stem,
        configuration=monosaccharide.configuration, id=monosaccharide.id
    )

    composition_shift = Composition()
    for pos, mod in fragment_data["modifications"].items():
        composition_shift = composition_shift + modification_compositions[mod](pos)
    fragment_object.composition = fragment_object.composition + composition_shift

    for pos, link in fragment_data['substituent_links'].items():
        subst = link[monosaccharide]
        link.clone(fragment_object, subst.clone())

    for pos, link in fragment_data['links'].items():
        subtree = Glycan.subtree_from(link[monosaccharide])
        if link.is_parent(monosaccharide):
            link.clone(fragment_object, subtree)
        else:
            link.clone(subtree, fragment_object)
    return fragment_object


# http://en.wikipedia.org/wiki/Hexose for visual information
def unroll_ring(monosaccharide):
    ring_size = monosaccharide.superclass.value
    nodes = [None for i in range(ring_size)]
    for i in range(ring_size):
        segment = {
            "index": i + 1,
            "backbone": Composition("COH2"),
            "modifications": OrderedMultiMap(),
            "substituent_links": OrderedMultiMap(),
            "links": OrderedMultiMap()
        }
        for mod in (monosaccharide.modifications[i + 1]):
            segment['modifications'][i + 1] = mod

        for sub_link in monosaccharide.substituent_links[i + 1]:
            segment['substituent_links'][i + 1] = sub_link

        for glyco_link in monosaccharide.links[i + 1]:
            segment['links'][i + 1] = glyco_link

        nodes[i] = segment

    return nodes


def cleave_ring(monosaccharide, c1, c2):
    linear = unroll_ring(monosaccharide)
    ring_start = monosaccharide.ring_start
    ring_end = monosaccharide.ring_end
    c1_segment, c1_include, c2_segment, c2_include = slice_ring(
        linear[:ring_end], c1, c2, ring_start)

    if ring_start in c1_include and ring_start - 1 not in c1_include and ring_start != 1:
        c1_segment = linear[:ring_start] + c1_segment
        c1_include = list(i + 1 for i in range(ring_start + 1)) + c1_include
    elif ring_start in c2_include and ring_start - 1 not in c2_include and ring_start != 1:
        c2_segment = linear[:ring_start] + c2_segment
        c2_include = list(i + 1 for i in range(ring_start + 1)) + c2_include

    if ring_end in c2_include:
        c2_segment = c2_segment + linear[ring_end:]
        c2_include = c2_include + \
            list(i + 1 for i in range(ring_end, len(linear)))
    else:
        c1_segment = c1_segment + linear[ring_end:]
        c1_include = c1_include + \
            list(i + 1 for i in range(ring_end, len(linear)))

    return c1_segment, c1_include, c2_segment, c2_include


def slice_ring(linear, c1, c2, ring_start):
    c1_segment = linear[c1:c2]
    c1_include = [c['index'] for c in c1_segment]
    c2_segment = [linear[i]
                  for i in list(range(c2, len(linear))) + list(range(c1))
                  ]
    c2_include = [c['index'] for c in c2_segment]
    return c1_segment, c1_include, c2_segment, c2_include