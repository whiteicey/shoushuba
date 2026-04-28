from __future__ import annotations

import random
import re
import sys
import time

import requests
from lxml import etree

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

COMMENT_MESSAGES = [
    "别的不说，楼主就是给力啊",
    "谢谢楼主分享，祝搜书吧越办越好！",
    "看了LZ的帖子，我只想说一句很好很强大！",
    "太感谢了太感谢了太感谢了",
]

MAX_SUCCESSFUL_COMMENTS = 3
RETRY_DELAY = 65


class SoushubarClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._formhash = ""

    def run(self):
        self._login()
        thread_ids = self._fetch_thread_ids()
        if not thread_ids:
            raise RuntimeError("No thread IDs found for commenting")

        success_count = 0
        while success_count < MAX_SUCCESSFUL_COMMENTS:
            success_count = self._post_comment(success_count, thread_ids)
            if success_count < MAX_SUCCESSFUL_COMMENTS:
                time.sleep(RETRY_DELAY)

        print(f"签到完成，共成功评论 {success_count} 次")

    def _login(self):
        login_url = (
            f"{self.base_url}/member.php?mod=logging&action=login"
            f"&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1"
        )
        headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "application/x-www-form-urlencoded",
            "Pragma": "no-cache",
            "Referer": self.base_url,
        }
        data = {
            "username": self.username,
            "password": self.password,
            "quickforward": "yes",
            "handlekey": "ls",
        }

        resp = self.session.post(url=login_url, headers=headers, data=data)
        text = resp.text

        if "window.location.href=" in text:
            print(f"账号 {self.username} 登录成功", flush=True)
        elif "登录失败" in text or "密码错误" in text:
            print(f"[ERROR] 登录响应: {text[:500]}", flush=True)
            raise RuntimeError("登录失败，账号或密码错误")
        else:
            print(f"[ERROR] 登录响应(前500字): {text[:500]}", flush=True)
            raise RuntimeError(f"登录失败，未知错误，URL: {self.base_url}")

        self._fetch_coins()
        self._extract_formhash()

    def _fetch_coins(self):
        info_url = f"{self.base_url}/home.php?mod=spacecp&ac=credit&showcredit=1"
        resp = self.session.get(url=info_url)
        if resp.status_code != 200:
            raise RuntimeError(f"获取用户信息失败，状态码: {resp.status_code}")

        tree = etree.HTML(resp.text)
        elements = tree.xpath('//*[@id="ct"]/div[1]/div/ul[2]/li[1]/text()')

        if elements and "\xa0" in elements[0]:
            coins = elements[0].replace("\xa0", "").strip()
            print(f"当前银币数量: {coins}")
        else:
            raise RuntimeError("获取银币数量失败")

    def _extract_formhash(self):
        info_url = f"{self.base_url}/home.php?mod=spacecp&ac=credit&showcredit=1"
        resp = self.session.get(url=info_url)
        tree = etree.HTML(resp.text)
        formhash_elements = tree.xpath("//input[@name='formhash']/@value")
        if formhash_elements:
            self._formhash = formhash_elements[0]
        else:
            raise RuntimeError("获取 formhash 失败")

    def _fetch_thread_ids(self) -> list[str]:
        url = f"{self.base_url}/forum.php?mod=forumdisplay&fid=39&page=1"
        resp = self.session.get(url=url)
        tree = etree.HTML(resp.text)
        tables = tree.xpath("//table[@id='threadlisttableid']")
        if not tables:
            raise RuntimeError("未找到帖子列表")

        text = str(etree.tostring(tables[0]))
        tid_list = re.findall(r"tid=(\d+)&amp", text)
        return list(dict.fromkeys(tid_list))[10:]

    def _post_comment(self, count: int, thread_ids: list[str]) -> int:
        message = random.choice(COMMENT_MESSAGES)
        payload = {
            "formhash": self._formhash,
            "handlekey": "register",
            "noticeauthor": "",
            "noticetrimstr": "",
            "noticeauthormsg": "",
            "usesig": "1",
            "subject": "",
            "message": message.encode("gbk"),
        }

        tid = random.choice(thread_ids)
        comment_url = (
            f"{self.base_url}/forum.php?mod=post&infloat=yes"
            f"&action=reply&fid=100&extra=&tid={tid}"
            f"&replysubmit=yes&inajax=1"
        )

        resp = self.session.post(url=comment_url, headers={
            "Cache-Control": "no-cache",
            "Referer": self.base_url,
        }, data=payload)

        if "发布成功" in resp.text:
            count += 1
            self._show_coins()
            print(
                f"评论成功 [{count}/{MAX_SUCCESSFUL_COMMENTS}] "
                f"tid={tid} message={message}"
            )
            return count
        elif "回复限制" in resp.text:
            print("重复评论，跳过")
        elif "发布间隔" in resp.text:
            print("评论太快，等待中...")
        else:
            print(f"评论失败，状态码: {resp.status_code}")
            time.sleep(1)

        return count

    def _show_coins(self):
        try:
            info_url = f"{self.base_url}/home.php?mod=spacecp&ac=credit&showcredit=1"
            resp = self.session.get(url=info_url)
            tree = etree.HTML(resp.text)
            elements = tree.xpath('//*[@id="ct"]/div[1]/div/ul[2]/li[1]/text()')
            if elements and "\xa0" in elements[0]:
                coins = elements[0].replace("\xa0", "").strip()
                print(f"当前银币数量: {coins}")
        except Exception:
            pass
