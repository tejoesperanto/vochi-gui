#!/usr/bin/env python3

from lib.stv import STV

ballots = [
	'ABC',
	'ABD',
	'DAB',
	'CBAD',
	'CA'
]

STV(3, 'ABCDE', ballots)
