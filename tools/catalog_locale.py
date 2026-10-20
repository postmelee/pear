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
    if key in MESSAGES:
        return MESSAGES[key]
    if key.startswith('· ') and key.endswith(' ·'):
        return '· ' + message(key[2:-2]) + ' ·'
    if key.startswith('· '):
        return '· ' + message(key[2:])
    if key.endswith(' ·'):
        return message(key[:-2]) + ' ·'
    if key.startswith('Pear · '):
        return 'Pear · ' + message(key[7:])
    if key in MESSAGES:
        return MESSAGES[key]
    for pattern, replacement in (
        (r'View (.+) reports', r'\1 제보 보기'), (r'(.+) artwork', r'\1 대표 이미지'),
        (r'Player reports (\d+)', r'사용자 제보 \1'), (r'(\d+) min', r'\1분'),
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
    known_routes = {}
    for name in pages:
        route = name.removesuffix('index.html') if name.endswith('index.html') else name.removesuffix('.html') + '/'
        known_routes[name] = name
        known_routes[route] = name
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
                        if parsed.scheme == 'https' and parsed.netloc == 'postmelee.github.io' and parsed.path.startswith('/pear/'):
                            target = known_routes.get(parsed.path.removeprefix('/pear/'))
                            if target:
                                value = urlunsplit(('', '', posixpath.relpath('ko/' + target, directory), parsed.query, parsed.fragment))
                        elif not parsed.scheme and not parsed.netloc:
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


def javascript_messages():
    """Emit the same reviewed messages for explicitly selected interactive UI sinks."""
    dictionary = json.dumps(MESSAGES, ensure_ascii=False).replace('<', '\\u003c')
    return '// SPDX-FileCopyrightText: 2026 Pear contributors\n// SPDX-License-Identifier: GPL-3.0-or-later\n' + 'globalThis.PearI18n = (() => {\nconst messages = ' + dictionary + ';\n' + r"""
const korean = document.documentElement.lang === 'ko';
function t(text) {
  if (!korean || typeof text !== 'string' || !text) return text;
  if (messages[text]) return messages[text];
  const rules = [
    [/^(\d+) reports?$/, '$1건의 제보'], [/^(\d+) games?$/, '게임 $1개'],
    [/^Last tested (.+)$/, '최근 확인 $1'],
    [/^(\d+) results?$/, '검색 결과 $1개'],
    [/^0 results — try a page, game, or topic such as Rosetta\.$/, '검색 결과가 없습니다. 게임 이름이나 Rosetta 같은 주제를 검색해 보세요.'],
    [/^Steam list updated (.+)\.$/, 'Steam 목록 갱신: $1'],
    [/^(.+) selected · Steam App (\d+)$/, '$1 선택됨 · Steam App $2'],
    [/^Steam App (\d+) · In Pear’s catalog$/, 'Steam App $1 · Pear 카탈로그에 있음'],
    [/^Steam App (\d+) · Steam game identity\.$/, 'Steam App $1 · Steam 게임 정보'],
    [/^Steam App (\d+) · Name from Pear’s reviewed catalog\.$/, 'Steam App $1 · Pear에서 검토한 카탈로그의 이름'],
    [/^Steam App (\d+) · You can submit by ID\. The name will be checked before publication\.$/, 'Steam App $1 · ID만으로 제출할 수 있습니다. 이름은 공개 전에 확인합니다.'],
  ];
  for (const [pattern, replacement] of rules) if (pattern.test(text)) return text.replace(pattern, replacement);
  const suggestions = text.match(/^(Up to 8|\d+) suggestions\. (.*)$/);
  if (suggestions) return (suggestions[1] === 'Up to 8' ? '최대 8' : suggestions[1]) + '개 추천 · ' + t(suggestions[2]);
  const noMatches = 'No matches. Try another name or paste a Steam link. ';
  if (text.startsWith(noMatches)) return t(noMatches.trim()) + ' ' + t(text.slice(noMatches.length));
  return text;
}
return {t};
})();
"""
