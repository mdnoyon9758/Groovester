from validators import ValidationError, url

url_ = "youtube.com"

if url(url_) :
	print(True)
else :
	print(False)