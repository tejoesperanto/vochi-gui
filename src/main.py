#!/usr/bin/env python3

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
QHBoxLayout, QLabel, QComboBox, QPushButton, QLineEdit, QSpinBox,
QPlainTextEdit, QMessageBox, QInputDialog, QAction)
from PyQt5 import QtCore
from collections import OrderedDict
import re
import sys
import os

from lib.ranked_pairs import RankedPairs
from lib.stv import STV
from lib.exceptions import InvalidTieBreakerException, InvalidBallotException, TooManyBlankBallotsException, TieBreakerNeededException

try:
	base_path = sys._MEIPASS
except Exception:
	base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

current_election_type = None
election_types = OrderedDict(sorted({ 'RP': 'Paroranga metodo', 'STV': 'Unuopa Transdonebla Voĉo' }.items(), key=lambda x: x[0]))

def change_election_type (index):
	global current_election_type
	current_election_type = list(election_types.items())[index][0]
	places_input.setReadOnly(current_election_type != 'STV')

def reset_form ():
	change_election_type(0)
	candidates_input.setText('')
	ignored_candidates_input.setText('')
	places_input.setValue(1)
	ballots_input.setPlainText('')

comma_regex = r'[^,\s]'
newline_regex = r'\r?\n'
space_regex = r'\s'
def run_election ():
	candidates = re.findall(comma_regex, candidates_input.text())
	ignored_candidates = re.findall(comma_regex, ignored_candidates_input.text())
	places = places_input.value()

	raw_ballots = ballots_input.toPlainText();
	ballots = re.split(newline_regex, raw_ballots.strip())
	ballots = map(lambda b: re.sub(space_regex, '', b), ballots)
	ballots = filter(lambda b: len(b), ballots)
	ballots = list(map(lambda b: '' if b == 'blanka' else b, ballots))

	ballots_input.setPlainText('Kaŝita')
	def unhide_ballots ():
		ballots_input.setPlainText(raw_ballots)

	results = None
	try:
		try:
			if current_election_type == 'RP':
				results = RankedPairs(candidates, ballots, ignored_candidates)
			elif current_election_type == 'STV':
				results = STV(places, candidates, ballots, ignored_candidates)
		except TieBreakerNeededException as e:
			tie_breaker_text  = 'La egalecrompanto mem enskribu sian balotilon ĉi-sube.'
			if current_election_type == 'RP':
				tie_breaker_text += '\nEkz. A>B>D>C'
			elif current_election_type == 'STV':
				tie_breaker_text += '\nEkz. ABDC'
			tie_breaker_text += '\nValidaj kandidatoj:\n%s' % (', '.join(candidates))
			tie_breaker, ok = QInputDialog.getText(window, 'Necesas egalecrompanto!', tie_breaker_text)

			if not ok:
				unhide_ballots()
				return
			if current_election_type == 'RP':
				results = RankedPairs(candidates, ballots, ignored_candidates, tie_breaker)
			elif current_election_type == 'STV':
				results = STV(places, candidates, ballots, ignored_candidates, tie_breaker)
	except (InvalidTieBreakerException, InvalidBallotException, TooManyBlankBallotsException) as e:
		error_modal = QMessageBox()

		if (isinstance(e, InvalidTieBreakerException)):
			error_title = 'Nevalida egalecrompa balotilo'
			error_text = 'La egalecrompa balotilo ne estis valida.'
			error_modal.setIcon(QMessageBox.Warning)
		elif isinstance(e, InvalidBallotException):
			error_title = 'Nevalida(j) balotilo(j)'
			error_text = 'Unu aŭ pluraj el la enmetitaj balotiloj ne estis valida(j).'
			error_modal.setIcon(QMessageBox.Warning)
		else:
			error_title = 'Tro da blankaj balotiloj'
			error_text = 'Rezulto: Sindetene (%d balotiloj el entute %d estis blankaj)' % (e.blank_ballots, e.num_ballots)

		error_modal.setWindowTitle(error_title)
		error_modal.setText(error_text)
		error_modal.buttonClicked.connect(unhide_ballots)
		error_modal.exec_()

	if not results:
		return

	results_text = '%d balotiloj kalkulitaj, %d blankaj' % (results['ballots'], results['blank_ballots'])
	if len(ignored_candidates):
		results_text += '\nIgnorataj kandidatoj: %s' % (', '.join(ignored_candidates))

	if current_election_type == 'RP':
		if len(results['disqualified_candidates']):
			results_text += '\nNeelektitaj laŭ §2.6: %s' % (', '.join(results['disqualified_candidates']))
		results_text += '<table border="1"><tr>'
		for th in ('Paro', 'Gajnanto'):
			results_text += '<th>%s</th>' % (th)
		results_text += '</tr>'
		results_text += '</table>'

	if current_election_type == 'RP':
		results_text += '\n\nVenkinto: %s' % (results['winner'])
	elif current_election_type == 'STV':
		results_text += '\n\nVenkintoj (laŭ ordo de elektiĝo): %s' % (', '.join(results['winners']))

	results_modal = QMessageBox()
	results_modal.setWindowTitle('Rezulto trovita')
	results_modal.setText(results_text)
	results_modal.buttonClicked.connect(unhide_ballots)
	results_modal.exec_()

