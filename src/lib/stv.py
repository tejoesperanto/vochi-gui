import sys
from functools import reduce

from lib.exceptions import InvalidTieBreakerException, InvalidBallotException, TooManyBlankBallotsException, TieBreakerNeededException
from lib.util import debug

# Ported from https://github.com/tejoesperanto/vocho-lib/blob/master/src/stv.js
def STV (places, candidates, ballots, ignored_candidates = [], tie_breaker = None):
	candidates = list(candidates)
	places = min(places, len(candidates)) # We can't elect a ghost

	# Validate the tie breaker
	if tie_breaker is not None:
		if len(set(tie_breaker)) != len(tie_breaker):
			raise InvalidTieBreakerException('Duplicate candidates in tie breaker')
		if len(tie_breaker) != len(candidates):
			raise InvalidTieBreakerException('Tie breaker vote must contain all candidates')
		for pref in tie_breaker:
			if not pref in candidates:
				raise InvalidTieBreakerException('Invalid candidate %s in tie breaker' % (pref))
		for cand in ignored_candidates:
			tie_breaker = tie_breaker.replace(cand, '')

	original_ballots = list(ballots)
	weighted_ballots = list(map(lambda b: { 'prefs': b, 'weight': 1 }, ballots))

	quota = len(ballots) / (places + 1) # Hagenbach-Bischoff

	blank_ballots = 0

	# Validate the ballots
	for i, ballot in enumerate(ballots):
		if not len(ballot):
			blank_ballots += 1
			continue

		already_mentioned = []
		for pref in ballot:
			if pref not in candidates:
				raise InvalidBallotException('Invalid candidate %s in ballot %s' % (pref, ballot))
			if pref in already_mentioned:
				raise InvalidBallotException('Duplicate candidate %s in ballot %s' % (pref, ballot))
			already_mentioned.append(pref)

		for cand in ignored_candidates:
			ballots[i] = ballot.replace(cand, '')

	for cand in ignored_candidates:
		candidates.remove(cand)

	# Check blank vote count
	debug('%d ballots cast (%d blank)' % (len(ballots), blank_ballots))
	if blank_ballots >= len(ballots) / 2:
		raise TooManyBlankBallotsException('Too many blank ballots', blank_ballots, len(ballots))

	debug('There are %d places and %d candidates' % (places, len(candidates)))
	debug('Election quota: %.3f' % (quota))

	elected_candidates = set()

	# Determine the amount of votes each candidate has based on everyone's first preference
	candidate_votes = {}
	for cand in candidates:
		candidate_votes[cand] = 0
	for ballot in ballots:
		try:
			first_pref = ballot[0]
			candidate_votes[first_pref] += 1
		except IndexError:
			pass

	rounds_stats = []
	stv_round = 0
	while len(elected_candidates) < places:
		debug('\nRound %d' % (stv_round + 1))
		stv_round += 1
		round_stat = {
			'elected': set(),
			'eliminated': None
		}
		rounds_stats.append(round_stat)

		debug('Valid candidates: %s' % (', '.join(candidates)))

		votes_debug = []
		exceeds_quota = []
		debug('Votes for each candidate:')
		for cand, votes in candidate_votes.items():
			votes_debug.append('%s: %s' % (cand, votes))
			if votes > quota:
				exceeds_quota.append(cand)
		debug(', '.join(votes_debug))
		elected_candidates.update(exceeds_quota)
		round_stat['elected'].update(exceeds_quota)

		debug('Ballots:')
		debug(weighted_ballots)

		# §3.7: Check if the amount of remaining candidates is equal to the amount of remaining places, and if so elect all remaining candidates
		if places - len(elected_candidates) == len(candidates):
			# Elect all remaining candidates
			elected_candidates.update(candidates)
			round_stat['elected'].update(candidates)
			debug('Elected all remaining candidates: %s' % (', '.join(candidates)))

		if len(exceeds_quota):
			debug('Elected candidates: %s' % (', '.join(exceeds_quota)))
		else:
			debug('No candidates elected')

		# Transfer surplus votes
		# Calculate the surplus transfer value using the Gregory method
		for cand in exceeds_quota:
			votes_received = candidate_votes[cand]

			# Find all ballots that listed the candidate as the first priority
			first_pref_ballots = []
			for ballot in weighted_ballots:
				try:
					if ballot['prefs'][0] == cand:
						first_pref_ballots.append(ballot)
				except IndexError:
					pass

			total_cand_vote_value = sum(map(lambda b: b['weight'], first_pref_ballots))
			transfer_value_factor = (total_cand_vote_value - quota) / total_cand_vote_value

			for ballot in first_pref_ballots:
				# Change the weight of each relevant ballot
				ballot['weight'] *= transfer_value_factor

			# Remove the elected candidate from the list of candidates
			candidates.remove(cand)
			del candidate_votes[cand]

			# Remove all mentions of the candidate from the ballots
			for ballot in weighted_ballots:
				ballot['prefs'] = ballot['prefs'].replace(cand, '')

			transfer_to = {}
			for ballot in first_pref_ballots:
				# Count the second priorities of all relevant ballots
				next_pref = None
				try:
					next_pref = ballot['prefs'][0]
				except IndexError:
					continue # Ignore the vote if there's no next priority

				if not next_pref in transfer_to:
					transfer_to[next_pref] = 1
				else:
					transfer_to[next_pref] += 1;

			# Transfer the votes
			for to, votes in transfer_to.items():
				new_votes = (votes_received - quota) / votes_received * votes;
				candidate_votes[to] += new_votes;

		if not len(exceeds_quota): # No candidate elected, time to eliminate someone
			# § 3.11, eliminate the candidate with the least votes
			min_votes = sys.maxsize
			min_votes_cands = None
			for cand, votes in candidate_votes.items():
				if votes < min_votes:
					min_votes = votes
					min_votes_cands = [ cand ]
				elif votes == min_votes:
					min_votes_cands.append(cand)

			eliminated_cand = None
			if len(min_votes_cands) == 1: # No tie
				eliminated_cand = min_votes_cands[0]
			else:
				# § 3.11 If multiple candidates have the same amount of votes, eliminate the one with the least first priorities
				# then second priorities etc. in the ORIGINAL ballots.
				# If there is still equality, a tie breaker is needed, whose least preferred of the relevant candidates is to be eliminated
				
				priority_num = -1
				while priority_num < len(candidates):
					priority_num += 1

					num_priorities = sys.maxsize
					num_priorities_cands = None
					for cand in min_votes_cands:
						# Find all ballots with the candidate at this priority level
						cand_num_priorities = 0
						for ballot in original_ballots:
							try:
								if ballot[priority_num] != cand:
									continue
							except IndexError:
								continue
							cand_num_priorities += 1
						if cand_num_priorities < num_priorities:
							num_priorities = cand_num_priorities
							num_priorities_cands = [ cand ]
						else:
							num_priorities_cands.append(cand)

				# Check if we've found a candidate to eliminate
				if len(min_votes_cands) == 1:
					eliminated_cand = min_votes_cands[0]
				else:
					# Nope, there's still equality. This calls for a tie breaker
					if not tie_breaker:
						raise TieBreakerNeededException()
					# The least preferred candidate according to the tie breaker is eliminated
					preferenceIndices = list(map(lambda cand: { 'cand': cand, 'index': tie_breaker.index(cand) },min_votes_cands))
					eliminated_cand = reduce(lambda a, b: a if a['index'] > b['index'] else b, preferenceIndices)['cand']

			# Transfer the votes of the eliminated candidate
			for ballot in weighted_ballots:
				# Find all ballots that have the eliminated candidate as their first priority
				try:
					if ballot['prefs'][0] != eliminated_cand:
						continue
				except IndexError:
					continue
				# Find their next preference (if there is one)
				next_pref = None
				try:
					next_pref = ballot['prefs'][1]
				except IndexError:
					continue
				candidate_votes[next_pref] += ballot['weight']

			# Remove eliminated candidates from the list of candidates
			candidates.remove(eliminated_cand)
			del candidate_votes[eliminated_cand]
			round_stat['eliminated'] = eliminated_cand

			# Remove all mentions of the candidate from the ballots
			for ballot in weighted_ballots:
				ballot['prefs'] = ballot['prefs'].replace(eliminated_cand, '')

			debug('Eliminated candidate: %s' % (eliminated_cand))

	debug('\n\nDone!\nElected: %s' % (', '.join(elected_candidates)))

	debug('Remaining ballots:')
	debug(weighted_ballots)

	return {
		'ballots': len(ballots),
		'blank_ballots': blank_ballots,
		'winners': elected_candidates,
		'rounds': rounds_stats,
		'quota': quota
	}
