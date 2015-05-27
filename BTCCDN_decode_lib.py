import binascii
import collections
import requests
import sys

VERSION = 0x00

API_KEY = 'af462d6b6a9814ebd17fcc53e7316afb'

COMMAND = {
	'MSG' : 16,
	'FILESTART' : 17,
	'FILETERM' : 18,
	'TERMACCT' : 1,
}

class LookupError(Exception):
	pass

class AddrTracker(object):
	global COMMAND
	def __init__(self, src, commands):
		self._s = src
		self._f = False
		self._n = ''
		self.files = self.get(commands)

	def get(self, commands):
		f = sorted(filter(lambda x: x['command'] & COMMAND['MSG'], commands), key = lambda x : x['payload'][0])

		files = {}
		c = -1
		txid = ''
		for pl in f:
			assert(c == -1 or c == pl['payload'][0])
			c = pl['payload'][0] + 1
			if pl['command'] & COMMAND['FILESTART'] == COMMAND['FILESTART']:
				txid = str(pl['txid'])
				files[txid] = {
					'global_pos' : pl['key'],
					'file' : bytearray(),
				}
			files[txid]['file'] += pl['payload'][1]
			if pl['command'] & COMMAND['FILETERM'] == COMMAND['FILETERM']:
				# end of file global pos
				files[txid]['global_pos'] = pl['key']
		return files

	@property
	def next(self):
		return self._n

	@property
	def src(self):
		return self._s

	@property
	def final(self):
		return self._f

class BTCCDNDownload(object):
	@staticmethod
	def get_name(txid):
		return 'files/%s.out' % txid

	def __init__(self, dest, txid=None, src=None):
		if txid is None:
			txid = []
		if src is None:
			src = []
		self._d = dest
		self._s = src
		self._t = txid
		self.sorted = None

	@property
	def txid(self):
		return self._t

	@property
	def dest(self):
		return self._d

	@property
	def src(self):
		return self._s

	@property
	def endpoint(self):
		global API_KEY
		return 'https://api.chain.com/v2/bitcoin/addresses/%s/op-returns?api-key-id=%s' % (self.dest, API_KEY)

	def parse(self, v):
		global VERSION, COMMAND
		b = bytearray.fromhex(v)
		version = b[0] >> 5
		command = b[0] & ((1 << 5) - 1)
		d = b[1:]
		payload = []
		if command & COMMAND['MSG']:
			payload = [ int(binascii.hexlify(d[0:4]), 16), d[4:] ]
		# NOTIMPLEMENTED
		# elif command & TERMACCT:
		#	payload = [ binascii.hexlify(d) ]
		else:
			return ( None, None, None )
		if VERSION != version:
			return ( None, None, None )
		
		return ( version, command, payload )

	def download(self):
		r = requests.get(self.endpoint)
		if r.status_code != 200:
			raise LookupError
		o = {}
		res = filter(lambda x: self.dest in x['receiver_addresses'], r.json())
		if self.src != []:
			res = filter(lambda x: len(set(x['sender_addresses'])) == 1 and set(x['sender_addresses']).intersection(self.src), res)
		clean = []
		for k, tx in enumerate(res):
			(version, command, payload) = self.parse(tx['hex'])
			if version is not None:
				clean.append({
					# global order
					'key' : len(res) - k,
					'src' : tx['sender_addresses'][0],
					'txid' : tx['transaction_hash'],
					'version' : version,
					'command' : command,
					'payload' : payload,
				})
		tracker = {}
		for tx in clean:
			if tx['src'] not in tracker:
				tracker[tx['src']] = []
			tracker[tx['src']].append(tx)
		downloads = [ AddrTracker(k, v) for k, v in tracker.items() ]
		files = {}
		for addr in downloads:
			for k, v in addr.files.items():
				files[k] = v
		sorted_files = []
		if self.txid != []:
			for x in set(self.txid).intersection(files):
				sorted_files.append(( x, files[x]))
		else:
			sorted_files = [ (x, y['file']) for x, y in sorted(files.items(), lambda (k1, v1), (k2, v2): cmp(v1['global_pos'], v2['global_pos'])) ]
		self.sorted = sorted_files
		return sorted_files

	def save(self):
		if self.sorted is None:
			self.download()
		for (k, v) in self.sorted:
			with open(BTCCDNDownload.get_name(k), 'wb') as fp:
				fp.write(v)
