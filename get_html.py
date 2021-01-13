# get html
from os import error
from re import L
from sys import path
from bs4.builder import HTML
import requests
import time
from pathlib import Path
from typing import Dict,List
from bs4 import BeautifulSoup, element, BeautifulStoneSoup
import random
import datetime
import json
import pandas as pd
import csv
#import xml.etree.ElementTree as ET


# ディレクトリ名からディレクトリのパス(str)を返す
# name: ディレクトリ名
# prefix: ローカル環境とリモート環境(コラボ)でのパスの違いを管理
def dirsName(name: str, prefix: str):
    return f"{prefix}data/{name}/"


# ファイル名から自動取得用のファイルのパス(str)を返す
# name: ファイル名
# prefix: ローカル環境とリモート環境(コラボ)でのパスの違いを管理
# extension: ファイルの拡張子
def auto_filename(name: str, prefix: str, extension: str = 'txt'):
    return f"{dirsName(name, prefix)}auto_list.{extension}"

# ファイル名から自動取得時の404リスト用のファイルのパス(str)を返す
# name: ファイル名
# prefix: ローカル環境とリモート環境(コラボ)でのパスの違いを管理
# extension: ファイルの拡張子
def auto_404filename(name: str, prefix: str, extension: str = 'txt'):
    return f"{dirsName(name, prefix)}auto_404list.{extension}"

# ディレクトリ名とファイル名からファイルのパス(str)を返す
# name: ディレクトリ名(ドメイン)
# prefix: ローカル環境とリモート環境(コラボ)でのパスの違いを管理
# id: ファイル名(記事id)
# extension: ファイルの拡張子
def fileName(name: str, prefix: str, id: str, extension: str="html")->str:
    return dirsName(name, prefix) + id.translate(str.maketrans('\\:*?"<>|/.','__________')) \
        + "." + extension #idの階層がローカルの階層にならないように'/'を'_'に変換,拡張子付きのサイト用に'.'を'_'に変換

# 記事のurlと記事のidからGET用のurlを返す
# article_url: 記事アクセス用のurlのid以外の共通する部分
# article_id: 記事id
def urlName(article_url: str, article_id: str) -> str:
    return article_url + article_id


# dateから年月日をyyyy-mm-dd形式で返す
# date: datetime.date型
def yyyymmdd(date: datetime.date):
    yyyy = f"0000{date.year}"[-4:]
    mm = f"00{date.month}"[-2:]
    dd = f"00{date.day}"[-2:]
    return f"{yyyy}-{mm}-{dd}"


# ディレクトリ構造に格納されたhtmlファイルを再帰的に取得
# tohohoは全記事をダウンロードして階層構造で保存しているため
# root: 記事の親のパス(Path)
def get_all_path(root: Path):
    if not root.is_dir():
        return
    res = []
    for x in root.iterdir():
        if x.is_dir():
            res.extend(get_all_path(x))
        elif x.suffix == '.htm' or x.suffix == '.html':
            res.append(x)
    return res


