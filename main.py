import time
from unittest import result
from urllib import request
from selenium import webdriver
from selenium.webdriver.common.by import By
import chromedriver_binary
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime
import sys

option = Options()
option.add_argument('--incognito')#シークレットウィンドウ
option.add_argument('--headless')#バックグラウンド起動
driver = webdriver.Chrome(options=option)   #

# コマンドライン引数を取り込み
try:
    SEARCH_WORD = str(sys.argv[1])
except:
    print("検索ワードは必須です")
    quit()

CLICK_TIMES = 0 if len(sys.argv) <= 2 else int(sys.argv[2])
NOW = datetime.now().strftime('%Y%m%d%H%M%S')
FILE_NAME = f"{SEARCH_WORD}_{NOW}.json"

result=[]
driver.get(f"https://news.yahoo.co.jp/search?ei=utf-8&p={SEARCH_WORD}")
time.sleep(1)
#指定した回数クリック
for _ in range(CLICK_TIMES):
    try:
        driver.find_element_by_class_name("button-height-large").click()
        time.sleep(1)
    except:
        break

html = driver.page_source.encode("utf-8")
bs = BeautifulSoup(html, "html.parser")

newsFeedItems = bs.find_all("li", {"class": "newsFeed_item", "class": "newsFeed_item-normal"})
links = []
for newsFeedItem in newsFeedItems:
    links.append(newsFeedItem.find("a").get("href"))

for link in links:
    print(f"link: {link}")
    try:
        res = requests.get(link)
        bs = BeautifulSoup(res.text, "html.parser")
        context={}
        context['url'] = link
        news = bs.find("article", {"id": "uamods"})
        context["title"] = news.find("header").text
        context["media"] = news.find("header").find("img", {"width": "170"}).get("alt")
        context["article"] = news.find("div", {"class": "article_body"}).text
        if news.find("li", {"class": "pagination_item-next"}) is not None:
            page=2
            while True:
                res = requests.get(link+f"?page={page}")
                bs = BeautifulSoup(res.text, "html.parser")
                if bs.find("article", {"id": "uamods"}).find("li", {"class": "pagination_item-next"}).find("a") is None:
                    break
                page+=1
        #コメント数がMINIMUM_COMMENTS以上のものならコメント収集をする
        comments_num=0
        try:
            comments_num=int(bs.find("article", {"id": "uamods"}).find("span", {"aria-hidden": "true"}).text)
        except AttributeError:
            pass
        if comments_num > 0:
            #コメント源のリンクを生成
            res = requests.get(link+"/comments")
            bs = BeautifulSoup(res.text, "html.parser")
            script_div = bs.find("div", {"class": "news-comment-plugin"})
            full_page_url = script_div["data-full-page-url"]
            topic_id = script_div["data-topic-id"]
            space_id = script_div["data-space-id"]
            commentURL = "https://news.yahoo.co.jp/comment/plugin/v1/full/?&sort=lost_points&order=desc&type=1"
            commentURL += f"&full_page_url={full_page_url}&topic_id={topic_id}&space_id={space_id}" #&page=1#こここんなまわりくどいことしなくて良くないか．

            page=1
            comments_all=[]
            while True:
                print(f"page:{page}")
                driver.get(commentURL+f"&page={page}")
                time.sleep(1)

                #サブコメントを表示させる
                buttons = driver.find_elements_by_class_name("btnView")
                for button in buttons:
                    try:
                        button.click()
                        time.sleep(1)
                    except:
                        pass

                html = driver.page_source.encode("utf-8")
                bs = BeautifulSoup(html, "html.parser")
                commentItems = bs.find_all("li", {"class": "commentListItem"})
                for commentItem in commentItems:
                    comment={}
                    try:
                        #メインコメントを取り出す．
                        root = commentItem.find("article", {"class": "root"})
                        main_comment = root.find("span", {"class": "cmtBody"}).text
                        gotGood = int(root.find("a", {"class": "agreeBtn"}).find("span", {"class": "userNum"}).text)
                        gotBad = int(root.find("a", {"class": "disagreeBtn"}).find("span", {"class": "userNum"}).text)
                        comment.update({"comment":main_comment,"good":gotGood,"bad":gotBad})
                        try:
                            #サブコメントを取り出す
                            subCommentItems = commentItem.find("ul", {"class":"response"}).find_all("li", {"class": "responseItem"})
                            subComments = []
                            for subCommentItem in subCommentItems:
                                try:
                                    subComment = subCommentItem.find("span", {"class": "cmtBody"}).text
                                    gotGood = int(subCommentItem.find("a", {"class": "agreeBtn"}).find("span", {"class": "userNum"}).text)
                                    gotBad= int(subCommentItem.find("a", {"class": "disagreeBtn"}).find("span", {"class": "userNum"}).text)
                                    subComments.append({"comment":subComment,"good":gotGood,"bad":gotBad})
                                except:
                                    pass
                            comment.update({"subComments":subComments})
                        except:
                            pass
                        finally:
                            comments_all.append(comment)
                    except:
                        pass
                next=bs.find("li", {"class": "next"})
                next_link=next.find("a")
                if next_link is None:
                    print("break")
                    break
                page += 1
            context['comments'] = comments_all
        result.append(context)

        with open(f"../json/{FILE_NAME}", 'w') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
    except:
        print("do not work in this url")
        continue

driver.close()
driver.quit()
