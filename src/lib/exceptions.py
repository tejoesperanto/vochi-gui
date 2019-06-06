class InvalidTieBreakerException (Exception):
	pass

class InvalidBallotException (Exception):
	pass

class TooManyBlankBallotsException (Exception):
	def __init__ (self, message, blank_ballots, num_ballots):
		super().__init__(message)

		self.blank_ballots = blank_ballots
		self.num_ballots = num_ballots

class TieBreakerNeededException (Exception):
	pass
