#!/usr/bin/env python3
import urllib.parse
import urllib.request
import urllib.error
import os.path
import time
import sys
import re

#############################################################################################################################################
#
#	Project goals:
#		Phase 1:
#			create a script to deduplicate the tab-delimited list of FDA-approved drugs "Products.txt", generating
#			a de-duplicated list of all the active ingredients in FDA-approved drugs by name.
#		Phase 2:
#			using the above list, auto-query the PubChem database and scrape canonical SMILES for all of the items in the above list,
#			thereby generating a new list of SMILES strings for all approved drugs.
#
#		Phase 3 (non-python):
#			use OpenBabel to generate a list of MDL files from the SMILES strings above, then convert those MDL files to PNGs
#			and have a (literal) look at them
#
#		Phase 4 (back in python):
#			create statistics from the SMILES list. Think MW, number of heterocycles, most common heterocycles, etc.
#
############################################################################################################################################

def print_usage():

	print("Usage:	drugs.py index_file \n")
	print("	index_file	A tab-delimited file containing a single row of headers followed by rows in which an API is listed in the 7th column")
	return None

def extract_smiles_from_pubchem_response(response):
	smiles_string = response.decode()
	smiles_string_list = smiles_string.split()
	return smiles_string_list

def get_smiles_from_name(name):
	smiles = None
	print("Getting SMILES for " + name)

	url = r"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/" + urllib.parse.quote(name) + r"/property/CanonicalSMILES/TXT"

	try:
		query_result = urllib.request.urlopen(url)
		text = query_result.read()
		smiles = extract_smiles_from_pubchem_response(text)

	except urllib.error.HTTPError:
		print("URL Error exception detected and handled.")

	return smiles

############################################################################################################################################
# BEGIN MAIN CODE
############################################################################################################################################

if len(sys.argv) < 3:
	print_usage()
	exit()

f = open("./" + sys.argv[1])
input_file = f.read()
f.close()

input_file_line_by_line = input_file.splitlines()

print("Parsing "+ str(len(input_file_line_by_line)) + " lines...")

active_ingredients_string = ""

for line in input_file_line_by_line:
	m = re.search(r"(.*\x09)(.*\x09)(.*\x09)(.*\x09)(.*\x09)(.*\x09)", line)	# API should be in group 6

	if m and m.group(6):								# NOTE: silently fails if a line doesn't conform to expectations
		active_ingredients = m.group(6)
		active_ingredients = active_ingredients.rstrip()			# Remove trailing tab
		active_ingredients = active_ingredients + ";"				# Add final semicolon
		active_ingredients_string = active_ingredients_string + active_ingredients

active_ingredients_list = active_ingredients_string.split(";")
active_ingredients_list.pop(0)								# Remove the first item in the list (it should be a column header)
non_redundant_active_ingredients_list = list(set(active_ingredients_list))

final_list_of_names = []

for entry in non_redundant_active_ingredients_list:					# Remove parentheses and leading whitespace....
	if entry != '':
		fixed_entry = entry.replace(r"(", "")
		fixed_entry = fixed_entry.replace(r")", "")
		final_list_of_names.append(fixed_entry.lstrip())

final_list_of_names = list(set(final_list_of_names))					# Perform a final de-duplication

print("Non-redundant list length: " + str(len(final_list_of_names)))

with open(sys.argv[2], 'a') as f_out:
	for i, api_name in enumerate(final_list_of_names):
		smiles_list = get_smiles_from_name(api_name)

		if smiles_list:
			deduplicated_smiles_list = list(set(smiles_list))		# de-duplicate the returned list of SMILES strings since, for some reason, often redundant
			for smiles_line in deduplicated_smiles_list:
				f_out.write(smiles_line + "," + api_name + "\n")

		if i % 5 == 0:
			time.sleep(1)

if not f_out.closed:
	f_out.close()

exit()
