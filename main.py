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

option = Options()
option.add_argument('--incognito')#シークレットウィンドウ
option.add_argument('--headless')#バックグラウンド起動
driver = webdriver.Chrome(options=option)   #

# def constants
SEARCH_WORD = '大谷翔平'
MINIMUM_COMMENTS = 1
#CLICK_TIMES = 1 #min:0 buttonがクリックとごとに変化するため非対応．

result=[]
driver.get('https://news.yahoo.co.jp/search?ei=utf-8&p='+SEARCH_WORD)
time.sleep(1)
#element = driver.find_element_by_css_selector(cssセレクタ)
#for _ in range(CLICK_TIMES):
#    element.click()
#    time.sleep(1)
html = driver.page_source.encode("utf-8")
bs = BeautifulSoup(html, "html.parser")

newsFeedItems = bs.find_all("li", {"class": "newsFeed_item", "class": "newsFeed_item-normal"})
links = []
for newsFeedItem in newsFeedItems:
    links.append(newsFeedItem.find("a").get("href"))

for link in links:
    res = requests.get(link)
    bs = BeautifulSoup(res.text, "html.parser")
    comments_num=int(bs.find("span", {"class": "sc-fOICqy"}).text)
    if comments_num >= MINIMUM_COMMENTS:
        context={}
        context['url'] = link
        news = bs.find("article", {"id": "uamods"})
        context["title"] = news.find("header").text
        context["article"] = news.find("div", {"class": "article_body"}).text
        res = requests.get(link+"/comments")
        bs = BeautifulSoup(res.text, "html.parser")
        script_div = bs.find("div", {"class": "news-comment-plugin"})
        full_page_url = script_div["data-full-page-url"]
        topic_id = script_div["data-topic-id"]
        space_id = script_div["data-space-id"]
        commentURL = "https://news.yahoo.co.jp/comment/plugin/v1/full/?&sort=lost_points&order=desc&type=1"
        commentURL += f"&full_page_url={full_page_url}&topic_id={topic_id}&space_id={space_id}" #&page=1
        page=1
        comments_all=[]
        while True:
            res = requests.get(commentURL+f"&page={page}")
            bs = BeautifulSoup(res.text, "html.parser")
            commentItems = bs.find_all("li", {"class": "commentListItem"})
            for commentItem in commentItems:
                try:
                    comment = commentItem.find("span", {"class": "cmtBody"}).text
                    gotGood = commentItem.find("a", {"class": "agreeBtn"}).find("span", {"class": "userNum"}).text
                    gotBad= commentItem.find("a", {"class": "disagreeBtn"}).find("span", {"class": "userNum"}).text
                    comments_all.append({"comment":comment,"good":gotGood,"bad":gotBad})
                except:
                    pass
            next=bs.find("li", {"class": "next"})
            next_link=next.find("a")
            if next_link is None:
                print("break!")
                break
            page += 1
        context['comments'] = comments_all
        result.append(context)

with open(f"./json/{SEARCH_WORD}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json", 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

driver.close()
driver.quit()

#TODO: subコメントはseleniumでないと取得できない．またcmtbodyはメインサブで共通なので，そこの対応がいるだろう．