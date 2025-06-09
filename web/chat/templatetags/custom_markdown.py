import re
from django import template
register = template.Library()

@register.filter
def custom_markdown_parse(value):
    def protect_quotes(match):
        text = match.group(0)
        text = text.replace('.', '[[DOT]]').replace('!', '[[EXCL]]').replace('?', '[[QST]]')
        return text

    value = re.sub(r'"[^"]*"|\'[^\']*\'|`[^`]*`', protect_quotes, value)

    value = re.sub(r'\*\*?분석\*\*?(?::)?\s?', '### ✅ 문제 행동 분석\n', value)
    value = re.sub(r'\*\*?해결책 제시\*\*?(?::)?\s?', '\n### 🐾 솔루션\n', value)
    value = re.sub(r'\*\*?추가 질문\*\*?(?::)?\s?', '\n### 추가 질문\n', value)
    value = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', value)

    value = re.sub(r'(\d+)\.\s', r'<br><span style="margin-left:1em; display:inline-block;">\1.</span> ', value)
    value = re.sub(r'([.!?])(?=[^\d<\n])', r'\1<br>', value)
    value = re.sub(r'(<br>\s*){2,}', '<br>', value)
    value = re.sub(r'^### (.+)$', r'<h3>\1</h3>', value, flags=re.MULTILINE)

    def section_divs(match):
        title = match.group(1)
        content = match.group(2)
        return f'<div class="answer-section"><h3>{title}</h3>{content.strip()}</div>'

    value = re.sub(
        r'<h3>(.*?)</h3>(.*?)(?=(<h3>|$))',
        section_divs,
        value,
        flags=re.DOTALL
    )

    if '<div class="answer-section">' not in value:
        value = f'<div class="answer-section">{value.strip()}</div>'

    value = value.replace('<hr>', '')
    value = value.replace('[[DOT]]', '.').replace('[[EXCL]]', '!').replace('[[QST]]', '?')
    return value