app = QApplication(['TEJO Voĉo'])
main_window = QMainWindow()
window = QWidget()
main_window.setCentralWidget(window)

menu = main_window.menuBar()
menu_about = menu.addMenu('&Pri Voĉo')

def display_about ():
	with open(os.path.join(base_path, 'version.txt'), encoding='utf8') as f:
		version = f.read()

	text  =   'TEJO Voĉo estas la eksterreta voĉdonsistemo de TEJO'
	text += '\nVersio: G-%s\n' % (version)
	text += '\n© Mia Nordentoft 2019, MIT-permesilo'

	modal = QMessageBox()
	modal.setWindowTitle('Pri Voĉo')
	modal.setText(text)
	modal.exec_()

menu_about_about = QAction('&Pri Voĉo')
menu_about_about.setShortcut('F2')
menu_about_about.triggered.connect(display_about)
menu_about.addAction(menu_about_about)

def display_help ():
	with open(os.path.join(base_path, 'help.html'), encoding='utf8') as f:
		help_text = f.read()

	modal = QMessageBox()
	modal.setWindowTitle('Voĉo-helpo')
	modal.setText(help_text)
	modal.exec_()

menu_about_help = QAction('&Helpo')
menu_about_help.setShortcut('F1')
menu_about_help.triggered.connect(display_help)
menu_about.addAction(menu_about_help)

form = QVBoxLayout()
window.setLayout(form)

# Line 1
form_options_line1 = QHBoxLayout()
form.addLayout(form_options_line1)

# Election type picker
election_type_label = QLabel('Voĉdonsistemo:')
form_options_line1.addWidget(election_type_label)

election_type_picker = QComboBox()
form_options_line1.addWidget(election_type_picker)
election_type_picker.addItems(election_types.values())
election_type_picker.currentIndexChanged.connect(change_election_type)

# Calculate button
calculate_btn = QPushButton('Kalkuli')
form_options_line1.addWidget(calculate_btn)
calculate_btn.clicked.connect(run_election)

# Reset button
reset_btn = QPushButton('Nuligi')
form_options_line1.addWidget(reset_btn)
reset_btn.clicked.connect(reset_form)

# Line 2
form_options_line2 = QVBoxLayout()
form.addLayout(form_options_line2)

# Candidates input
candidates_label = QLabel('Voĉdonebloj: (unulitera, dividu per komo)')
form_options_line2.addWidget(candidates_label)

candidates_input = QLineEdit()
form_options_line2.addWidget(candidates_input)

# Line 3
form_options_line3 = QVBoxLayout()
form.addLayout(form_options_line3)

# Ignored candidates input
ignored_candidates_label = QLabel('Ignorataj kandidatoj: (unulitera, dividu per komo)')
form_options_line3.addWidget(ignored_candidates_label)

ignored_candidates_input = QLineEdit()
form_options_line3.addWidget(ignored_candidates_input)

# Line 4
form_options_line4 = QVBoxLayout()
form.addLayout(form_options_line4)

# Places input
places_label = QLabel('Kvanto de venkontoj: (nur por UTV)')
form_options_line4.addWidget(places_label)

places_input = QSpinBox()
form_options_line4.addWidget(places_input)
places_input.setMinimum(1)

# Line 5
form_options_line5 = QVBoxLayout()
form.addLayout(form_options_line5)

# Ballots input
ballots_label = QLabel('Balotiloj:')
form_options_line5.addWidget(ballots_label)

ballots_input = QPlainTextEdit()
form_options_line5.addWidget(ballots_input)
ballots_input.setMinimumSize(400, 500)

reset_form()

main_window.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.MSWindowsFixedSizeDialogHint)
main_window.show()
main_window.setFixedSize(main_window.size())
app.exec_()
