import BTCCDN_decode_lib as cdnde

if __name__ == '__main__':
	# print cdnde.BTCCDNDownload('1AQmkM5K5RJ9vdGFtwXYQqdazCbB2pofbH').download()
	print cdnde.BTCCDNDownload('1AQmkM5K5RJ9vdGFtwXYQqdazCbB2pofbH', txid=['9e7d5b6c5634994bc7d23801debc6d5905c2c14c2d6339170e3283149e12555c']).download()
	# cdnde.BTCCDNDownload('1AQmkM5K5RJ9vdGFtwXYQqdazCbB2pofbH').save()
