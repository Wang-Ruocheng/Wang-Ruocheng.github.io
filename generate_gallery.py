import os

def generate_gallery_html():
    gallery_path = 'gallery'
    categories_order = ['family', 'travel', 'food']
    categories_title_indict = {'family': 'Family', 'travel': 'Travel', 'food': 'Food'}
    html_content = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
         <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gallery</title>
         <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
         <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
         <link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Cutive+Mono&family=Lora:wght@400;700&family=Roboto:wght@400;700&display=swap&display=swap">
         <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cutive+Mono&family=Lora:wght@400;700&family=Roboto:wght@400;700&display=swap&display=swap" media="print" onload="this.media='all'">
         <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
         <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cutive+Mono&family=Lora:wght@400;700&family=Roboto:wght@400;700&display=swap&display=swap" media="print" onload="this.media='all'">
         <link rel="stylesheet" href="/css/vendor-bundle.min.047268c6dd09ad74ba54a0ba71837064.css" media="print" onload="this.media='all'"> 
         <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/academicons@1.9.2/css/academicons.min.css" integrity="sha512-KlJCpRsLf+KKu2VQa5vmRuClRFjxc5lXO03ixZt82HZUk41+1I0bD8KBSA0fY290ayMfWYI9udIqeOWSu1/uZg==" crossorigin="anonymous" media="print" onload="this.media='all'">
         <link rel="stylesheet" href="/css/libs/chroma/github-light.min.css" title="hl-light" media="print" onload="this.media='all'" >
         <link rel="stylesheet" href="/css/libs/chroma/dracula.min.css" title="hl-dark" media="print" onload="this.media='all'" disabled>
         <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
            font-family: 'Roboto', sans-serif; /* 设置全局字体 */
                background-color: transparent; /* 设置背景颜色为透明 */
                mix-blend-mode: difference;
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
                background-color: transparent; /* 设置卡片背景颜色为透明 */
                color: inherit; /* 继承全局字体颜色 */
            }
            .card-body {
                background-color: transparent; /* 设置卡片内容区域背景颜色为透明 */
                font-size: 0.9em; /* 调整字体大小 */
            }

            /* 媒体查询 */
            @media (max-width: 1200px) {
                .gallery-container {
                    column-count: 4; /* 设置列数 */
                }
                .category-title {
                    font-size: 1.4em;
                }
                .card-body {
                    font-size: 0.8em; /* 调整字体大小 */
                }
            }
            @media (max-width: 992px) {
                .gallery-container {
                    column-count: 4; /* 设置列数 */
                }
                .category-title {
                    font-size: 1.4em;
                }
                .card-body {
                    font-size: 0.8em; /* 调整字体大小 */
                }
            }
            @media (max-width: 768px) {
                .gallery-container {
                    column-count: 3; /* 设置列数 */
                }
                .category-title {
                    font-size: 1.3em;
                }
                .card-body {
                    font-size: 0.7em; /* 调整字体大小 */
                }
            }
            @media (max-width: 576px) {
                .gallery-container {
                    column-count: 3; /* 设置列数 */
                }
                .category-title {
                    font-size: 1.3em;
                }
                .card-body {
                    font-size: 0.7em; /* 调整字体大小 */
                }
            }
        </style>
        <script>
            document.addEventListener('DOMContentLoaded', (event) => {
                document.documentElement.setAttribute('data-theme', 'dark');
            });
          </script>
    </head>
    <body>
            <div class="gallery-container">
    '''

    for category in categories_order:
        category_path = os.path.join(gallery_path, category)
        if os.path.isdir(category_path):
            html_content += f'<div class="category-title">{categories_title_indict[category]}</div>'
            for image in os.listdir(category_path):
                if image.endswith(('jpg', 'jpeg', 'png', 'gif')):
                    image_path = os.path.join(category, image)
                    html_content += f'''
                    <div class="gallery-item">
                        <div class="card" style="{'border: none;' if category == 'food' else ''}">
                            <img data-src="/gallery/{image_path}" class="card-img-top" alt="{image}" src="data:image/gif;base64,R0lGODlhAQABAIAAAAUEBA==">
                    '''
                    if category != 'food':
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
            // 延迟加载图片
                var lazyImages = [].slice.call(document.querySelectorAll("img[data-src]"));

                if ("IntersectionObserver" in window) {
                    let lazyImageObserver = new IntersectionObserver(function(entries, observer) {
                        entries.forEach(function(entry) {
                            if (entry.isIntersecting) {
                                let lazyImage = entry.target;
                                lazyImage.src = lazyImage.dataset.src;
                                lazyImage.removeAttribute("data-src");
                                lazyImageObserver.unobserve(lazyImage);
                            }
                        });
                    });

                    lazyImages.forEach(function(lazyImage) {
                        lazyImageObserver.observe(lazyImage);
                    });
                } else {
                    // Fallback for browsers that do not support IntersectionObserver
                    lazyImages.forEach(function(lazyImage) {
                        lazyImage.src = lazyImage.dataset.src;
                        lazyImage.removeAttribute("data-src");
                    });
                }
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