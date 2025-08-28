import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, send_file, current_app, flash, jsonify
from .services.renderer import parse_md_template, render_to_markdown
from .services.ai_generator import generate_syllabus_content
from .services.teaching_outline_generator import generate_teaching_outline
from .services.word_generator import create_word_from_outline

bp = Blueprint('main', __name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DEFAULT_MD_PATH = os.path.join(PROJECT_ROOT, 'templates', '教学大纲模板.md')

@bp.route('/', methods=['GET'])
def index():
    # 检查是否存在旧的模板文件
    old_template_path = os.path.join(PROJECT_ROOT, 'templates', 'syllabus_template.md')
    if os.path.exists(old_template_path):
        fields_meta, _, _ = parse_md_template(old_template_path)
        examples = {}
        for key, meta in fields_meta.items():
            if meta.get('type') == 'table':
                cols = meta.get('columns', [])
                row = {c: '' for c in cols}
                if key == 'schedule_table':
                    for c in ('讲授', '实验/实践', '作业'):
                        if c in row:
                            row[c] = []
                examples[key] = json.dumps([row], ensure_ascii=False, indent=2)
        return render_template('index.html', fields=fields_meta, examples=examples)
    else:
        # 如果没有旧模板，显示简单的导航页面
        return render_template('navigation.html')

@bp.route('/render', methods=['POST'])
def render_md():
    fields_meta, template_str, _ = parse_md_template(DEFAULT_MD_PATH)

    data = {}
    for key, meta in fields_meta.items():
        ftype = meta.get('type', 'text')
        if ftype == 'list':
            val = request.form.get(key, '').strip()
            items = [x.strip() for x in val.replace('\r', '').replace('\n', ',').split(',') if x.strip()] if val else []
            data[key] = items
        elif ftype == 'table':
            raw = request.form.get(key, '').strip()
            try:
                data[key] = json.loads(raw) if raw else []
            except Exception:
                data[key] = []
        else:
            data[key] = request.form.get(key, '').strip()

    # 读取列表渲染样式，并将教学进度表中的数组字段转为字符串以适配模板显示
    list_style = request.form.get('list_style', 'br')

    def _fmt_cells(val):
        if isinstance(val, list):
            if list_style == 'bullet':
                return '<br>'.join([f'• {x}' for x in val])
            return '<br>'.join(val)
        return val

    if isinstance(data.get('schedule_table'), list):
        for row in data['schedule_table']:
            if isinstance(row, dict):
                for k in ('讲授', '实验/实践', '作业'):
                    if k in row:
                        row[k] = _fmt_cells(row.get(k))

    md = render_to_markdown(template_str, data)

    out_path = os.path.join(current_app.config['OUTPUT_FOLDER'], 'rendered_syllabus.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(md)

    return render_template('preview.html', markdown_content=md, download_url=url_for('main.download_md'))

@bp.route('/download/md', methods=['GET'])
def download_md():
    out_path = os.path.join(current_app.config['OUTPUT_FOLDER'], 'rendered_syllabus.md')
    if not os.path.exists(out_path):
        return redirect(url_for('main.index'))
    return send_file(out_path, as_attachment=True, download_name='rendered_syllabus.md')

@bp.route('/ai/generate', methods=['POST'])
def ai_generate():
    payload = request.get_json(force=True) or {}
    course_name = payload.get('course_name', '')
    course_code = payload.get('course_code')
    credit = payload.get('credit')
    hours = payload.get('hours')
    prerequisites_text = payload.get('prerequisites', '')
    num_weeks = int(payload.get('num_weeks', 18) or 18)
    focus_points = payload.get('focus_points', '')
    exclude_points = payload.get('exclude_points', '')

    # 新增：大模型参数
    llm_provider = (payload.get('llm_provider') or '').strip()
    llm_api_key = payload.get('llm_api_key')
    llm_model = (payload.get('llm_model') or '').strip()

    data = generate_syllabus_content(
        course_name=course_name,
        course_code=course_code,
        credit=credit,
        hours=hours,
        prerequisites_text=prerequisites_text,
        num_weeks=num_weeks,
        focus_points=focus_points,
        exclude_points=exclude_points,
        llm_provider=llm_provider,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
    )
    return jsonify(data)

@bp.route('/teaching-outline', methods=['GET'])
def teaching_outline():
    """教学大纲生成页面"""
    return render_template('teaching_outline.html')

@bp.route('/teaching-outline/generate', methods=['POST'])
def generate_teaching_outline_api():
    """教学大纲AI生成API"""
    payload = request.get_json(force=True) or {}
    
    # 基本信息
    course_name = payload.get('course_name', '').strip()
    write_date = payload.get('write_date', '').strip()
    assessment_method = payload.get('assessment_method', '').strip()
    
    # AI生成参数
    exclude_items = payload.get('exclude_items', '').strip()
    
    # AI精细控制参数
    system_prompt = payload.get('system_prompt', '').strip()
    user_prompt = payload.get('user_prompt', '').strip()
    
    # 大模型设置
    llm_provider = payload.get('llm_provider', '').strip()
    llm_api_key = payload.get('llm_api_key', '').strip()
    llm_model = payload.get('llm_model', '').strip()
    
    # 字数控制参数
    positioning_length = payload.get('positioning_length', 100)
    objectives_length = payload.get('objectives_length', 80)
    module_content_length = payload.get('module_content_length', 60)
    
    if not course_name:
        return jsonify({'error': '课程名称不能为空'}), 400
        
    try:
        # 生成教学大纲内容
        outline_data = generate_teaching_outline(
            course_name=course_name,
            write_date=write_date,
            assessment_method=assessment_method,
            exclude_items=exclude_items,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            llm_provider=llm_provider,
            llm_api_key=llm_api_key,
            llm_model=llm_model,
            positioning_length=positioning_length,
            objectives_length=objectives_length,
            module_content_length=module_content_length
        )
        
        return jsonify(outline_data)
        
    except Exception as e:
        current_app.logger.error(f'生成教学大纲失败: {str(e)}')
        return jsonify({'error': f'生成失败: {str(e)}'}), 500

@bp.route('/teaching-outline/preview', methods=['POST'])
def preview_teaching_outline():
    """预览生成的教学大纲"""
    payload = request.get_json(force=True) or {}
    
    # 读取教学大纲模板
    template_path = os.path.join(PROJECT_ROOT, 'templates', '教学大纲模板.md')
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # 替换模板变量
        for key, value in payload.items():
            if value:
                template_content = template_content.replace(f'{{{{{key}}}}}', str(value))
        
        # 保存生成的文件
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], '教学大纲.md')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        return render_template('teaching_outline_preview.html', 
                             markdown_content=template_content,
                             download_url=url_for('main.download_teaching_outline'))
        
    except Exception as e:
        current_app.logger.error(f'预览教学大纲失败: {str(e)}')
        return jsonify({'error': f'预览失败: {str(e)}'}), 500

