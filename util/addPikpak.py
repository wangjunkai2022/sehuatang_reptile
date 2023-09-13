import json
import os

from pikpakapi import PikPakApi
import asyncio
import queue
from util.log_util import log
from util.config import date, pikpak_enable, pikpak_username, pikpak_pw, proxy_enable, proxy_url, fid_json


class PikPak:
    client = PikPakApi(pikpak_username, pikpak_pw, proxy_enable and proxy_url or None)

    async def downloads(self, datas, fid, typeid=None):
        if not pikpak_enable or len(datas) < 1:
            return
        try:
            await self.client.login()
        except Exception:
            log.error("pikpak 登陆失败")

        for data in datas:
            log.info("pikpak 开启离线下载：{}".format(data["magnet"]))
            parent_path = os.path.join("sehuatang", fid_json.get(fid, "other"))
            if data.get('type_name'):
                parent_path = os.path.join(parent_path, data['type_name'])
            if '[无码破解]' in data['title']:
                parent_path = os.path.join(parent_path, "无码破解")
            # parent_path = None
            try:
                paths = await self.client.path_to_id(parent_path, True)
                path_id = paths[len(paths) - 1]["id"]
                await self.client.offline_download(
                    data["magnet"],
                    path_id,
                )
                log.info("pikpak 保存成功：{}".format(data["magnet"]))
                data['save_pikpak'] = parent_path
            except Exception:
                log.error("pikpak 离线下载失败 :{}".format(data["magnet"]))


if __name__ == "__main__":
    pikpak = PikPak()
    asyncio.run(pikpak.downloads([{
        'magnet': 'magnet:?xt=urn:btih:CBA071E8CCADC4C33263878A599AE000E26AA693'
    }], 36))
