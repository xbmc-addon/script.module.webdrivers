# -*- coding: utf-8 -*-

__author__ = 'hal9000'

import time
import re
import json
import threading
import htmlentitydefs

import xbmc

import requests2 as requests

from xbmcup.cache import Cache

CACHE_VERSION = '1'


class Clear:
    RE = {
        'space': re.compile('[ ]{2,}', re.U|re.S),
        'cl': re.compile('[\n]{2,}', re.U|re.S),
        'br': re.compile('<\s*br[\s/]*>', re.U|re.S),
        'inner': re.compile('<[^>]*>[^<]+<\s*/[^>]*>', re.U|re.S),
        'html': re.compile('<[^>]*>', re.U|re.S),
        'entity': re.compile('&#?\w+;', re.U)
    }

    UNSUPPORT = {
        '&#151;': '-'
    }

    def text(self, text, inner=False):
        text = self._unsupport(text).replace(u'\r', u'\n')
        text = self.RE['br'].sub(u'\n', text)
        if inner:
            text = self.RE['inner'].sub(u'', text)
        text = self.RE['html'].sub(u'', text)
        text = self.char(text)
        text = self.RE['space'].sub(u' ', text)
        return self.RE['cl'].sub(u'\n', text).strip()

    def string(self, text, space=u''):
        return self.text(text).replace(u'\n', space).strip()

    def char(self, text):
        return self.RE['entity'].sub(self._unescape, self._unsupport(text))

    def _unsupport(self, text):
        for tag, value in self.UNSUPPORT.iteritems():
            text = text.replace(tag, value)
        return text

    def _unescape(self, m):
        text = m.group(0)
        if text[:2] == u"&#":
            try:
                if text[:3] == u"&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text



class Base:
    def __init__(self):
        self.cache = Cache('webdrivers.kinopoisk', CACHE_VERSION)
        self.clear = Clear()


    def fetch(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4',
            'Cache-Control': 'no-cache',
            'Referer': 'http://www.kinopoisk.ru/'
        }
        try:
            response = requests.get(url, headers=headers)
        except requests.exceptions.RequestException:
            return ''
        else:
            return response.text if response.status_code == 200 else ''


    def thread(self, functions):
        result, pool = {}, []

        def call(token, fun, args):
            result[token] = fun(*args)

        for token, fun, args in functions:
            pool.append(threading.Thread(target=call, args=(token, fun, args)))

        for t in pool:
            t.start()
        for t in pool:
            t.join()

        return result





