#!/usr/bin/env python3echo ""

import argparse
import sys

import munger
import util

parser = argparse.ArgumentParser(description="Provocative text replacement with famous literature")
parser.add_argument(
    '--initialize', '-i', choices=['no', 'init', 'reinit'], default='no',
    help='Controls whether the database is assumed in a good state, initialized assuming empty state, or dropped then initialized')
parsed = parser.parse_args()

if parsed.initialize == 'init':
    init = util.InitializationOption.InitIfNone
elif parsed.initialize == 'reinit':
    init = util.InitializationOption.Reinitialize
else:
    init = util.InitializationOption.NoAction

sys.exit(munger.application(initialize=init))
