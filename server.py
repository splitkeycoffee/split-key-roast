"""Run the server and begin hosting."""
import socket
import sys
from app import create_app, sio
from argparse import ArgumentParser


def main():
    """Go."""
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

    try:
        app.redis.setex('testasdf', 1, 42)
    except Exception as e:
        raise Exception("failed to contact redis", e)

    sio.run(app, host="0.0.0.0", port=80)


if __name__ == '__main__':
    main()
