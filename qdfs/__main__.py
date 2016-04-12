from qdfs.dn.blockstore import LocalFileStore
from qdfs.dn.server import DataNodeServer
from qdfs.peer.discovery import Peer
import logging
from tornado.log import enable_pretty_logging

def main():
    enable_pretty_logging()
    # TODO: Do some configuration stuff?
    def logger(event_type, **kwargs):
        logging.info('%s' % kwargs)
    peer = Peer(groups=['qdfs'], event_handler=logger)
    fs = LocalFileStore(root_dir='/tmp/qdfs')
    dn = DataNodeServer(fs, peer)
    logging.info('Starting QDFS')
    dn.start()

if __name__ == '__main__':
    main()
