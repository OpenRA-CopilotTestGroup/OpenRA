from flask import Flask, Response, render_template_string
import os

app = Flask(__name__)
PIPE_PATH = './stream.ts'

@app.route('/')
def index():
    return render_template_string('''
    <html>
    <body style="margin:0">
        <video src="/stream" width="100%" autoplay muted playsinline></video>
    </body>
    </html>
    ''')

@app.route('/stream')
def stream():
    def generate():
        with open(PIPE_PATH, 'rb') as pipe:
            while True:
                data = pipe.read(1024)
                if not data:
                    continue
                yield data
    return Response(generate(), mimetype='video/mp2t')

if __name__ == '__main__':
    if not os.path.exists(PIPE_PATH):
        os.mkfifo(PIPE_PATH)
    app.run(host='0.0.0.0', port=8090, threaded=True)