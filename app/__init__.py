import os
from flask import Flask


def create_app():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'web_templates'),
        static_folder=os.path.join(os.path.dirname(__file__), 'static'),
    )
    upload_dir = os.path.join(base_dir, 'uploads')
    output_dir = os.path.join(base_dir, 'output')
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_dir
    app.config['OUTPUT_FOLDER'] = output_dir

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app