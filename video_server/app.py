from flask import Flask, render_template, send_from_directory

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video/<path:filename>')
def video(filename):
    return send_from_directory('videos', filename)

@app.route('/hls/<path:filename>')
def hls(filename):
    return send_from_directory('hls', filename)

@app.route('/hls')
def hls_index():
    return render_template('hls.html')

@app.route('/dash/<path:filename>')
def dash(filename):
    return send_from_directory('dash', filename)

@app.route('/dash')
def dash_index():
    return render_template('dash.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
