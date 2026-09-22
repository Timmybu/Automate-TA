# Util functions
def perror(*args, **kwargs):
	import sys
	return print(args, kwargs, file=sys.stdout)

def ask_for_continue(message, default='Y'):
	yes = 'y'
	no = 'n'

	if default.lower() == 'y':
		yes = 'Y'
	elif default.lower() == 'n':
		no = 'N'

	print(f"About to {message}")
	inp = input(f"Do you wish to continue? ({yes}/{no}): ")

	if len(inp) == 0:
		return default.lower() == yes.lower()
	if inp[0].lower() == yes.lower():
		return True
	elif inp[0].lower() == no.lower():
		return False

	raise Exception(f"Invalid input. Options are 'y' or 'n'.\nYour input: {inp[0]}")
