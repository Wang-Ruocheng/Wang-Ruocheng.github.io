import os

def generate_gallery_html():
    gallery_path = 'gallery'
    categories_order = ['Family', 'Travel', 'Food']
    html_content = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gallery</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            body {
                background-color: transparent; /* 设置背景颜色为透明 */
            }
            .gallery-container {
                column-count: 4; /* 设置列数 */
                column-gap: 10px; /* 列间距 */
            }
            .gallery-item {
                display: inline-block;
                width: 100%;
                margin-bottom: 10px;
            }
            .gallery-item img {
                width: 100%;
                height: auto;
                display: block;
            }
            .card-title {
                text-align: center; /* 图片标题居中 */
            }
            .category-title {
               
                column-span: all;
                text-align: center;
                margin: 20px 0;
                font-size: 1.5em;
                font-weight: bold;
            }
            .card {
                border: none; /* 移除卡片边框 */
            }
            .dark-theme .card {
                background-color: #333;
                color: #fff;
            }
            .light-theme .card {
                background-color: #fff;
                color: #000;
            }
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="section-heading col-12 mb-3 text-center">
                </div>
            </div>
            <div class="gallery-container">
    '''

    for category in categories_order:
        category_path = os.path.join(gallery_path, category)
        if os.path.isdir(category_path):
            html_content += '<div class="category-title"></div>'
            for image in os.listdir(category_path):
                if image.endswith(('jpg', 'jpeg', 'png', 'gif')):
                    image_path = os.path.join(category, image)
                    html_content += f'''
                    <div class="gallery-item">
                        <div class="card" style="{'border: none;' if category == 'Food' else ''}">
                            <img src="/gallery/{image_path}" class="card-img-top" alt="{image}">
                    '''
                    if category != 'Food':
                        html_content += f'''
                            <div class="card-body">
                                <h5 class="card-title">{os.path.splitext(image)[0]}</h5>
                            </div>
                        '''
                    html_content += '''
                        </div>
                    </div>
                    '''

    html_content += '''
            </div>
        </div>
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const theme = localStorage.getItem('theme') || 'light';
                document.body.classList.add(theme + '-theme');

                document.querySelectorAll('.js-set-theme-light').forEach(el => {
                    el.addEventListener('click', () => {
                        document.body.classList.remove('dark-theme', 'auto-theme');
                        document.body.classList.add('light-theme');
                        localStorage.setItem('theme', 'light');
                    });
                });

                document.querySelectorAll('.js-set-theme-dark').forEach(el => {
                    el.addEventListener('click', () => {
                        document.body.classList.remove('light-theme', 'auto-theme');
                        document.body.classList.add('dark-theme');
                        localStorage.setItem('theme', 'dark');
                    });
                });

                document.querySelectorAll('.js-set-theme-auto').forEach(el => {
                    el.addEventListener('click', () => {
                        document.body.classList.remove('light-theme', 'dark-theme');
                        document.body.classList.add('auto-theme');
                        localStorage.setItem('theme', 'auto');
                    });
                });
            });
        </script>
    </body>
    </html>
    '''
    return html_content

if __name__ == '__main__':
    html_content = generate_gallery_html()
    if not os.path.exists('templates'):
        os.makedirs('templates')
    with open('templates/gallery.html', 'w') as f:
        f.write(html_content)
    print("Gallery HTML has been generated and saved to templates/gallery.html")