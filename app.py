from flask import Flask, render_template, Response, request
from imutils.video import VideoStream
import threading
import imutils
import time
import cv2
from pose_est import pose_det

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful when multiple browsers/tabs
# are viewing the stream)
outputFrame = None
lock = threading.Lock()
# initialize a flask object
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/opencam', methods = ['POST'])
def index2():
	answer = request.form['response']
	return render_template('index.html', ans = answer)

def camera():
	global vs, outputFrame, lock
	vs = VideoStream(src=1).start()
	time.sleep(2.0)
	# grab global references to the video stream, output frame, and
	# lock variables

	while True:
		# read the next frame from the video stream, resize it,
		frame = vs.read()
		frame = imutils.resize(frame, width=800)
		frame = pose_det(frame)

		# acquire the lock, set the output frame, and release the
		# lock
		with lock:
			outputFrame = frame.copy()

def generate():
	# grab global references to the output frame and lock variables
	global outputFrame, lock
	# loop over frames from the output stream
	while True:
		# wait until the lock is acquired
		with lock:
			# check if the output frame is available, otherwise skip
			# the iteration of the loop
			if outputFrame is None:
				continue
			# encode the frame in JPEG format
			(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
			# ensure the frame was successfully encoded
			if not flag:
				continue
		# yield the output frame in the byte format
		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
			bytearray(encodedImage) + b'\r\n')

@app.route("/video_feed")
def video_feed():
	# return the response generated along with the specific media
	# type (mime type)
	return Response(generate(),
		mimetype = "multipart/x-mixed-replace; boundary=frame")

if __name__ == '__main__':
	# construct the argument parser and parse command line arguments

	t = threading.Thread(target=camera)
	t.daemon = True
	t.start()
	# start the flask app
	app.run(debug=True,
		threaded=True, use_reloader=False)
# release the video stream pointer
vs.stop()