from lib.exceptions import InvalidTieBreakerException, InvalidBallotException, TooManyBlankBallotsException, TieBreakerNeededException
from lib.util import debug

# Ported from https://github.com/tejoesperanto/vocho-lib/blob/master/src/ranked-pairs.js
# https://hackernoon.com/the-javascript-developers-guide-to-graphs-and-detecting-cycles-in-them-96f4f619d563
def is_cyclic (graph):
	nodes = list(graph.keys())
	visited = {}
	rec_stack = {}

	def _is_cyclic (node, visited, rec_stack):
		if not node in visited or not visited[node]:
			visited[node] = True
			rec_stack[node] = True
			node_neighbors = graph[node]
			for current_node in node_neighbors:
				if ((not current_node in visited or not visited[current_node]) and _is_cyclic(current_node, visited, rec_stack) or
					current_node in rec_stack and rec_stack[current_node]):
					return True
		rec_stack[node] = False
		return False

	for node in nodes:
		if _is_cyclic(node, visited, rec_stack):
			return True

	return False

def RankedPairs (candidates, ballots, ignored_candidates = [], tie_breaker = None):
	candidates = list(candidates)
	candidates.sort()

	tie_breaker_list = []
	if tie_breaker:
		tie_breaker_list = tie_breaker.split('>')

		if len(set(tie_breaker_list)) != len(tie_breaker_list):
			raise InvalidTieBreakerException('The tie breaker ballot must not contain duplicate candidates')

		if len(tie_breaker_list) < len(candidates):
			raise InvalidTieBreakerException('The tie breaker ballot must contain all candidates')

		for cand in tie_breaker_list:
			if not cand in candidates:
				raise InvalidTieBreakerException('Invalid candidate %s in tie breaker' % (cand))

	# Create pairs
	pairs = {}
	for i, cand1 in enumerate(candidates):
		for cand2 in candidates[i + 1:]:
			pair_name = cand1 + cand2
			pair = pairs[pair_name] = {
				'diff': 0,
				'winner': None,
				'loser': None,
				cand1: 0,
				cand2: 0
			}

	# Tally
	blank_ballots = 0
	cand_stats = {}
	for cand in candidates:
		cand_stats[cand] = {
			'won': 0,
			'lost': 0,
			'mentions': 0
		}

	for ballot in ballots:
		already_mentioned = []

		rows = ballot.split('>')
		# Turn blank votes into an empty list
		rows = list(filter(lambda row: len(row), rows))
		rows = list(map(lambda row: row.split('='), rows))
		
		if not len(rows):
			blank_ballots += 1
			continue

		for y, cur_row in enumerate(rows):
			for cur_col in cur_row:
				if not cur_col in candidates:
					raise InvalidBallotException('Invalid candidate %s in ballot %s' % (cur_col, ballot))
				if cur_col in already_mentioned:
					raise InvalidBallotException('Duplicate candidate %s in ballot %s' % (cur_col, ballot))
				already_mentioned.append(cur_col)
				cand_stats[cur_col]['mentions'] += 1

		# Consider candidates not mentioned as lesser than those mentioned
		rows.append(list(set(candidates) - set(already_mentioned)))
		print(rows)

		for y, cur_row in enumerate(rows):
			for cur_col in cur_row:
				for lesser_row in rows[y + 1:]:
					for lesser_col in lesser_row:
						if not lesser_col in candidates:
							raise InvalidBallotException('Invalid candidate %s in ballot %s' % (cur_col, ballot))
						if lesser_col == cur_col:
							raise InvalidBallotException('Duplicate candidate %s in ballot %s' % (cur_col, ballot))
						pair_name = ''.join(sorted(( cur_col, lesser_col )))
						pairs[pair_name][cur_col] += 1

	# Check blank vote count
	debug('%d ballots cast (%d blank)' % (len(ballots), blank_ballots))
	if blank_ballots >= len(ballots) / 2:
		raise TooManyBlankBallotsException('Too many blank ballots', blank_ballots, len(ballots))

	# Disqualify candidates as needed
	disqualified_candidates = []
	for cand, stats in cand_stats.items():
		is_ignored = cand in ignored_candidates
		has_insufficient_mentions = stats['mentions'] < len(ballots) / 2

		if (is_ignored or has_insufficient_mentions):
			candidates.remove(cand)

			for pair_name in dict(pairs):
				cands = list(pair_name)
				if cand in cands:
					del pairs[pair_name]

		if is_ignored:
			debug('%s is ignored in this election' % (cand))
		elif has_insufficient_mentions:
			disqualified_candidates.append(cand)
			debug('%s is disqualified due to insufficient mentions' % (cand))

	# Determine the results of the compared pairs
	for pair_name, pair in pairs.items():
		cand1, cand2 = list(pair_name)
		pair['diff'] = pair[cand1] - pair[cand2]

		if pair[cand1] > pair[cand2]:
			cand_stats[cand1]['won'] += 1
			cand_stats[cand2]['lost'] += 1
			pair['winner'] = cand1
			pair['loser'] = cand2
		elif pair[cand2] > pair[cand1]:
			cand_stats[cand2]['won'] += 1
			cand_stats[cand1]['lost'] += 1
			pair['winner'] = cand2
			pair['loser'] = cand1
		else:
			if not tie_breaker:
				raise TieBreakerNeededException()

			cand1_index = tie_breaker_list.index(cand1)
			cand2_index = tie_breaker_list.index(cand2)

			if cand1_index < cand2_index:
				cand_stats[cand1]['won'] += 1
				cand_stats[cand2]['lost'] += 1
				pair['winner'] = cand1
				pair['loser'] = cand2
			else:
				cand_stats[cand2]['won'] += 1
				cand_stats[cand1]['lost'] += 1
				pair['winner'] = cand2
				pair['loser'] = cand1

	debug('\nCompared pairs:')
	debug(pairs)

	debug('\nCandidate pair scores:')
	debug(cand_stats)

	# Order the pairs
	ordered_entries = []
	entries = list(pairs.items())
	while len(entries):
		max_diff = -1
		max_diff_indices = None

		for i, pair in enumerate(entries):
			abs_diff = abs(pair[1]['diff'])
			if abs_diff > max_diff:
				max_diff = abs_diff
				max_diff_indices = [ i ]
			elif abs_diff == max_diff:
				max_diff_indices.append(i)

		if len(max_diff_indices) == 1:
			# No tie
			pair = entries[max_diff_indices[0]]
			ordered_entries.append(pair)
			entries.pop(max_diff_indices[0])
		else:
			# We have a tie, follow §2.10
			# Obtain the pairs, from the highest index to the lowest as to not mess up the indices when popping
			max_diff_indices.sort(reverse=True)
			equal_pairs = []
			for i in max_diff_indices:
				equal_pairs.append(entries[i])
				entries.pop(i)

			# 1. The equal pair with a loser that's already listed as a loser is put first
			loser_entries = [] # All losers that are already in the ordered pairs
			for i, equal_pair in enumerate(equal_pairs):
				# Find the loser of the equal pair
				equal_pair_loser = equal_pair[1]['loser']

				# Check if the loser is already in the ordered pairs as a loser
				ordered_index = None
				for n, ordered_entry in enumerate(ordered_entries):
					ordered_loser = ordered_entry[1]['loser']
					if equal_pair_loser == ordered_loser:
						ordered_index = n
						break
				if ordered_index is not None:
					loser_entries.append({ 'eq_i': i, 'or_i': ordered_index })
			loser_entries.sort(reverse=True, key = lambda x: x['or_i']) # Don't mess up indices when popping

			new_ordered_loser_entries = []
			for i, loser_entry in enumerate(loser_entries):
				next_loser_entry = None
				try:
					next_loser_entry = loser_entries[i + 1]
				except IndexError:
					pass
				if next_loser_entry is None or next_loser_entry['or_i'] > loser_entry['or_i']:
					new_ordered_loser_entries.append(loser_entry['eq_i'])
			new_ordered_loser_entries.sort(reverse=True) # Don't mess up indices when popping
			for i in new_ordered_loser_entries:
				ordered_entries.append(equal_pairs[i])
				equal_pairs.pop(i)

			# 2. The pair with a winner that's already listed as a winner is put first
			winner_entries = [] # All winners that are already in the ordered pairs
			for i, equal_pair in enumerate(equal_pairs):
				# Find the winner of the equal pair
				equal_pair_winner = equal_pair[1]['winner']

				# Check if the winner is already in the ordered pairs as a winner
				ordered_index = None
				for n, ordered_entry in enumerate(ordered_entries):
					ordered_winner = ordered_entry[1]['winner']
					if equal_pair_winner == ordered_winner:
						ordered_index = n
						break
				if ordered_index is not None:
					winner_entries.append({ 'eq_i': i, 'or_i': ordered_index })
			winner_entries.sort(reverse=True, key = lambda x: x['or_i']) # Don't mess up indices when popping

			new_ordered_winner_entries = []
			for i, winner_entry in enumerate(winner_entries):
				next_winner_entry = None
				try:
					next_winner_entry = winner_entries[i + 1]
				except IndexError:
					pass
				if next_winner_entry is None or next_winner_entry['or_i'] > winner_entry['or_i']:
					new_ordered_winner_entries.append(winner_entry['eq_i'])
			new_ordered_winner_entries.sort(reverse=True) # Don't mess up indices when popping
			for i in new_ordered_winner_entries:
				ordered_entries.append(equal_pairs[i])
				equal_pairs.pop(i)

			if len(equal_pairs) > 1:
				# 3. The pair with a loser that is least preferred by the tie breaker balllot is put first
				if not tie_breaker:
					raise TieBreakerNeededException()

				loser_pref_indices = []
				for i, equal_pair_entry in enumerate(equal_pairs):
					loser = equal_pair_entry[1]['loser']
					loser_pref_indices.append({ 'eq_i': i, 'or_i': tie_breaker_list.index(loser) })

				new_ordered_tie_breaker_pairs = []
				for i, pair in enumerate(loser_pref_indices):
					next_pair = None
					try:
						next_pair = loser_pref_indices[i + 1]
					except IndexError:
						pass
					if (next_pair is None or next_pair['or_i'] > pair['or_i']):
						new_ordered_tie_breaker_pairs.append(pair['eq_i'])
				new_ordered_tie_breaker_pairs.sort(reverse=True) # Don't mess up indices when popping
				for i in new_ordered_tie_breaker_pairs:
					ordered_entries.append(equal_pairs[i])
					equal_pairs.pop(i)

			# There should only be one pair remaining at this point
			ordered_entries.extend(equal_pairs)

	debug('\nRanked pairs')
	debug(ordered_entries)

	# Make a graph of the winning pairs
	lock = {}
	for cand in candidates:
		lock[cand] = []
	lock_entries = []
	debug('\nLock:')
	for entry in ordered_entries:
		pair = entry[1]

		lock[pair['winner']].append(pair['loser'])
		if is_cyclic(lock):
			lock[pair['winner']].remove(pair['loser'])
			continue
		lock_entries.append((pair['winner'], pair['loser']))

		debug('%s → %s' % (pair['winner'], pair['loser']))

	# Find the candidate at the root of graph (with nothing pointing to it)
	possible_winners = list(candidates)
	cands_pointed_to = set(item for sublist in lock.values() for item in sublist)
	for cand in cands_pointed_to:
		possible_winners.remove(cand)
	winner = possible_winners[0]

	debug('\nWinner: %s' % (winner))

	return {
		'ballots': len(ballots),
		'blank_ballots': blank_ballots,
		'winner': winner,
		'disqualified_candidates': disqualified_candidates,
		'comp_pairs': pairs,
		'ranked_pairs': ordered_entries,
		'cand_stats': cand_stats,
		'lock': lock_entries,
		'graph': lock
	}
