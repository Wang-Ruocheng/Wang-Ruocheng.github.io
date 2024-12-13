from flask import Flask, jsonify, send_from_directory
import os

app = Flask(__name__)

def get_images():
    gallery_path = 'gallery'
    categories = {}
    for category in os.listdir(gallery_path):
        category_path = os.path.join(gallery_path, category)
        if os.path.isdir(category_path):
            images = [os.path.join(category, img) for img in os.listdir(category_path) if img.endswith(('jpg', 'jpeg', 'png', 'gif'))]
            categories[category] = images
    return categories

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/gallery/<path:filename>')
def gallery(filename):
    return send_from_directory('gallery', filename)

@app.route('/api/gallery')
def api_gallery():
    categories = get_images()
    return jsonify(categories)

if __name__ == '__main__':
    app.run(debug=True)