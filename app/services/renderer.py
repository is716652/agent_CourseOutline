import os
import yaml
from jinja2 import Template


def parse_md_template(md_path: str):
    """
    读取带 YAML Front Matter 的 Markdown 模板
    返回：fields(dict), template_body(str), meta(dict)
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if content.startswith('---'):
        parts = content.split('\n---\n', 1)
        header = parts[0][3:]  # 去掉起始 ---
        body = parts[1] if len(parts) > 1 else ''
        meta = yaml.safe_load(header) or {}
    else:
        meta = {}
        body = content

    fields = (meta or {}).get('fields', {})
    return fields, body, meta


def render_to_markdown(template_str: str, data: dict) -> str:
    template = Template(template_str)
    return template.render(**data)