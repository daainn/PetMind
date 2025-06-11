import re
from django import template

register = template.Library()

@register.filter
def custom_markdown_parse(value):
    if not value:
        return ''

    value = re.sub(r'^\s*\n(?=\d+\.)', '', value, flags=re.MULTILINE)

    value = re.sub(
        r'(^-\s.*?)(?:\n\s*\n)+(?=-\s)',
        r'\1\n',
        value,
        flags=re.MULTILINE
    )

    def protect_quotes(match):
        text = match.group(0)
        return (text.replace('.', '[[DOT]]')
                    .replace('!', '[[EXCL]]')
                    .replace('?', '[[QST]]'))
    value = re.sub(r'"[^"]*"|\'[^\']*\'|`[^`]*`', protect_quotes, value)

    value = re.sub(r'\*\*?분석\*\*?(?::)?\s?', '### ✅ 문제 행동 분석\n', value)
    value = re.sub(r'\*\*?해결책 제시\*\*?(?::)?\s?', '\n### 🐾 솔루션\n', value)
    value = re.sub(r'\*\*?추가 질문\*\*?(?::)?\s?', '\n### 추가 질문\n', value)

    value = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', value)

    value = re.sub(
        r'((?:^\d+\.\s.+\n?)+)',
        lambda m: (
            '<ol style="margin:0.5em 0 0 1.2em; padding:0;">'
            + ''.join(
                f'<li>{line.lstrip(re.match(r"^\d+\.\s*", line).group(0)).strip()}</li>'
                for line in m.group(0).strip().splitlines()
            )
            + '</ol>'
        ),
        value,
        flags=re.MULTILINE
    )

    value = re.sub(
        r'((?:^-\s.+\n?)+)',
        lambda m: (
            '<ul style="margin:0.5em 0 0 1.2em; padding:0;">'
            + ''.join(
                f'<li>{line.lstrip("- ").strip()}</li>'
                for line in m.group(0).strip().splitlines()
            )
            + '</ul>'
        ),
        value,
        flags=re.MULTILINE
    )

    value = re.sub(r'(<br>\s*){2,}', '<br>', value)

    value = re.sub(r'^### (.+)$', r'<h3>\1</h3>', value, flags=re.MULTILINE)

    def section_divs(match):
        title, content = match.group(1), match.group(2)
        return f'<div class="answer-section"><h3>{title}</h3>{content.strip()}</div>'
    value = re.sub(r'<h3>(.*?)<\/h3>(.*?)(?=<h3>|$)', section_divs, value, flags=re.DOTALL)

    if '<div class="answer-section">' not in value:
        value = f'<div class="answer-section">{value.strip()}</div>'

    return (value
            .replace('[[DOT]]', '.')
            .replace('[[EXCL]]', '!')
            .replace('[[QST]]', '?'))
