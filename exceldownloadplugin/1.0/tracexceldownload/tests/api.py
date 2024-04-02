# -*- coding: utf-8 -*-

import unittest

from ..api import _replace_invalid_chars


class ApiTestCase(unittest.TestCase):

    def test_replace_invalid_chars_ucs2(self):
        self._replace_invalid_chars(
            u'\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd'
            u'\ufffd\x09\x0a\ufffd\ufffd\x0d\ufffd\ufffd'
            u'\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd'
            u'\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd'
            u'\x20',
            u'\x00\x01\x02\x03\x04\x05\x06\x07'
            u'\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
            u'\x10\x11\x12\x13\x14\x15\x16\x17'
            u'\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'
            u'\x20')
        self._replace_invalid_chars(u'\x7e\ufffd\ufffd\ufffd\ufffd\x85',
                                    u'\x7e\x7f\x80\x83\x84\x85')
        self._replace_invalid_chars(u'\x85\ufffd\ufffd\ufffd\xa0',
                                    u'\x85\x86\x9e\x9f\xa0')
        self._replace_invalid_chars(u'\ufdcf\ufffd\ufffd\ufde0',
                                    u'\ufdcf\ufdd0\ufddf\ufde0')
        self._replace_invalid_chars(u'\ufffd\ufffd\ufffd\U00010000',
                                    u'\ufffd\ufffe\uffff\U00010000')

    def test_replace_invalid_chars_ucs4(self):
        self._replace_invalid_chars(
            u'\U0001fffd\ufffd\ufffd\U00020000',
            u'\U0001fffd\U0001fffe\U0001ffff\U00020000')
        self._replace_invalid_chars(
            u'\U0002fffd\ufffd\ufffd\U00030000',
            u'\U0002fffd\U0002fffe\U0002ffff\U00030000')
        self._replace_invalid_chars(
            u'\U0003fffd\ufffd\ufffd\U00040000',
            u'\U0003fffd\U0003fffe\U0003ffff\U00040000')
        self._replace_invalid_chars(
            u'\U0004fffd\ufffd\ufffd\U00050000',
            u'\U0004fffd\U0004fffe\U0004ffff\U00050000')
        self._replace_invalid_chars(
            u'\U0005fffd\ufffd\ufffd\U00060000',
            u'\U0005fffd\U0005fffe\U0005ffff\U00060000')
        self._replace_invalid_chars(
            u'\U0006fffd\ufffd\ufffd\U00070000',
            u'\U0006fffd\U0006fffe\U0006ffff\U00070000')
        self._replace_invalid_chars(
            u'\U0007fffd\ufffd\ufffd\U00080000',
            u'\U0007fffd\U0007fffe\U0007ffff\U00080000')
        self._replace_invalid_chars(
            u'\U0008fffd\ufffd\ufffd\U00090000',
            u'\U0008fffd\U0008fffe\U0008ffff\U00090000')
        self._replace_invalid_chars(
            u'\U0009fffd\ufffd\ufffd\U000a0000',
            u'\U0009fffd\U0009fffe\U0009ffff\U000a0000')
        self._replace_invalid_chars(
            u'\U000afffd\ufffd\ufffd\U000b0000',
            u'\U000afffd\U000afffe\U000affff\U000b0000')
        self._replace_invalid_chars(
            u'\U000bfffd\ufffd\ufffd\U000c0000',
            u'\U000bfffd\U000bfffe\U000bffff\U000c0000')
        self._replace_invalid_chars(
            u'\U000cfffd\ufffd\ufffd\U000d0000',
            u'\U000cfffd\U000cfffe\U000cffff\U000d0000')
        self._replace_invalid_chars(
            u'\U000dfffd\ufffd\ufffd\U000e0000',
            u'\U000dfffd\U000dfffe\U000dffff\U000e0000')
        self._replace_invalid_chars(
            u'\U000efffd\ufffd\ufffd\U000f0000',
            u'\U000efffd\U000efffe\U000effff\U000f0000')
        self._replace_invalid_chars(
            u'\U000ffffd\ufffd\ufffd\U00100000',
            u'\U000ffffd\U000ffffe\U000fffff\U00100000')
        self._replace_invalid_chars(
            u'\U0010fffd\ufffd\ufffd',
            u'\U0010fffd\U0010fffe\U0010ffff')

    def test_replace_invalid_chars_surrogates(self):
        self._replace_invalid_chars(u'\ufffd\ufffd\U0001f408\ufffd\ufffd',
                                    u'\udfff\udc00\U0001f408\ud800\udbff')

    def _replace_invalid_chars(self, result, value):
        self.assertEqual(result, _replace_invalid_chars(value))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ApiTestCase))
    return suite
