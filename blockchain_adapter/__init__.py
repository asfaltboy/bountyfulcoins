import logging
import os
import unittest

import requests

logger = logging.getLogger('blockchain_adapter')


URL_BASE = 'https://blockchain.info'
URL_BALANCE = '{base}/q/addressbalance/{addr}'
CONFIRMATIONS_MIN = 6  # min recommended by blockchain docs


class BlockChainAdapter(object):
    """
    A simple wrapper around requests to query blockchain.info API.

    Currently supports getting a specified address balance
    """
    def __init__(self, *args, **kwargs):
        self.url_base = kwargs.get('URL_BASE', URL_BASE)
        self.url_balance = kwargs.get('URL_BALANCE', URL_BALANCE)

    def get_balance_url(self, addr):
        return self.url_balance.format(base=self.url_base, addr=addr)

    def get_balance(self, address):
        logger.debug('Entering get_balance')
        if 'TEST_BLOCKCHAIN_BALANCE' in os.environ:
            return float(os.environ['TEST_BLOCKCHAIN_BALANCE'])

        res = requests.get(self.get_balance_url(address), params={
            'confirmations': CONFIRMATIONS_MIN})
        if not res.ok:
            logger.error('Could not get balance, server returned: %s - %s',
                         res.status_code, res.content)
            return None
        return float(res.content)

blockchain = BlockChainAdapter()


class TestBlockChainAdapter(unittest.TestCase):
    good_address = '1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX'
    bad_address = 'NOT_REAL'

    def test_bad_address(self):
        res = blockchain.get_balance(self.bad_address)
        self.assertIsNone(res, "get_balance should have returned 'None'"
                          " for this address")

    def test_good_address(self):
        res = blockchain.get_balance(self.good_address)
        self.assertIsInstance(res, float, "get_balance should have returned"
                              " a float number fot this address")


if __name__ == '__main__':
    unittest.main()
