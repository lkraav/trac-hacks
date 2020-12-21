# -*- coding: utf-8 -*-

def cnv_text2list(refs_text):
    """ convert text to list
    >>> cnv_text2list(None)
    set([])
    >>> cnv_text2list("")
    set([])
    >>> cnv_text2list("1, 3")
    set([1, 3])
    """
    refs = set([])
    if refs_text:
        refs_seq = refs_text.replace(",", " ").split()
        try:
            refs = set([int(id_) for id_ in refs_seq])
        except ValueError:
            pass
    return refs

def cnv_list2text(refs):
    """ convert list to text
    >>> cnv_list2text(set([]))
    u''
    >>> cnv_list2text(set([3, 1]))
    u'1, 3'
    """
    return u", ".join(str(i) for i in sorted(refs))

def cnv_sorted_refs(orig_text, extra_refs):
    """
    >>> cnv_sorted_refs(u"", set([]))
    u''
    >>> cnv_sorted_refs(u"1", set([]))
    u'1'
    >>> cnv_sorted_refs(u"", set([3, 1]))
    u'1, 3'
    >>> cnv_sorted_refs(u"1, 5", set([3, 1]))
    u'1, 3, 5'
    >>> cnv_sorted_refs(u"2, 1, 5", set([3, 1, 2]))
    u'1, 2, 3, 5'
    """
    refs = cnv_text2list(orig_text)
    refs.update(extra_refs)
    return cnv_list2text(refs)

def get_diff_refs(old_text, new_text):
    """
    >>> get_diff_refs(u"", u"1")
    ('added', set([1]))
    >>> get_diff_refs(u"1", u"")
    ('removed', set([1]))
    >>> get_diff_refs(u"3, 5", u"2, 3, 5")
    ('added', set([2]))
    >>> get_diff_refs(u"2, 3, 5", u"3, 5")
    ('removed', set([2]))
    >>> get_diff_refs(u"2", u"2, 3, 5")
    ('added', set([3, 5]))
    >>> get_diff_refs(u"2, 3, 5", u"3")
    ('removed', set([2, 5]))
    >>> get_diff_refs(u"2, 3, 5", u"2,3,5")
    ('removed', set([]))
    """
    old = cnv_text2list(old_text)
    new = cnv_text2list(new_text)
    if len(old) < len(new):
        return 'added', new.difference(old)
    else:
        return 'removed', old.difference(new)
