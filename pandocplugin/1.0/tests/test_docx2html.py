# vim: set fileencoding=utf-8 :

import unittest
from tracpandoc.any2html import Docx2Html

class TestDocx2Html(unittest.TestCase):
    def test_render(self):
        sut = Docx2Html()
        if not sut.is_available():
            self.skipTest("This installation of pandoc does not support docx")
        with open("tests/fixture.docx") as f:
            actual = sut.render(f)
            expected = u"""<h1 id="見出し1">見出し1</h1>
<h2 id="見出し2">見出し2</h2>
<p>表 1</p>
<table>
<thead>
<tr class="header">
<th>No.</th>
<th>列A</th>
<th>列B</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>1</td>
<td>あ</td>
<td>い</td>
</tr>
<tr class="even">
<td>2</td>
<td>う</td>
<td>え</td>
</tr>
</tbody>
</table>
"""
            self.assertEqual(actual, expected)
