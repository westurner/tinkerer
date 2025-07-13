
def _main(argv):
    from tinkerer.cmdline import main
    main(argv=argv)

import sys
print(('Starting tinkerer ...',), file=sys.stderr)
print(('sys.argv', sys.argv), file=sys.stderr)
_main(argv=sys.argv[1:])

# if __name__ == "main":
#     pass