@bp.route('/download/teaching-outline', methods=['GET'])
def download_teaching_outline():
    """下载生成的教学大纲"""
    output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], '教学大纲.md')
    if not os.path.exists(output_path):
        return redirect(url_for('main.teaching_outline'))
    return send_file(output_path, as_attachment=True, download_name='教学大纲.md')

@bp.route('/teaching-outline/generate-word', methods=['POST'])
def generate_word_document():
    """生成Word文档"""
    payload = request.get_json(force=True) or {}
    
    course_name = payload.get('课程名称', '')
    if not course_name:
        return jsonify({'error': '课程名称不能为空'}), 400
    
    try:
        # 生成Word文档
        word_path = create_word_from_outline(
            outline_data=payload,
            course_name=course_name,
            output_dir=current_app.config['OUTPUT_FOLDER']
        )
        
        # 返回下载链接
        filename = os.path.basename(word_path)
        download_url = url_for('main.download_word_document', filename=filename)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'download_url': download_url,
            'message': 'Word文档生成成功'
        })
        
    except Exception as e:
        current_app.logger.error(f'生成Word文档失败: {str(e)}')
        return jsonify({'error': f'生成失败: {str(e)}'}), 500

@bp.route('/download/word/<filename>', methods=['GET'])
def download_word_document(filename):
    """下载Word文档"""
    file_path = os.path.join(current_app.config['OUTPUT_FOLDER'], filename)
    
    if not os.path.exists(file_path):
        flash('文件不存在', 'error')
        return redirect(url_for('main.teaching_outline'))
    
    return send_file(file_path, as_attachment=True, download_name=filename)