"""Run the server and begin hosting."""

from app import create_app, sio
from argparse import ArgumentParser

parser = ArgumentParser()
subs = parser.add_subparsers(dest='cmd')
setup_parser = subs.add_parser('run')
setup_parser.add_argument('--debug', action='store_true',
                          help='Run in debug mode.')
setup_parser.add_argument('--simulate', action='store_true',
                          help='Run in simulation mode.')
args = parser.parse_args()
kwargs = {'simulate': args.simulate, 'debug': args.debug}
app = create_app(**kwargs)

if __name__ == '__main__':
    sio.run(app, host="0.0.0.0", port=80)
