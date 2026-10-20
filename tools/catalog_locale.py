# SPDX-FileCopyrightText: 2026 Pear contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Reviewed presentation messages and locale routes; never translate report data."""
import html
import json
import posixpath
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

MESSAGES = json.loads((Path(__file__).parent / 'catalog/locales/ko.json').read_text())
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


def message(text):
    key = ' '.join(text.split())
    if key.startswith('Pear · '):
        return 'Pear · ' + message(key[7:])
    if key in MESSAGES:
        return MESSAGES[key]
    for pattern, replacement in (
        (r'(\d+) reports?', r'제보 \1건'), (r'(\d+) games?', r'게임 \1개'),
        (r'(\d+) (?:minutes? read|min read)', r'읽는 데 약 \1분'),
        (r'(\d+) entr(?:y|ies) about this topic', r'이 주제의 글 \1개'),
        (r'Last tested (.+)', r'최근 확인 \1'), (r'Votes synced (.+)', r'추천 수 갱신 \1'),
        (r'↑ (\d+) · Vote on GitHub', r'↑ \1 · GitHub에서 추천'),
        (r'October (\d+), (\d+)', r'\2년 10월 \1일'),
    ):
        if re.fullmatch(pattern, key):
            return re.sub(pattern, replacement, key)
    return key


class Presentation(HTMLParser):
    """Only text and accessible labels change. Protected content stays verbatim."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output, self.stack = [], []

    @property
    def protected(self):
        return bool(self.stack and self.stack[-1][1])

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        protected = self.protected or values.get('translate') == 'no' or tag in {'script', 'style', 'code', 'pre'}
        updated = []
        for key, value in attrs:
            if not protected and value is not None and (key in {'aria-label', 'title', 'placeholder', 'alt', 'data-message'} or tag == 'meta' and key == 'content'):
                value = message(value)
            if tag == 'html' and key == 'lang':
                value = 'ko'
            updated.append(key if value is None else f'{key}="{html.escape(value, quote=True)}"')
        self.output.append('<' + tag + (' ' + ' '.join(updated) if updated else '') + '>')
        if tag not in VOID:
            self.stack.append((tag, protected))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        self.output.append(f'</{tag}>')
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_data(self, text):
        if self.protected or not text.strip():
            self.output.append(text if self.stack and self.stack[-1][0] in {'script', 'style'} else html.escape(text))
        else:
            leading = text[:len(text) - len(text.lstrip())]
            trailing = text[len(text.rstrip()):]
            self.output.append(leading + html.escape(message(html.unescape(text))))
            self.output.append(trailing)

    def handle_entityref(self, name):
        self.output.append(f'&{name};')

    def handle_charref(self, name):
        self.output.append(f'&#{name};')

    def handle_comment(self, text):
        self.output.append('<!--' + text + '-->')

    def handle_decl(self, text):
        self.output.append('<!' + text + '>')


def translate(content):
    # Options without explicit values originally submit their English labels.
    content = re.sub(r'<option>([^<]*)</option>', lambda m: '<option value="' + html.escape(html.unescape(m[1]), quote=True) + '">' + m[1] + '</option>', content)
    parser = Presentation()
    parser.feed(content)
    parser.close()
    return ''.join(parser.output)


def korean_pages(pages):
    """Move page destinations into ko/ while referring to one shared asset tree."""
    output = {}
    for source, content in pages.items():
        destination = 'ko/' + source
        directory = posixpath.dirname(destination) or '.'
        class Routes(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=False)
                self.output = []
            def handle_starttag(self, tag, attrs):
                values = []
                for key, value in attrs:
                    if key in {'href', 'src', 'poster', 'data-steam-index'} and value and not value.startswith(('#', '/')):
                        parsed = urlsplit(value)
                        if not parsed.scheme and not parsed.netloc:
                            target = posixpath.normpath(posixpath.join(posixpath.dirname(source), parsed.path))
                            if target in pages:
                                target = 'ko/' + target
                            value = urlunsplit(('', '', posixpath.relpath(target, directory), parsed.query, parsed.fragment))
                    values.append(key if value is None else f'{key}="{html.escape(value, quote=True)}"')
                self.output.append('<' + tag + (' ' + ' '.join(values) if values else '') + '>')
            def handle_endtag(self, tag): self.output.append(f'</{tag}>')
            def handle_data(self, text): self.output.append(text)
            def handle_entityref(self, name): self.output.append(f'&{name};')
            def handle_charref(self, name): self.output.append(f'&#{name};')
            def handle_comment(self, text): self.output.append('<!--' + text + '-->')
            def handle_decl(self, text): self.output.append('<!' + text + '>')
        parser = Routes()
        if source.startswith('game-'):
            content = content.replace('<title>', '<title translate="no">').replace('<meta property="og:title"', '<meta translate="no" property="og:title"').replace('<meta name="twitter:title"', '<meta translate="no" name="twitter:title"')
        parser.feed(translate(content))
        output[destination] = ''.join(parser.output)
    return output
