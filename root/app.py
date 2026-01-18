from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import threading
from core.input.workflowInput import run
from core.output.workflowOutput import run_output

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp',
                     'xls', 'xlsx', 'csv', 'doc', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Track workflow state
workflow_thread_running = False

@app.route('/')
def chat():
    return render_template('chat.html')

@app.route('/uploadfile')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global workflow_thread_running

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Background workflow thread
        def background_job():
            global workflow_thread_running
            try:
                workflow_thread_running = True
                print("[WORKFLOW] Started.")
                run()  # Your heavy processing function
                print("[WORKFLOW] Finished.")
            finally:
                workflow_thread_running = False

        # Run in background only if not already running
        if not workflow_thread_running:
            threading.Thread(target=background_job, daemon=True).start()
        else:
            print("[WORKFLOW] Already running.")

        # Return immediately (loader will poll until done)
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'size': os.path.getsize(filepath)
        }), 200

    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/workflow_status')
def workflow_status():
    """Polled by frontend to check if run() is still running."""
    global workflow_thread_running
    return jsonify({'running': workflow_thread_running})

#----- Output section

memory = []

@app.route('/reset', methods=['GET'])
def reset():
    global memory
    memory = []
    print("Memory is :- ",memory)
    print("Memory reset to 0 due to browser reload.")
    return jsonify({'message': 'Memory reset', 'memory': memory})


@app.route('/process', methods=['GET'])
def process():
    # Receive textarea value
    message = request.args.get('message', '')
    print("COMING QUERY IS :- ", message)

    global memory 
    memory_len = len(memory)

    output, result=run_output(message, memory)

    try:
        update_memory = str(output+"------"+result)
        memory.append(update_memory)
        if memory_len<len(memory):
            print("MEMORY IS UPDATED :-",len(memory))
    except Exception as e:
        print("GETTING SOME ISSUE IN MEMORY UPDATION :- ",e)


    return jsonify({'received': output})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
