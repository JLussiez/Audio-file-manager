from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from functools import wraps
import json
import os
from werkzeug.utils import secure_filename
from mutagen.mp3 import MP3
from datetime import timedelta
from pydub import AudioSegment
import tempfile

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_tres_securisee'  # À changer en production
app.config['UPLOAD_FOLDER'] = 'user_files'
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB max file size
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac'}

def load_users():
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            return config.get('users', [])
    except FileNotFoundError:
        return []

def save_users(users):
    with open('config.json', 'w') as f:
        json.dump({'users': users}, f, indent=4)

# Charger les utilisateurs au démarrage
AUTHORIZED_USERS = load_users()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_user_folder(username):
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    return user_folder

def get_mp3_duration(file_path):
    try:
        audio = MP3(file_path)
        duration = int(audio.info.length)
        return str(timedelta(seconds=duration))
    except:
        return "Durée inconnue"

def compress_audio(input_path, output_path, bitrate='128k'):
    try:
        # Déterminer le format d'entrée
        input_format = input_path.split('.')[-1].lower()
        
        # Charger le fichier audio selon son format
        if input_format == 'mp3':
            audio = AudioSegment.from_mp3(input_path)
        elif input_format == 'wav':
            audio = AudioSegment.from_wav(input_path)
        elif input_format == 'ogg':
            audio = AudioSegment.from_ogg(input_path)
        elif input_format == 'flac':
            audio = AudioSegment.from_file(input_path, format='flac')
        else:
            return {
                'success': False,
                'error': f'Format non supporté: {input_format}'
            }
        
        # Exporter en MP3 avec une qualité réduite
        audio.export(output_path, format='mp3', bitrate=bitrate)
        
        # Vérifier la taille du fichier compressé
        original_size = os.path.getsize(input_path)
        compressed_size = os.path.getsize(output_path)
        
        return {
            'success': True,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': (1 - compressed_size / original_size) * 100
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('files'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        
        if username in AUTHORIZED_USERS:
            session['username'] = username
            return redirect(url_for('files'))
        return render_template('login.html', error='Utilisateur non autorisé')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/files')
@login_required
def files():
    user_folder = get_user_folder(session['username'])
    files = []
    for filename in os.listdir(user_folder):
        if allowed_file(filename):
            file_path = os.path.join(user_folder, filename)
            files.append({
                'name': filename,
                'size': os.path.getsize(file_path),
                'type': filename.rsplit('.', 1)[1].lower(),
                'duration': get_mp3_duration(file_path)
            })
    return render_template('files.html', files=files, username=session['username'])

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        user_folder = get_user_folder(session['username'])
        
        # Créer un fichier temporaire pour le fichier original
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            file.save(temp_file.name)
            original_path = temp_file.name
        
        # Chemin pour le fichier compressé
        compressed_path = os.path.join(user_folder, filename)
        
        # Compresser le fichier
        compression_result = compress_audio(original_path, compressed_path)
        
        # Supprimer le fichier temporaire
        os.unlink(original_path)
        
        if compression_result['success']:
            return jsonify({
                'message': 'Fichier téléchargé et compressé avec succès',
                'duration': get_mp3_duration(compressed_path),
                'compression_info': {
                    'original_size': compression_result['original_size'],
                    'compressed_size': compression_result['compressed_size'],
                    'compression_ratio': round(compression_result['compression_ratio'], 2)
                }
            })
        else:
            return jsonify({'error': f'Erreur lors de la compression: {compression_result["error"]}'}), 500
    
    return jsonify({'error': 'Type de fichier non autorisé'}), 400

@app.route('/delete/<filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
    user_folder = get_user_folder(session['username'])
    file_path = os.path.join(user_folder, secure_filename(filename))
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'message': 'Fichier supprimé avec succès'})
    
    return jsonify({'error': 'Fichier non trouvé'}), 404

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    user_folder = get_user_folder(session['username'])
    return send_from_directory(user_folder, secure_filename(filename), as_attachment=True)

# Routes pour la gestion des utilisateurs
@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    return jsonify(AUTHORIZED_USERS)

@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({'error': 'Nom d\'utilisateur requis'}), 400
    
    if username in AUTHORIZED_USERS:
        return jsonify({'error': 'Utilisateur déjà existant'}), 400
    
    AUTHORIZED_USERS.append(username)
    save_users(AUTHORIZED_USERS)
    return jsonify({'message': 'Utilisateur créé avec succès'}), 201

@app.route('/api/users/<username>', methods=['DELETE'])
@login_required
def delete_user(username):
    if username not in AUTHORIZED_USERS:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    AUTHORIZED_USERS.remove(username)
    save_users(AUTHORIZED_USERS)
    return jsonify({'message': 'Utilisateur supprimé avec succès'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000) 