# auto_type毎にauto_num個をauto_urlもしくは保存先からhtmlを取得
# 【注意事項】一覧取得の際にfor分を回す場合は、対象サイトの規約(robots.txtなど)を読んだうえで必ずsleepを挟み、できれば想定外(200以外など)のresponse場合breakするようにしてください
# また小さいテストをして動作を確認してから動かしてください
# auto_url: url一覧を自動取得する用のurl、auto_url + 'id'で記事一覧(大抵1ページごとに20記事程度)をGETする対象のURLを取得
# auto_type: 自動取得の種類の区別、現状実質全て区別しているが将来的にまとめるかもしれない
# auto_num: 返り値の自動取得するurl数
# lower_bound: 'id'が数字の場合、idの下限
# upper_bound: 'id'が数字の場合、idの上限、
# idを[lower_bound,uppper_bound)で回すが200以外が返ってくると止めるようにするため、厳密に指定する必要はない
# path_prefix: ローカル環境とリモート環境(コラボ)でのパスの違いを管理
def autoGetUrl(auto_url: str, auto_type: str, auto_num: int, upper_bound: int, lower_bound: int, path_prefix: str) -> \
List[str]:
    res: List[str] = []  # 返り値
    store: List[str] = []  # urlを全列挙する際の格納先
    if auto_type == 'sejuku':
        filename = auto_filename(auto_type, path_prefix)  # ローカル保存用のパス(str)
        file_path = Path(filename)  # ローカル保存用のパス(Path)
        print(filename)
        print(file_path.exists())
        if not file_path.exists():  # ローカルで保存していなかった場合
            for i in range(lower_bound, upper_bound):  # idを[lower_bound,uppper_bound)で回す
                auto_urlname = auto_url + str(i)
                auto_html = requests.get(auto_urlname)
                if auto_html.status_code != 200:  # 200以外のステータスの場合終了する(記事一覧のページ番号末尾まで取得)
                    print(f'{auto_type} finish {i}')
                    break
                time.sleep(3)
                auto_html_code = auto_html.content.decode('utf-8')  # getしたhtml(string)
                auto_soup = BeautifulSoup(auto_html_code)
                tmp = auto_soup.select(".main-box-inside .image > a")  # .main-box-insideクラスの内側のimageクラスの子のaタグを抽出
                print(i, len(tmp))
                for v in tmp:
                    store.append(v.attrs["href"])
            dir_path = Path(dirsName(auto_type, path_prefix))
            if not dir_path.exists():
                dir_path.mkdir(mode=0o777, parents=True, exist_ok=False)  # ディレクトリを作成
            with open(filename, mode='w', encoding='utf-8') as f:
                for v in store:
                    f.write(v + '\n')
        else:
            with file_path.open(mode='r') as f:
                r = f.read()
                store = r.split('\n')[0:-1]
        sum = len(store)
        if sum < auto_num:
            raise Exception(f'number of all articles is less than auto_num:{auto_num}')
        random.shuffle(store)
        extracted_url = store[0:auto_num]
        for v in extracted_url:
            res.append(v)
    elif auto_type == 'techacademy':
        filename = auto_filename(auto_type, path_prefix)  # ローカル保存用のファイル名
        file_path = Path(filename)
        print(filename)
        print(file_path.exists())
        if not file_path.exists():
            for i in range(lower_bound, upper_bound):
                auto_urlname = auto_url + str(i)
                auto_html = requests.get(auto_urlname)
                if auto_html.status_code != 200:
                    print(f'{auto_type} finish {i}')
                    break
                time.sleep(3)
                auto_html_code = auto_html.content.decode('utf-8')  # getしたhtml(string)、後で知ったがauto_html.textでよい
                auto_soup = BeautifulSoup(auto_html_code)
                tmp = auto_soup.select(".content .entry-eyecatch > a")  # .main-box-insideクラスの内側のimageクラスの子のaタグを抽出
                print(i, len(tmp))
                for v in tmp:
                    store.append(v.attrs["href"])
            dir_path = Path(dirsName(auto_type, path_prefix))
            if not dir_path.exists():
                dir_path.mkdir(mode=0o777, parents=True, exist_ok=False)  # ディレクトリを作成
            with open(filename, mode='w', encoding='utf-8') as f:
                for v in store:
                    f.write(v + '\n')
        else:
            with file_path.open(mode='r') as f:
                r = f.read()
                store = r.split('\n')[0:-1]
        sum = len(store)
        if sum < auto_num:
            raise Exception(f'number of all articles is less than auto_num:{auto_num}')
        random.shuffle(store)
        extracted_url = store[0:auto_num]
        for v in extracted_url:
            res.append(v)
    elif auto_type == 'qiita':  # いいね数apiからdaily ranking top 30を取得して累計3000(重複を許さず)に到達するまで一日ずつ遡る
        filename = auto_filename(auto_type, path_prefix)  # ローカル保存用のファイル名
        file_path = Path(filename)
        print(filename)
        print(file_path.exists())
        ub = 3000  # 取得urlの上限
        url_set = set()  # 重複を許さずにurlを格納するデータ構造
        if not file_path.exists():
            # APIがYYYY-MM-DD形式
            date = datetime.datetime.today() - datetime.timedelta(
                days=2)  # 一昨日の日付から遡って取得(昨日からだと実行するタイミング次第(日付変更直後)で存在しない場合がある)
            stop = datetime.datetime(2018, 9, 23)  # 日付の制限(これより前は存在しない)
            while date >= stop and len(url_set) <= ub:
                ymd = yyyymmdd(date)  ## YYYY-MM-DD形式(0埋め)
                print(f"date:{ymd}", end='\t')
                auto_urlname = auto_url + ymd
                response = requests.get(auto_urlname)  # get API
                if response.status_code != 200:  # 200以外だったら終了
                    print(f'{auto_type} finish {date}')
                    break
                time.sleep(5)
                json_data = json.loads(response.text)['data']  # jsonを読み込んで、'data'を抽出
                for v in json_data:
                    url_set.add(v["url"])  # urlを抽出、重複を許さず
                print(f"size:{len(url_set)}")  # 経過出力
                date -= datetime.timedelta(days=1)  # 一日遡る
            store = list(url_set)
            dir_path = Path(dirsName(auto_type, path_prefix))
            if not dir_path.exists():
                dir_path.mkdir(mode=0o777, parents=True, exist_ok=False)  # ディレクトリを作成
            with open(filename, mode='w', encoding='utf-8') as f:
                for v in store:
                    f.write(v + '\n')
        else:
            with file_path.open(mode='r') as f:
                r = f.read()
                store = r.split('\n')[0:-1]
        sum = len(store)  # 記事一覧の個数
        if sum < auto_num:  # 記事一覧の個数よりも取得個数が多い場合エラー
            raise Exception(f'number of all articles is less than auto_num:{auto_num}')
        random.shuffle(store)
        extracted_url = store[0:auto_num]
        for v in extracted_url:
            res.append(v)
    elif auto_type == 'zenn':  # 記事一覧から全記事のurlと☆数を取得してall time rankingを作成する
        filename = auto_filename(auto_type, path_prefix, 'csv')  # ローカル保存用のファイル名
        file_path = Path(filename)
        print(filename)
        print(file_path.exists())
        url_set = dict()  # 取得ごとに3秒休むと、記事が新規追加されて一覧のページがずれるので、重複が発生する。そのため重複を除去するデータ構造
        if not file_path.exists():  # all_list.csv(☆数トップ3000の記事のurl一覧)が存在しない場合、all_list.csvを作成する
            for i in range(lower_bound, upper_bound):  # 全記事のurlと☆数を抽出
                auto_urlname = auto_url + str(i)
                auto_html = requests.get(auto_urlname)
                if auto_html.status_code != 200:
                    print(f'{auto_type} finish {i}')
                    break
                time.sleep(3)
                auto_html_code = auto_html.text  # getしたhtml(string)
                auto_soup = BeautifulSoup(auto_html_code)
                if len(auto_soup.select('.error_status__1HzcU')) > 0:  # 404の表示
                    break
                for article in auto_soup.select(".ArticleListItem_container__1TunJ"):
                    tmp = []
                    link = article.select(".ArticleListItem_link__WbSan")  # ArticleListItem_link__WbSanクラスを抽出(リンク用)
                    like = article.select(".ArticleListItem_like__3BdyY")  # ArticleListItem_like__3BdyYクラスを抽出(☆用)
                    tmp.append("https://zenn.dev" + link[0].attrs["href"])
                    if len(like) == 0:
                        tmp.append(0)
                    else:
                        tmp.append(int(like[0].text))
                    url_set[tmp[0]] = tmp[1]
                print(i)
            for v in url_set:  # [[url,☆数],...]で二重配列
                tmp = []
                tmp.append(v)
                tmp.append(url_set[v])
                store.append(tmp)
            store.sort(key=lambda x: x[1], reverse=True)  # ☆数の多い順でソート
            dir_path = Path(dirsName(auto_type, path_prefix))
            if not dir_path.exists():
                dir_path.mkdir(mode=0o777, parents=True, exist_ok=False)  # ディレクトリを作成
            with open(filename, mode='w', encoding='utf-8') as f:
                f.write('url, like\n')
                for v in store:
                    f.write(f'{v[0]}, {v[1]}\n')  # ☆数で閾値を設けたくなるかもしれないので保存

        store = pd.read_csv(filename)['url'].to_list()[:1000]  # 上位1000位まで
        sum = len(store)
        if sum < auto_num:
            raise Exception(f'number of all articles is less than auto_num:{auto_num}')
        random.shuffle(store)
        extracted_url = store[0:auto_num]
        for v in extracted_url:
            res.append(v)
    elif auto_type == 'tohoho':
        # とほほは全データで10MB程度なのでディレクトリ構造ごとすべて保存していることを前提とする
        root_path = Path(dirsName('www_20181111', path_prefix))
        # root直下のhtmlファイルはホームページの案内等なので、root下のディレクトリ以下にあるhtmlファイルを抽出
        dir_list = [x for x in root_path.iterdir() if root_path.is_dir() and x.is_dir()]
        path_list = []
        for x in dir_list:
            path_list.extend(get_all_path(x))
        print(len(path_list))  # 742個
        if len(path_list) < auto_num:
            raise Exception(f'number of all articles is less than auto_num:{auto_num}')
        random.shuffle(path_list)
        extracted_url = path_list[0:auto_num]
        for v in extracted_url:
            res.append(v)
    elif auto_type == 'qastack':
        filename = auto_filename(auto_type, path_prefix)  # ローカル保存用のパス(str)
        file_path = Path(filename)  # ローカル保存用のパス(Path)
        if not file_path.exists():
            sitemap_programming = auto_url + 'sitemap/questions/10.xml'  # TODO: カテゴリ展開時に拡張する
            xml = requests.get(sitemap_programming)
            if xml.status_code != 200:  # サイトマップ取得時に異常
                print(f'{auto_type} finished in getting XML')
            xml_code = xml.content.decode('utf-8')
            xml_soup = BeautifulSoup(xml_code)
            links = xml_soup.select('urlset > url > loc')
            store = [link.text for link in links]
            with file_path.open(mode='w',encoding='utf-8') as f:
                for v in store:
                    f.write(v+'\n')
        else:
            with file_path.open(mode='r',encoding='utf-8') as f:
                store = f.read().split('\n')[:-1]
        #print("stored:", store[0])
        print(len(store))
        random.shuffle(store)
        if len(store) < auto_num:
            raise Exception(f'number of all articles is less than auto_num:{auto_num}')
        extracted_url = store[0:auto_num]
        for v in extracted_url:
            res.append(v)
        #print(res)
    elif auto_type=='cpprefjp' or auto_type=='note.nkmk.me' or auto_type=='dbonline' or auto_type=='javadrive' or auto_type=='deepage': # sitemap.xmlからall_listを作成
        filename = auto_filename(auto_type, path_prefix)
        file_path = Path(filename)
        if not file_path.exists():
            dirname = Path(dirsName(auto_type,path_prefix))
            if not dirname.exists():
                dirname.mkdir(mode=0o777,parents=True,exist_ok=False)
            auto_xml = requests.get(auto_url) # get sitemap xml
            if auto_xml.status_code != 200:
                raise Exception(f'status code: {auto_xml.status_code}')
            time.sleep(3)
            xml_text = auto_xml.text
            auto_soup = BeautifulStoneSoup(xml_text,features="xml") # parse xml from string
            all_loc = auto_soup.findAll('loc') # <urL>下にある<loc>を全て抽出
            with file_path.open(mode='w',encoding='utf-8') as f:
                for v in all_loc:
                    f.write(v.text+'\n')
            print(len(res))
        with file_path.open(mode='r',encoding='utf-8') as f:
            r = f.read()
            store = r.split('\n')[:-1]
        sum = len(store)
        if sum < auto_num:
            raise Exception(f'number of all articles:{sum} is less than auto_num:{auto_num}')
        random.shuffle(store)
        extracted_url = store[0:auto_num]
        for v in extracted_url:
            res.append(v)
    elif auto_type=='jastackoverflow' or auto_type=='jastackoverflow_bad':
        filename = auto_filename(auto_type, path_prefix)  # ローカル保存用のパス(str)
        file_path = Path(filename)  # ローカル保存用のパス(Path)
        # ディレクトリにja_stack_overflow.csvがあることを前提とする
        if not file_path.exists():
            dirname = Path(dirsName(auto_type,path_prefix))
            if not dirname.exists():
                dirname.mkdir(mode=0o777,parents=True,exist_ok=False)
            # CSVからURLを取得
            # CSVは https://data.stackexchange.com/ja/query/1348894/post-with-good-answer
            # CSVは https://data.stackexchange.com/ja/query/1356039/post-with-bad-answer
            with Path(dirsName(auto_type, path_prefix)+"ja_stack_overflow.csv").open(mode='r',encoding='utf-8', newline='') as csvfile:
                with file_path.open(mode='w',encoding='utf-8') as f:
                    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                    index = 0
                    for row in spamreader:
                        index += 1
                        if index==1:
                            continue
                        f.write(f'https://ja.stackoverflow.com/questions/{row[0]}\n')
                        #print(', '.join(row))
        with file_path.open(mode='r',encoding='utf-8') as f:
            r = f.read()
            store = r.split('\n')[:-1]
        sum = len(store)
        if sum < auto_num:
            raise Exception(f'number of all articles:{sum} is less than auto_num:{auto_num}')
        random.shuffle(store)
        extracted_url = store[0:auto_num]
        for v in extracted_url:
            res.append(v)
    elif auto_type=='techteacher':
        filename = auto_filename(auto_type, path_prefix)  # ローカル保存用のパス(str)
        file_path = Path(filename)  # ローカル保存用のパス(Path)
        print(filename)
        print(file_path.exists())
        if not file_path.exists():  # ローカルで保存していなかった場合
            # 1頁目がページングされてない
            first_url = auto_url[:auto_url.find('page')]
            auto_html = requests.get(first_url)
            time.sleep(3)
            auto_html_code = auto_html.text  # getしたhtml(string)
            auto_soup = BeautifulSoup(auto_html_code)
            tmp = auto_soup.select(".post-list-mag .post-list-item > a")  # .post-list-magクラスの内側のpost-list-itemクラスの子のaタグを抽出
            for v in tmp:
                    store.append(v.attrs["href"])
            print(1, len(tmp))
            for i in range(lower_bound, upper_bound):  # idを[lower_bound,uppper_bound)で回す
                auto_urlname = auto_url + str(i)
                auto_html = requests.get(auto_urlname)
                if auto_html.status_code != 200:  # 200以外のステータスの場合終了する(記事一覧のページ番号末尾まで取得)
                    print(f'{auto_type} finish {i}')
                    break
                time.sleep(3)
                auto_html_code = auto_html.text  # getしたhtml(string)
                auto_soup = BeautifulSoup(auto_html_code)
                tmp = auto_soup.select(".post-list-mag .post-list-item > a")  # .post-list-magクラスの内側のpost-list-itemクラスの子のaタグを抽出
                print(i, len(tmp))
                for v in tmp:
                    store.append(v.attrs["href"])
            dir_path = Path(dirsName(auto_type, path_prefix))
            if not dir_path.exists():
                dir_path.mkdir(mode=0o777, parents=True, exist_ok=False)  # ディレクトリを作成
            with open(filename, mode='w', encoding='utf-8') as f:
                for v in store:
                    f.write(v + '\n')
        else:
            with file_path.open(mode='r') as f:
                r = f.read()
                store = r.split('\n')[0:-1]
        sum = len(store)
        if sum < auto_num:
            raise Exception(f'number of all articles is less than auto_num:{auto_num}')
        random.shuffle(store)
        extracted_url = store[0:auto_num]
        for v in extracted_url:
            res.append(v)
    elif auto_type=='headboost':  # sitemap.xmlからall_listを作成, 画像のurlを除外
        filename = auto_filename(auto_type, path_prefix)
        file_path = Path(filename)
        if not file_path.exists():
            dirname = Path(dirsName(auto_type,path_prefix))
            if not dirname.exists():
                dirname.mkdir(mode=0o777,parents=True,exist_ok=False)
            auto_xml = requests.get(auto_url) # get sitemap xml
            if auto_xml.status_code != 200:
                raise Exception(f'status code: {auto_xml.status_code}')
            time.sleep(3)
            xml_text = auto_xml.text

            auto_soup = BeautifulStoneSoup(xml_text,features="lxml-xml") # parse xml from string
            all_loc = auto_soup.select('url > loc') # <urL>下にある<loc>を全て抽出
            with file_path.open(mode='w',encoding='utf-8') as f:
                for v in all_loc:
                    f.write(v.text+'\n')
            print(len(res))
        with file_path.open(mode='r',encoding='utf-8') as f:
            r = f.read()
            store = r.split('\n')[:-1]
        sum = len(store)
        if sum < auto_num:
            raise Exception(f'number of all articles:{sum} is less than auto_num:{auto_num}')
        random.shuffle(store)
        extracted_url = store[0:auto_num]
        for v in extracted_url:
            res.append(v)
    return res


