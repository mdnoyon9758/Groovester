import logging as log
import os
from pytube import YouTube as yt # Dev docs: https://pypi.org/project/python-youtube/

linkToYouTubeVideo = ""

def downloadYouTubeVideoViaLink():
	global linkToYouTubeVideo

	linkToYouTubeVideo = input("Enter the YouTube video URL: ")
	log.debug("YouTube video URL" + linkToYouTubeVideo)

	youtubeObj = yt(linkToYouTubeVideo)
	youtubeObj = youtubeObj.streams.get_highest_resolution()

	try:
	    youtubeObj.download()
	except:
	    log.error("An error has occurred with downloading the YouTube video")
	    return False

	return True

def setupFs() :
	if not os.path.exists("/home/jbone/youtube/") :
		try :
			os.mkdir("/home/jbone/youtube/")
		except OSError as err :
		    log.error(err)    

	if not os.path.exists("/home/jbone/youtube/downloads/") : 
		try :
			os.mkdir("/home/jbone/youtube/downloads/")
		except OSError as err :
		    log.error(err)   

	os.chdir("/home/jbone/youtube/downloads/")

if __name__ == "__main__" :
	log.basicConfig(format='%(levelname)s:%(message)s', level=log.DEBUG)

	setupFs()
	if downloadYouTubeVideoViaLink() :
		log.info("Downloaded completed successfully!")

    