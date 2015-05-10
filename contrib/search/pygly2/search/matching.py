import re
import collections
from math import fabs
from itertools import chain
from functools import partial
from collections import defaultdict

from pygly2 import Composition

from pygly2.utils import make_struct
from pygly2.algorithms import database
from pygly2.search.spectra import IonMatchAnnotation


def get_intact_mass(record):
    try:
        return record.intact_mass
    except:
        return record.mass()


def get_score(record):
    try:
        return record.score
    except:
        try:
            return len(record.matches) / float(len(record.fragments))
        except:
            return 0.0


def get_match_count(record):
    try:
        return len(record.matches)
    except:
        return 0


def get_search_space_size(record):
    try:
        return len(record.fragments)
    except:
        return -1


def get_scan_count(record):
    try:
        return len(record.scan_ids)
    except:
        return 0


def get_charge_count(record):
    try:
        return len(record.charge_states)
    except:
        return 0


@database.column_data("score", "FLOAT", get_score)
@database.column_data("match_count", "FLOAT", get_match_count)
@database.column_data("scan_count", "FLOAT", get_scan_count)
@database.column_data("charge_count", "FLOAT", get_charge_count)
@database.column_data("search_space_size", "INTEGER", get_search_space_size)
class ResultsRecord(database.GlycanRecord):

    def __init__(self, *args, **kwargs):
        super(ResultsRecord, self).__init__(*args, **kwargs)
        self.report_data = kwargs.get("report_data", {})

    @classmethod
    def from_base(cls, record):
        instance = cls(record.structure)
        for name in dir(record):
            if "_" == name[0] or isinstance(getattr(record, name), collections.Callable):
                continue
            try:
                setattr(instance, name, getattr(record, name))
            except:
                pass
        instance.intact_mass = get_intact_mass(record)
        instance.score = get_score(record)
        return instance

    match_count = property(get_match_count)
    search_space_size = property(get_search_space_size)
    scan_count = property(get_scan_count)
    charge_count = property(get_charge_count)


ResultsDatabase = partial(database.RecordDatabase, record_type=ResultsRecord)


def _machine_epsilon(func=float):
    machine_epsilon = func(1)
    while func(1)+func(machine_epsilon) != func(1):
        machine_epsilon_last = machine_epsilon
        machine_epsilon = func(machine_epsilon) / func(2)
    return machine_epsilon_last


crossring_pattern = re.compile(r"\d,\d")

PROTON = Composition("H+").mass
DEFAULT_MS2_MATCH_TOLERANCE = 2e-5
DEFAULT_MS1_MATCH_TOLERANCE = 1e-5
MACHINE_EPSILON = _machine_epsilon()


FragmentMatch = make_struct("FragmentMatch", ["match_key", "mass", "ppm_error",
                                              "intensity", "charge", "peak_id"])
MergedMatch = make_struct("MergedMatch", ["match_key", "mass", "ppm_error", "intensity",
                                          "charge", "peak_id", "matches"])
MassShift = make_struct("MassShift", ["name", "mass"])
NoShift = MassShift("", 0.0)


def split_match_key(match_key):
    key, shift = match_key.split(":")
    return key, shift


def strip_shift_label(match_key):
    return match_key.split(":")[0]


def neutral_mass(mz, z):
    return (mz * z) - (z * PROTON)


def mass_charge_ratio(neutral_mass, z):
    return (neutral_mass + (z * PROTON)) / z


def ppm_error(x, y):
    return (x - y) / y


def collect_similar_ions(fragments, tolerance=2e-8, redundant=True):
    '''
    Find clusters of close mass fragments.
    '''
    groups = defaultdict(list)
    membership = dict()
    for index in fragments:
        for other in fragments:
            if other.name in membership and not redundant:
                continue
            if fabs(ppm_error(index.mass, other.mass)) < tolerance:
                groups[index.name].append(other)
                membership[other.name] = index.name
    return groups