class Movies(Base):
    def vote(self):
        pass

    def scraper(self):
        pass

    def premiere(self):
        pass

    def comingsoon(self):
        pass

    def top250(self):
        pass

    def list(self):
        pass

    def top(self):
        pass

    def box(self):
        pass

    def search(self):
        pass

    def recommend(self):
        pass

    def popular(self):
        pass


    def get(self, ids, fields=None):

        def compile_fields(fields):
            full = 'covers', 'wallpapers', 'stills', 'trailers', 'studios', 'people'
            if fields is None:
                return tuple()
            if isinstance(fields, basestring):
                fields = [x for x in [x.strip() for x in fields.split(',')] if x]
            if 'full' in fields:
                return full
            return [x for x in full if x in fields]


        def parse_info(html):
            info = {}

            # имя, оригинальное имя, девиз, возрастное ограничение, длительность фильма, год, top250
            for tag, reg, fun in (
                ('title', '<title>(.+?)</title>', self.clear.string),
                ('originaltitle', 'itemprop="alternativeHeadline">([^<]*)</span>', self.clear.string),
                ('tagline', '<td style="color\: #555">&laquo;(.+?)&raquo;</td></tr>', self.clear.string),
                ('mpaa', 'images/mpaa/([^\.]+).gif', self.clear.string),
                ('runtime', '<td class="time" id="runtime">[^<]+<span style="color\: #999">/</span>([^<]+)</td>', self.clear.string),
                ('year', '<a href="/lists/m_act%5Byear%5D/([0-9]+)/"', int),
                ('top250', 'Топ250\: <a\shref="/level/20/#([0-9]+)', int)
                ):
                r = re.search(reg, html, re.U)
                if r:
                    value = r.group(1).strip()
                    if value:
                        info[tag] = fun(value)

            if 'title' not in info:
                return None

            # режисеры, сценаристы, жанры, актеры
            for tag, reg, fun in (
                ('director', u'<td itemprop="director">(.+?)</td>', lambda x:u', '.join(x)),
                ('writer', u'<td class="type">сценарий</td><td[^>]*>(.+?)</td>', lambda x:u', '.join(x)),
                ('genre', u'<span itemprop="genre">(.+?)</span>', lambda x:u', '.join(x)),
                ('cast', u'<h4>В главных ролях:</h4>(.+?)</ul>', lambda x:x),
                ):
                r = re.search(reg, html, re.U|re.S)
                if r:
                    r = [x for x in [self.clear.string(x) for x in re.findall('<a href="[^"]+">([^<]+)</a>', r.group(1))] if x and x != '...']
                    if r:
                        info[tag] = fun(r)


            # описание фильма
            r = re.search('<span class="_reachbanner_"><div class="brand_words" itemprop="description">(.+?)</div></span>', html, re.U)
            if r:
                plot = self.clear.text(r.group(1).replace('<=end=>', '\n'))
                if plot:
                    info['plot'] = plot


            # премьера
            r = re.search(u'премьера \(мир\)</td>(.+?)</tr>', html, re.U|re.S)
            if r:
                r = re.search(u'data\-ical\-date="([^"]+)"', r.group(1), re.U|re.S)
                if r:
                    data = r.group(1).split(' ')
                    if len(data) == 3:
                        i = 0
                        for mon in (u'января', u'февраля', u'марта', u'апреля', u'мая', u'июня', u'июля', u'августа', u'сентября', u'октября', u'ноября', u'декабря'):
                            i += 1
                            if mon == data[1]:
                                mon = str(i)
                                if len(mon) == 1:
                                    mon = '0' + mon
                                day = data[0]
                                if len(day) == 1:
                                    day = '0' + day
                                info['premiered'] = '-'.join([data[2], mon, day])
                                break

            # IMDB
            r = re.search('IMDb: ([0-9.]+) \(([0-9\s]+)\)</div>', html, re.U)
            if r:
                info['rating'] = float(r.group(1).strip())
                info['votes'] = r.group(2).strip()

            return info



        def parse_pics_url(html, ratio):
            r = re.search('var wallpapers =(.+?)</script>', html, re.S)
            if r:
                filter = (lambda x: x['width'] > x['height']) if ratio == 'width' else (lambda x: x['width'] < x['height'])
                try:
                    pics = [x for x in [{'width': int(x['width']), 'height': int(x['height']), 'src': 'http://st-im.kinopoisk.ru' + x['image']} for x in json.loads(r.group(1).replace(';', '').strip()).values()] if filter(x)]
                except:
                    pass
                else:
                    pics.sort(key=(lambda x: x['width']), reverse=True)
                    best = [x for x in pics if x['width'] <= 1280]
                    if best:
                        pics = best
                    return [x['src'] for x in pics]
            r = re.search('id="image" src="([^"]+?)"', html, re.S)
            if r:
                return [r.group(1)]
            return []


        def parse_pics(url, ratio):
            html = self.fetch(url)
            if html:
                r = re.search('<a href="/picture/([0-9]+)/"><img', html, re.S)
                if r:
                    html = self.fetch('http://www.kinopoisk.ru/picture/' + r.group(1) + '/')
                    if html:
                        return parse_pics_url(html, ratio)
            return []


        def get_covers(id, menu):
            if menu.find('/film/' + id + '/covers/') != -1:
                return parse_pics('http://www.kinopoisk.ru/film/' + id + '/covers/', 'height')
            if menu.find('/film/' + id + '/posters/') != -1:
                return parse_pics('http://www.kinopoisk.ru/film/' + id + '/posters/', 'height')
            return []


        def get_stills(id, menu):
            if menu.find('/film/' + id + '/stills/') != -1:
                return parse_pics('http://www.kinopoisk.ru/film/' + id + '/stills/', 'width')
            return []


        def get_wallpapers(id, menu):
            if menu.find('/film/' + id + '/wall/') != -1:
                html = self.fetch('http://www.kinopoisk.ru/film/' + id + '/wall/')
                if html:
                    pics = sorted([(x[0], int(x[1])) for x in re.findall('<a href="/picture/([0-9]+)/w_size/([0-9]+)/">', html, re.U)], key=(lambda x: x[1]))
                    if pics:
                        best = [x for x in pics if x[1] <= 1280]
                        if best:
                            pics = best
                        html = self.fetch('http://www.kinopoisk.ru/picture/' + pics[-1][0] + '/w_size/' + str(pics[-1][1]) + '/')
                        if html:
                            return parse_pics_url(html, 'width')
            return []


        def get_studios(id, menu):
            if menu.find('/film/' + id + '/studio/') != -1:
                html = self.fetch('http://www.kinopoisk.ru/film/' + id + '/studio/')
                if html:
                    r = re.search(u'<b>Производство:</b>(.+?)</table>', html, re.U|re.S)
                    if r:
                        return [{'id': x[0], 'name': x[1]} for x in [(int(x[0]), self.clear.string(x[1])) for x in re.findall('<a href="/lists/m_act%5Bstudio%5D/([0-9]+)/" class="all">(.+?)</a>', r.group(1), re.U)] if x[1]]



        def get_trailers(id, menu):
            if menu.find('/film/' + id + '/video/') == -1:
                return []

            html = self.fetch('http://www.kinopoisk.ru/film/' + id + '/video/')
            if not html:
                return []

            trailers1 = [] # русские трейлеры
            trailers2 = [] # другие русские видео
            trailers3 = [] # трейлеры
            trailers4 = [] # другие видео

            for row in re.findall(u'<!-- ролик -->(.+?)<!-- /ролик -->', html, re.U|re.S):

                # отсекаем лишние блоки
                if row.find(u'>СМОТРЕТЬ</a>') != -1:

                    # получаем имя трейлера
                    r = re.search('<a href="/film/' + id + '/video/[0-9]+/[^>]+ class="all">(.+?)</a>', row, re.U)
                    if r:
                        name = self.clear.string(r.group(1))
                        if name:

                            trailer = {
                                'name': name,
                                'trailer': bool([x for x in (u'Трейлер', u'трейлер', u'Тизер', u'тизер') if name.find(x) != -1]),
                                'ru': bool(row.find('class="flag flag2"') != -1),
                                'quality': 0,
                                'video': None,
                                'size': None,
                                'time': None
                            }

                            # получаем время трейлера
                            r = re.search(u'clock.gif"[^>]+></td>\s*<td style="color\: #777">[^0-9]*([0-9\:]+)</td>', row, re.U|re.S)
                            if r:
                                trailer['time'] = r.group(1).strip()

                                # делим ролики по качеству
                                for r in re.findall('trailer/([1-3])a.gif"(.+?)link=([^"]+)" class="continue">.+?<td style="color\:#777">([^<]+)</td>\s*</tr>', row, re.U|re.S):
                                    trailer['video'] = r[2].strip()
                                    trailer['size'] = r[3].strip()
                                    trailer['quality'] = int(r[0])
                                    if r[1].find('icon-hd') != -1:
                                        trailer['quality'] += 3

                                if trailer['video']:
                                    if trailer['ru']:
                                        trailers1.append(trailer) if trailer['trailer'] else trailers2.append(trailer)
                                    else:
                                        trailers3.append(trailer) if trailer['trailer'] else trailers4.append(trailer)

            # склеиваем трейлеры
            trailers1.sort(key=(lambda x: x['quality']), reverse=True)
            trailers2.sort(key=(lambda x: x['quality']), reverse=True)
            trailers3.sort(key=(lambda x: x['quality']), reverse=True)
            trailers4.sort(key=(lambda x: x['quality']), reverse=True)
            return trailers1 + trailers2 + trailers3 + trailers4



        def get_people(id, menu):
            people = dict([(x['occupation'], []) for x in OCCUPATIONS])
            html = self.fetch('http://www.kinopoisk.ru/film/' + id + '/cast/')
            if html:
                for i, block in enumerate(re.split('<a name="([^"]+?)"></a>', html, re.S)[1:]):
                    if 2*(i/2) == i:
                        role = block
                    else:
                        for r in [x for x in re.findall('<img class="flap_img"[^>]+?title="/images/([^"]+?)".+?<div class="name"><a href="/name/([0-9]+?)/">([^<]+?)</a> <span class="gray">([^<]+?)</span></div>', block, re.S)]:
                            name = {'id': int(r[1]), 'name': r[2], 'photo': (None if r[0] == 'no-poster.gif' else 'http://st.kp.yandex.net/images/actor_iphone/iphone360_' + r[1] + '.jpg'), 'original': (r[2] if r[3] == '&nbsp;' else r[3])}
                            try:
                                people[role].append(name)
                            except KeyError:
                                pass
            return people




        def fetch(id, fields):

            html = self.fetch('http://www.kinopoisk.ru/film/' + id + '/')
            if not html:
                return 600, None # 10 minutes

            res = {
                'id': int(id),
                'info': parse_info(html),
                'covers': [],
                'wallpapers': [],
                'stills': [],
                'trailers': [],
                'studios': [],
                'people': dict([(x['occupation'], []) for x in OCCUPATIONS])
            }

            if not res['info']:
                return 600, None # 10 minutes


            # смотрим, какие дополнительные страницы есть на сайте
            r = re.search('<ul id="newMenuSub" class="clearfix(.+?)<!\-\- /menu \-\->', html, re.U|re.S)
            if r:
                menu = r.group(1)
                res.update(self.thread([
                    ('covers', get_covers, (id, menu)),
                    ('wallpapers', get_wallpapers, (id, menu)),
                    ('stills', get_stills, (id, menu)),
                    ('studios', get_studios, (id, menu)),
                    ('trailers', get_trailers, (id, menu)),
                    ('people', get_people, (id, menu))
                ]))


            # постер
            r = re.search("openImgPopup\('([^']+)'\)", html, re.S)
            if r:
                res['covers'].insert(0, 'http://www.kinopoisk.ru' + r.group(1))


            # студии в info
            if res['studios']:
                res['info']['studio'] = u', '.join([x['name'] for x in res['studios']])

            # трейлер в info
            if res['trailers']:
                res['info']['trailer'] = res['trailers'][0]['video']


            ttl = 365*24*60*60 # year
            # если фильм свежий, то кладем в кэш НЕ на долго (могут быть обновления на сайте)
            if 'year' not in res['info'] or int(res['info']['year']) >= time.gmtime(time.time()).tm_year:
                ttl = 7*24*60*60 # week
            #return ttl, res
            # на время тестирования
            return res


        # смотрим, какие поля затребовали
        fields = compile_fields(fields)

        if isinstance(ids, (list, tuple)):
            print str(ids)
            ids, ret = [str(id) for id in ids], lambda x: [x[id] for id in ids]
        else:
            ids, ret = [str(ids)], lambda x: x[ids[0]]
        #print str(ret())
        print str(self.thread([(id, self.cache.call, ('movie:' + id, fetch, id, fields)) for id in ids]))





    def info(self, ids, fields):
        fields = self._fields(fields)
        if isinstance(ids, (list, tuple)):
            res, ids = [], [str(x) for x in ids]
            full = self._profile([x for x in ids if x.isdigit()], fields)
            for id in ids:
                if not id.isdigit():
                    res.append(None)
                else:
                    res.append(full.get(id))
        else:
            id = str(ids)
            if not id.isdigit():
                return None
            return self._profile([id], fields).get(id)



    # PRIVATE


    def _fields(self, fields):
        full = 'info', 'covers', 'wallpapers', 'stills', 'trailers', 'studios', 'people'
        if fields is None:
            return tuple()
        if isinstance(fields, basestring):
            fields = [x for x in [x.strip() for x in fields.split(',')] if x]
        if 'full' in fields:
            return full
        return [x for x in full if x in fields]


    def _default(self, meta, fields):
        res = {'meta': meta}
        for field in fields:
            if field == 'info':
                res['info'] = {}
            elif field == 'people':
                res['people'] = {}
            else:
                res[field] = []
        return res


    def _full(self, meta_list, fields):
        if not meta_list:
            return []
        fields = self._fields(fields)
        if not fields:
            return [{'meta': x} for x in meta_list]
        res, ids = [], [str(x['id']) for x in meta_list]
        full = self._profile(ids, fields)
        for i, id in enumerate(ids):
            if id in full:
                res.append(full[id])
            else:
                res.append(self._default(meta_list[i], fields))
        return res



    def _profile(self, ids, fields):


        def get_meta(id):
            html = self.fetch('http://www.kinopoisk.ru/film/' + id + '/')
            if not html:
                return 600, None # 10 minutes



        def get_covers(id, subdir):
            if 'covers' in subdir:
                pass
            if 'posters' in subdir:
                pass
            return []


        def get_wallpapers(id, subdir):
            return []


        def get_stills(id, subdir):
            return []


        def get_studios(id, subdir):
            return []


        def get_people(id, subdir):
            return []


        def get_trailers(id, subdir):
            return []



        def get(id, field, subdir):
            # TODO: выставить тут таймауты для кэша
            return {
                'covers': get_covers,
                'wallpapers': get_wallpapers,
                'stills': get_stills,
                'studios': get_studios,
                'people': get_people,
                'trailers': get_trailers
            }[field](id, subdir)



        def fetch(id, fields):
            index = self.cache.call('movie:index:' + id, get_meta, id)
            if not index:
                return None

            res = self._default(index['meta'], fields)

            task = []
            for field in fields:
                if field == 'info':
                    res['info'] = index['info']
                elif field in index['subdir']:
                    task.append((field, self.cache.get, ('movie:' + field + ':' + id, get, id, field, index['subdir'][field])))

            if task:
                res.update(self.thread(task))

            # TODO: тут надо обновить трейлеры в инфо и так далее...

            return res


        result = self.thread([(id, fetch, (id, fields)) for id in ids])
        return dict([(id, result[id]) for id in ids if id in result and result[id]])






