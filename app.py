from flask import Flask, send_from_directory, render_template
import os

app = Flask(__name__)

def generate_gallery_html():
    gallery_path = 'gallery'
    html_content = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gallery</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="section-heading col-12 mb-3 text-center">
                    <h1 class="mb-0">Gallery</h1>
                </div>
            </div>
            <div id="gallery-container" class="row">
    '''

    for category in os.listdir(gallery_path):
        category_path = os.path.join(gallery_path, category)
        if os.path.isdir(category_path):
            html_content += f'<div class="col-12 mb-3 text-center"><h2>{category}</h2></div>'
            for image in os.listdir(category_path):
                if image.endswith(('jpg', 'jpeg', 'png', 'gif')):
                    image_path = os.path.join(category, image)
                    html_content += f'''
                    <div class="col-lg-4 col-md-6 mb-4">
                        <div class="card">
                            <img src="/gallery/{image_path}" class="card-img-top" alt="{image}">
                            <div class="card-body">
                                <h5 class="card-title">{os.path.splitext(image)[0]}</h5>
                            </div>
                        </div>
                    </div>
                    '''

    html_content += '''
            </div>
        </div>
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    </body>
    </html>
    '''
    return html_content

@app.route('/')
def index():
    html_content = generate_gallery_html()
    with open('templates/gallery.html', 'w') as f:
        f.write(html_content)
    return render_template('gallery.html')

@app.route('/gallery/<path:filename>')
def gallery(filename):
    return send_from_directory('gallery', filename)

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    app.run(debug=True)