# -*- coding: utf-8 -*-

import unittest


def _find_openpyxl_shutdown():
    try:
        import openpyxl
    except ImportError:
        return
    del openpyxl

    try:
        from openpyxl.writer.write_only import _openpyxl_shutdown
    except ImportError:
        pass
    else:
        return _openpyxl_shutdown

    try:
        from openpyxl.worksheet.write_only import _openpyxl_shutdown
    except ImportError:
        pass
    else:
        return _openpyxl_shutdown

    try:
        from openpyxl.worksheet._writer import _openpyxl_shutdown
    except ImportError:
        pass
    else:
        return _openpyxl_shutdown


_openpyxl_shutdown = _find_openpyxl_shutdown()
if _openpyxl_shutdown:
    import atexit
    if hasattr(atexit, 'unregister'):
        atexit.unregister(_openpyxl_shutdown)
    else:
        for idx, entry in enumerate(atexit._exithandlers):
            if entry[0] == _openpyxl_shutdown:
                del atexit._exithandlers[idx]
                break
        del idx, entry
        del atexit
del _find_openpyxl_shutdown, _openpyxl_shutdown


def suite():
    from . import api, ticket
    suite = unittest.TestSuite()
    for mod in (api, ticket):
        suite.addTest(mod.suite())
    return suite