class People(Base):
    def info(self, ids):
        pass

    def search(self):
        pass

    def popular(self):
        pass

    def fame(self):
        pass

    def occupations(self, lang=None, plural=None):
        if lang is None:
            lang = xbmc.getLanguage(xbmc.ISO_639_1)
        if lang not in ('en', 'ru'):
            lang = 'ru'
        result = [(x['occupation'], x[lang]) for x in OCCUPATIONS]
        if isinstance(plural, bool):
            i = 1 if plural else 0
            return [(x[0], x[1][i]) for x in result]
        return result





class KinoPoisk:
    def __init__(self):
        self.movies = Movies()
        self.people = People()



OCCUPATIONS = (
    {'occupation': 'director',        'en': (u'Director', u'Directors'),                'ru': (u'Режиссер', u'Режиссеры')},
    {'occupation': 'actor',           'en': (u'Actor', u'Actors'),                      'ru': (u'Актер', u'Актеры')},
    {'occupation': 'producer',        'en': (u'Producer', u'Producers'),                'ru': (u'Продюсер', u'Продюсеры')},
    {'occupation': 'producer_ussr',   'en': (u'Producer (USSR)', u'Producers (USSR)'),  'ru': (u'Директор фильма', u'Директоры фильма')},
    {'occupation': 'voice_director',  'en': (u'Voice Director', u'Voice Directors'),    'ru': (u'Режиссер дубляжа', u'Режиссеры дубляжа')},
    {'occupation': 'translator',      'en': (u'Translator', u'Translators'),            'ru': (u'Переводчик', u'Переводчики')},
    {'occupation': 'voice',           'en': (u'Voice', u'Voices'),                      'ru': (u'Актер дубляжа', u'Актеры дубляжа')},
    {'occupation': 'writer',          'en': (u'Writer', u'Writers'),                    'ru': (u'Сценарист', u'Сценаристы')},
    {'occupation': 'operator',        'en': (u'Operator', u'Operators'),                'ru': (u'Оператор', u'Операторы')},
    {'occupation': 'composer',        'en': (u'Composer', u'Composers'),                'ru': (u'Композитор', u'Композиторы')},
    {'occupation': 'design',          'en': (u'Designer', u'Designers'),                'ru': (u'Художник', u'Художники')},
    {'occupation': 'editor',          'en': (u'Editor', u'Editors'),                    'ru': (u'Монтажер', u'Монтажеры')}
)