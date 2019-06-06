#!/usr/bin/env python3

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
QLabel, QComboBox, QPushButton, QLineEdit, QSpinBox, QPlainTextEdit)
from PyQt5 import QtCore

current_election_type = 'RP'
election_types = { 'RP': 'Paroranga metodo', 'STV': 'Unuopa Transdonebla Voĉo' }

def main ():
	app = QApplication(['TEJO Voĉo'])
	window = QWidget()

	form = QVBoxLayout()
	window.setLayout(form)

	# Line 1
	form_options_line1 = QHBoxLayout()
	form.addLayout(form_options_line1)

	election_type_label = QLabel('Voĉdonsistemo:')
	form_options_line1.addWidget(election_type_label)
	election_type_picker = QComboBox()
	election_type_picker.addItems(election_types.values())
	form_options_line1.addWidget(election_type_picker)

	calculate_btn = QPushButton('Kalkuli')
	form_options_line1.addWidget(calculate_btn)

	reset_btn = QPushButton('Nuligi')
	form_options_line1.addWidget(reset_btn)

	# Line 2
	form_options_line2 = QVBoxLayout()
	form.addLayout(form_options_line2)

	candidates_label = QLabel('Voĉdonebloj: (unulitera, dividu per komo)')
	form_options_line2.addWidget(candidates_label)

	candidates_input = QLineEdit()
	form_options_line2.addWidget(candidates_input)

	# Line 3
	form_options_line3 = QVBoxLayout()
	form.addLayout(form_options_line3)

	ignored_candidates_label = QLabel('Ignorataj kandidatoj: (unulitera, dividu per komo)')
	form_options_line3.addWidget(ignored_candidates_label)

	ignored_candidates_input = QLineEdit()
	form_options_line3.addWidget(ignored_candidates_input)

	# Line 4
	form_options_line4 = QVBoxLayout()
	form.addLayout(form_options_line4)

	places_label = QLabel('Kvanto de venkontoj: (nur por UTV)')
	form_options_line4.addWidget(places_label)

	places_input = QSpinBox()
	form_options_line4.addWidget(places_input)
	places_input.setValue(1)
	places_input.setMinimum(1)

	# Line 5
	form_options_line5 = QVBoxLayout()
	form.addLayout(form_options_line5)

	ballots_label = QLabel('Balotiloj:')
	form_options_line5.addWidget(ballots_label)

	ballots_input = QPlainTextEdit()
	form_options_line5.addWidget(ballots_input)
	ballots_input.setMinimumSize(400, 500)

	window.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.MSWindowsFixedSizeDialogHint)

	window.show()
	window.setFixedSize(window.size())
	app.exec_()

main()
