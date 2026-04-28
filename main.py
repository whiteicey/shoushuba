#!/usr/bin/env python3
import sys

from soushubar.checkin import SoushubarClient
from soushubar.config import Config
from soushubar.url_finder import find_current_url


def main():
    config = Config.load()

    if not config.has_credentials:
        print("[ERROR] 请配置账号密码。")
        print("  方式一: 设置环境变量 SOUSHUBA_USERNAME, SOUSHUBA_PASSWORD")
        print("  方式二: 在当前目录下创建 config.txt，格式为:")
        print("    https://www.example.soushu2028.com/")
        print("    username")
        print("    password")
        sys.exit(1)

    if not config.has_url:
        print(f"[INFO] 正在从 {config.entry_url} 发现新URL...", flush=True)
        config.base_url = find_current_url(config.entry_url)
        config.save_url()
        print(f"[INFO] 发现新URL: {config.base_url}", flush=True)

    client = SoushubarClient(
        base_url=config.base_url,
        username=config.username,
        password=config.password,
    )
    client.run()


if __name__ == "__main__":
    main()
