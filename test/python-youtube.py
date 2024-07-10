import logging as log
import os
from pytube import YouTube # Dev docs: https://pytube.io/en/latest/api.html#youtube-object

linkToYouTubeVideo = ""

def downloadYouTubeVideoViaLink():
	global linkToYouTubeVideo

	# linkToYouTubeVideo = input("Enter the YouTube video URL: ")

	try:
		youtubeObj = YouTube("https://youtu.be/5_xKLgaCwkM?si=4zbTw3OU90aL-yKY")
		youtubeObj = youtubeObj.streams.get_audio_only()
		log.debug("Starting to download")
		youtubeObj.download()
		log.debug("Finished the download")
	except OSError as err:
	    log.error(f"{err}")
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
	log.basicConfig(
        datefmt="%Y-%m-%d %H:%M:%S", 
        format='%(levelname)s;%(asctime)s;%(message)s', 
        level=log.DEBUG
    )

	setupFs()
	if downloadYouTubeVideoViaLink() :
		log.info("Downloaded completed successfully!")

    

    # https://www.youtube.com/watch?v=5_xKLgaCwkM