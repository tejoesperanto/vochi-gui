#!/usr/bin/env python3

from lib.ranked_pairs import RankedPairs

ballots = []
for i in range(60):
	ballots.append('B>K>M>S')
for i in range(45):
	ballots.append('S>K>M>B')
for i in range(40):
	ballots.append('M>K>S>B')
for i in range(35):
	ballots.append('K>M>B>S')

RankedPairs('BKMS', ballots)
