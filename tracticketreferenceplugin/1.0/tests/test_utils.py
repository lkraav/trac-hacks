# -*- coding: utf-8 -*-
import pytest

from ticketref import utils


@pytest.mark.parametrize(("refs_text", "expected"), [
    (None, set([])),
    ("", set([])),
    (", ", set([])),
    ("1", set([1])),
    ("1, 3", set([1, 3])),
    ("  1,3,   5", set([1, 3, 5])),
    (",  1,3,", set([1, 3])),
    ("1 3", set([1, 3])),
    ("  1 3    5", set([1, 3, 5])),
    (",  1 3 ", set([1, 3])),
    ("#1 3", set([])),
    ("1 a", set([])),
])
def test_cnv_text2list(refs_text, expected):
    assert expected == utils.cnv_text2list(refs_text)


@pytest.mark.parametrize(("refs", "expected"), [
    (set([]), u''),
    (set([1]), u'1'),
    (set([3, 1]), u'1, 3'),
])
def test_cnv_list2text(refs, expected):
    assert expected == utils.cnv_list2text(refs)


@pytest.mark.parametrize(("orig_text", "extra_refs", "expected"), [
    (u"", set([]), u''),
    (u"1", set([]), u'1'),
    (u"", set([3, 1]), u'1, 3'),
    (u"1, 5", set([3, 1]), u'1, 3, 5'),
    (u"2, 1, 5", set([3, 1, 2]), u'1, 2, 3, 5'),
])
def test_cnv_sorted_refs(orig_text, extra_refs, expected):
    assert expected == utils.cnv_sorted_refs(orig_text, extra_refs)