def find_matches(precursor, msms_db, shifts=None,
                 ms1_match_tolerance=DEFAULT_MS1_MATCH_TOLERANCE,
                 ms2_match_tolerance=DEFAULT_MS2_MATCH_TOLERANCE,
                 ion_types=('A', 'B', 'C', 'X', 'Y', 'Z'),
                 spectrum_matches=None):
    '''Find all MS1 matches, find all MS2 matches in these matches, and merge the fragments found.

    Parameters
    ----------
    precursor: GlycanRecord
        Precursor Glycan to search for
    msms_db : MSMSSqlDB
        The observed MS and MSMS Spectra
    shifts : list of MassShift, optional
        List of mass shifts to apply to each mass searched, defaults to :const:`NoShift`
    ms1_match_tolerance : float, optional
        PPM matching tolerance for MS1 search. Defaults to :const:`DEFAULT_MS1_MATCH_TOLERANCE`
    ms2_match_tolerance : float, optional
        PPM matching tolerance for MS2 search. Defaults to :const:`DEFAULT_MS2_MATCH_TOLERANCE`
    ion_types : iterable, optional
        Iterable of ion types to search for. Defaults to ('A', 'B', 'C', 'X', 'Y', 'Z')

    Returns
    -------
    precursor: GlycanRecord
        precursor is modified to contain new attributes
            - charge_states
            - ppm_error
            - scan_ids
            - intact_structures_searched
            - scan_density
            - matches
            - score
    '''
    shifts = shifts or [NoShift]
    results = []
    precursor_ppm_errors = []
    precursor_charge_state = []
    scans_searched = set()
    if spectrum_matches is None:
        spectrum_matches = []
    i = 0
    ion_types = map(''.join, map(sorted, ion_types))
    precursor.fragments = [f for f in precursor.fragments
                           if ''.join(sorted(crossring_pattern.sub("", f.kind))) in (ion_types)]
    for shift in shifts:
        for row in msms_db.ppm_match_tolerance_search(precursor.intact_mass + shift.mass, ms1_match_tolerance):
            spectrum = msms_db.precursor_type.from_sql(row, msms_db)
            precursor_ppm_errors.append(ppm_error(precursor.mass() + shift.mass, spectrum.neutral_mass))
            precursor_charge_state.append(spectrum.charge)
            scans_searched.update(spectrum.scan_ids)
            matches = match_fragments(precursor, spectrum,
                                      shifts=shifts,
                                      ms2_match_tolerance=ms2_match_tolerance,
                                      spectrum_matches=spectrum_matches)
            results.append(matches)
            i += 1

    precursor.charge_states = precursor_charge_state
    precursor.ppm_error = precursor_ppm_errors
    precursor.scan_ids = scans_searched
    precursor.intact_structures_searched = i

    precursor.scan_density = scan_density(precursor)
    precursor.matches = collect_matches(chain.from_iterable(results))
    precursor.score = simple_score(precursor)
    return precursor, spectrum_matches


def match_fragments(precursor, precursor_spectrum, shifts=None,
                    ms2_match_tolerance=DEFAULT_MS2_MATCH_TOLERANCE,
                    spectrum_matches=None):
    '''
    Match theoretical MS2 fragments against the observed peaks.
    '''
    if spectrum_matches is None:
        spectrum_matches = []
    peak_list = precursor_spectrum.tandem_data
    shifts = shifts or [NoShift]
    matches = []
    for shift in shifts:
        for fragment in precursor.fragments:
            for peak in peak_list:
                match_error = fabs(ppm_error(fragment.mass + shift.mass, peak.mass))
                if match_error <= ms2_match_tolerance:
                    matches.append(FragmentMatch(
                        fragment.name + ":" + shift.name, peak.mass,
                        match_error, peak.intensity, peak.charge, peak.id))
                    spectrum_matches.append(IonMatchAnnotation(peak.id, precursor.id,
                                                                    fragment.name + ":" + shift.name))
    return matches


def collect_matches(matches):
    '''
    Groups matches to the same theoretical ions into lists, and calls :func:`merge_matches`
    on each group
    '''
    acc = defaultdict(list)
    for match in matches:
        acc[match.match_key].append(match)
    return map(merge_matches, acc.values())


def merge_matches(matches):
    '''
    Merge a list of :class:`FragmentMatch` instances into a single :class:`MergedMatch`
    '''
    best_ppm = float('inf')
    best_match = None
    match_map = {}
    for match in matches:
        if fabs(match.ppm_error) < fabs(best_ppm):
            best_ppm = match.ppm_error
            best_match = match
        match_map[match.peak_id] = match
    merged = MergedMatch(best_match.match_key, best_match.mass, best_match.ppm_error,
                         best_match.intensity, best_match.charge,
                         best_match.peak_id, match_map)
    return merged


def collect_matched_scans(matches, msms_db):
    '''
    Count the number of scans matched and the number of scans not matched in the data

    Parameters
    ----------
    matches: iterable of GlycanRecord
        Search Results
    masms_db: spectra.MSMSSqlDB
        Observed Data
    '''
    scan_ids = tuple({scan_id for match in matches for scan_id in match.scan_ids})
    scans_not_matched = map(dict, msms_db.execute("select scan_id from Scans where scan_id not in {}".format(scan_ids)))
    return scan_ids, scans_not_matched


def simple_score(record):
    total_mass = record.mass()
    for fragment in record.fragments:
        fragment.score = fragment.mass / total_mass
    total_score = sum(fragment.score for fragment in record.fragments)

    for fragment in record.fragments:
        fragment.score /= total_score

    fmap = {f.name: f for f in record.fragments}

    score = 0
    observed = set()
    for match in record.matches:
        key = strip_shift_label(match.match_key)
        if key in observed:
            continue
        observed.add(key)
        score += fmap[key].score
    return score


def scan_density(record):
    scan_range = record.scan_ids
    if len(scan_range) == 0:
        return 0.
    min_scan = min(scan_range)
    max_scan = max(scan_range)
    total_scans = len(scan_range)
    try:
        scan_density = total_scans / (float(max_scan - min_scan))
    except ZeroDivisionError:
        scan_density = 0.
    return scan_density