# ファイル名がfilenameのものが存在しない場合、urlで指定した記事を取得し、filenameに保存し、html(str)を返す
# 存在する場合、html(str)を返す
# url: 取得するURL(str)
# filename: ファイルのパス(str)
def getHtmlbyURL(url: str, filename: str) -> str:
    res: str
    file_path = Path(filename)
    if not file_path.exists(): # 1回getしたらローカルに保存して、複数回getしない
        html = requests.get(url) # getしたhtml(bytes)
        if html.status_code!=200:
            time.sleep(6)  # インターバル
            raise Exception(f'url: {url}, status code: {html.status_code}')
        html_code = html.content.decode('utf-8') #getしたhtml(string)
        dir_path = file_path.parent
        if not dir_path.exists():
            dir_path.mkdir(mode=0o777, parents=True, exist_ok=False)  # ディレクトリを作成
        with open(filename, mode='w', encoding='utf-8') as f:
            f.write(html_code)  # ローカルに保存
        time.sleep(6)  # インターバル
    with open(filename, mode='r', encoding='utf-8') as f:
        html_code = f.read()
        res = html_code
    return res


# get html段階のメインの実行関数
# ドメイン毎にhtmlを取得し、返す。保存するなどして高速化を図っている
# 返り値の型
# {
#   "{domain}":
#       {
#           "texts":[] // html(str)の配列
#           "label" 0 or 1 // 1がgood, 0がbad
#       }
# }
def getHTML() -> Dict[str, List[str]]:
    # ドメイン毎の取得用の各種データ
    # name: 一意なid
    # domain: ドメインのルートurl
    # article_url: 記事アクセス用のurlのid以外の共通する部分
    # auto_url: 自動取得の際のurl
    # auto_type: 自動取得の種類
    # upper_bound,lower_bound: ページングされているタイプのauto_urlのページの範囲 
    # label: 0がbad,1がgood
    contents = [
        {
            "name": "sejuku",
            "domain": "https://www.sejuku.net/",
            "article_url": "https://www.sejuku.net/blog/",
            "auto_url": "https://www.sejuku.net/blog/archive/page/",
            "auto_type": "sejuku",
            "upper_bound": 200,  # 200以外が返ってくるまで続ける、そのうえで(安全性のために)上限をつける
            "lower_bound": 2,
            "label": 0,  # bad
        },
        {
            "name": "techacademy",
            "domain": "https://techacademy.jp/",
            "article_url": "https://techacademy.jp/magazine/",
            "auto_url": "https://techacademy.jp/magazine/category/programming/page/",
            "auto_type": "techacademy",
            "upper_bound": 200,  # 200以外が返ってくるまで続ける、そのうえで(安全性のために)上限をつける
            "lower_bound": 2,
            "label": 0,  # bad
        },
        {
            "name": "qiita",
            "domain": "https://qiita.com/",
            "article_url": "https://qiita.com/",
            "auto_url": "https://us-central1-qiita-trend-web-scraping.cloudfunctions.net/qiitaScraiping/daily/",
            "auto_type": "qiita",
            "upper_bound": 0,
            "lower_bound": 0,
            "label": 1,  # good
        },
        {
            "name": "zenn",
            "domain": "https://zenn.dev/",
            "article_url": "https://zenn.dev/",  # https://zenn.dev/[userid]/articles/[articleid]
            "auto_url": "https://zenn.dev/articles?page=",
            "auto_type": "zenn",
            "upper_bound": 120,
            "lower_bound": 2,
            "label": 1,  # good
        },
        {
            "name": "tohoho",
            "domain": "http://www.tohoho-web.com/",
            "auto_url": "",
            "auto_type": "tohoho",
            "upper_bound": 0,
            "lower_bound": 0,
            "label": 1,  # good
        },
        {
            "name": "qastack",
            "domain": "https://qastack.jp/",
            "article_url": "https://qastack.jp/",
            "auto_url": "https://qastack.jp/",  # https://qastack.jp/[category]/[num]/[title]
            "auto_type": "qastack",
            "upper_bound": 0,
            "lower_bound": 0,
            "label": 0,  # bad
        },
        {
            "name": "cpprefjp",
            "domain": "https://cpprefjp.github.io/",
            "article_url": "https://cpprefjp.github.io/",
            "auto_url": "https://cpprefjp.github.io/sitemap.xml",
            "auto_type": "cpprefjp",
            "upper_bound": 0,
            "lower_bound": 0,
            "label": 1, # good
        },
        {
            "name": "jastackoverflow",
            "domain": "https://ja.stackoverflow.com/",
            "article_url": "https://ja.stackoverflow.com/questions/", #https://ja.stackoverflow.com/questions/[ID]/
            "auto_url": "",
            "auto_type": "jastackoverflow",
            "upper_bound": 0,
            "lower_bound": 0,
            "label": 1, # good
        },
        {
            "name": "jastackoverflow_bad",
            "domain": "jastackoverflow_bad",
            "article_url": "https://ja.stackoverflow.com/questions/", #https://ja.stackoverflow.com/questions/[ID]/
            "auto_url": None,
            "auto_type": "jastackoverflow_bad",
            "upper_bound": 0,
            "lower_bound": 0,
            "label": 0, # bad
        },
        {
            "name": "dbonline",
            "domain": "https://www.dbonline.jp/",
            "article_url": "https://www.dbonline.jp/",
            "auto_url": "https://www.dbonline.jp/sitemap.xml",
            "auto_type": "dbonline",
            "upper_bound": 0,
            "lower_bound": 0,
            "label": 1, # good
        },
        {
            "name": "note.nkmk.me",
            "domain": "https://note.nkmk.me/",
            "article_url": "https://note.nkmk.me/",
            "auto_url": "https://note.nkmk.me/sitemap.xml",
            "auto_type": "note.nkmk.me",
            "upper_bound": 0,
            "lower_bound": 0,
            "label": 1, # good
        },
        {
            "name": "techteacher",
            "domain": "https://www.tech-teacher.jp/",
            "article_url": "https://www.tech-teacher.jp/blog/",
            "auto_url": "https://www.tech-teacher.jp/blog/category/programming/page/",
            "auto_type": "techteacher",
            "upper_bound": 15,
            "lower_bound": 2,
            "label": 0, # bad
        },
        {
            "name": "deepage",
            "domain": "https://deepage.net/",
            "article_url": "https://deepage.net/",
            "auto_url": "https://deepage.net/sitemap.xml",
            "auto_type": "deepage",
            "upper_bound": 0,
            "lower_bound": 0,
            "label": 0, # bad
        },
        {
            "name": "javadrive",
            "domain": "https://www.javadrive.jp/",
            "article_url": "https://www.javadrive.jp/",
            "auto_url": "https://www.javadrive.jp/sitemap.xml",
            "auto_type": "javadrive",
            "upper_bound": 0,
            "lower_bound": 0,
            "label": 0, # bad
        },
        {
            "name": "headboost",
            "domain": "https://www.headboost.jp/",
            "article_url": "https://www.headboost.jp/",
            "auto_url": "https://www.headboost.jp/sitemap.xml",
            "auto_type": "headboost",
            "upper_bound": 0,
            "lower_bound": 0,
            "label": 0, # bad
        },
    ]
    # 環境指定用変数、パスの先頭部分を変更する。わざわざ実行時引数で指定するの面倒だったので変数で指定、各自の環境に合わせて追加・変更してください
    # environment = 'local'
    # environment = 'debug'
    environment = 'share'
    if environment == 'local':
        path_prefix = './'
    elif environment == 'debug':
        path_prefix = './scraping/'
    else:
        path_prefix = '/content/drive/Shareddrives/システム設計構築演習/'

    # デバッグで追加したcontentだけ実行したい時用(残したままだと以降のランダム取得がずれるので、注意)
    # content = contents[4]
    # urls = autoGetUrl(content["auto_url"],content["name"],10,content["upper_bound"],content["lower_bound"],path_prefix)
    # tmp = getHtmlbyURL(urls[0],fileName(content['name'],path_prefix,urls[0][len("https://qiita.com/"):],))
    # print(len(tmp))

    res = {}  # 返り値
    number_of_get_html = 53  # ドメイン毎のhtml取得数
    #number_of_get_html = 149  # ドメイン毎のhtml取得数
    #number_of_get_html = 740  # ドメイン毎のhtml取得数
    for content in contents:
        random.seed(0)
        print(content)
        res[content['domain']] = {}
        res[content['domain']]['texts'] = []
        res[content['domain']]['label'] = content['label']
        url_set = set() # ドメイン毎のhtmlが取得できたurl集合(while2周目以降で重複を除去,404の割合が十分に低いと仮定)
        while number_of_get_html > len(url_set):
            urls = autoGetUrl(content["auto_url"], content["name"], number_of_get_html - len(url_set), content["upper_bound"],
                            content["lower_bound"], path_prefix)
            if content["name"] == 'tohoho':  # tohohoは全ファイル保存済
                for i, url in enumerate(urls):
                    if environment != 'share':
                        print(f'{i}, {datetime.datetime.today()}: {url._str}')
                    with url.open(encoding='utf-8') as f:
                        res[content['domain']]['texts'].append(f.read())
                    url_set.add(url)
            else:
                auto404path = Path(auto_404filename(content['name'],path_prefix))
                if content["name"]=='zenn':
                    autopath = Path(auto_filename(content['name'],path_prefix,'csv'))
                else:
                    autopath = Path(auto_filename(content['name'],path_prefix))
                with autopath.open(mode='r',encoding='utf-8') as f:
                    alllist = f.read().split('\n')[:-1]
                    all_list = str(alllist)
                if auto404path.exists():
                    with auto404path.open(mode='r',encoding='utf-8') as f:
                        list404 = set(f.read().split('\n')[:-1])
                        l = len(all_list) # all_listの個数
                        if l-len(list404) < number_of_get_html: # all_listの内404以外の個数が取得数を超えていた場合
                            raise Exception(f'number of all articles:{l-len(list404)} is less than number_of_get_html:{number_of_get_html}')
                else:
                    list404 = set()
                for i, url in enumerate(urls):
                    if environment != 'share':
                        print(f'{i}, {datetime.datetime.today()}: {url}')
                    filename = fileName(content["name"], path_prefix, url[len(content["article_url"]):])
                    if url in list404:
                        print(f'{url} include 404 list.')
                        continue
                    if url in url_set:
                        print(f'{url} include used list.')
                        continue
                    try: # 404のときエラー
                        html_code = getHtmlbyURL(url, filename)
                        res[content['domain']]['texts'].append(html_code)
                    except Exception: # 404リストに加える
                        print(f"detect 404 not found.")
                        with auto404path.open(mode='a',encoding='utf-8') as f:
                            f.write(url+'\n')
                        list404.add(url)
                    else:
                        url_set.add(url)
    return res


if __name__ == "__main__":
    # random.seed(0)
    # autoGetHtml('https://www.sejuku.net/blog/archive/page/', 'sejuku', 3, 3, 2)
    randomState = random.getstate()
    gotHTML = getHTML()
    # 動作確認
    for v in gotHTML:
        print(v)
        if gotHTML[v]['label']==1:
            print('good')
        else:
            print('bad')
        print(len(gotHTML[v]['texts']))
    del gotHTML
    random.setstate(randomState)
