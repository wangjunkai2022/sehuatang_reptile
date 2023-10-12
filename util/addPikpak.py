import os

from pikpakapi import PikPakApi
import asyncio
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

        parent_paths = {}
        for index in range(len(datas) - 1, -1, -1):
            data = datas[index]
        # for data in datas[:]:
            try:
                parent_path = os.path.join("sehuatang", fid_json.get(fid, "other"))
                if data.get('type_name'):
                    parent_path = os.path.join(parent_path, data['type_name'])
                if '[无码破解]' in data['title']:
                    parent_path = os.path.join(parent_path, "无码破解")
                path_id = parent_paths.get(parent_path, None)
                if path_id:
                    pass
                else:
                    paths = await asyncio.wait_for(self.client.path_to_id(parent_path, True), timeout=10000)
                    path_id = paths[len(paths) - 1].get("id", None)
                    parent_paths[parent_path] = path_id

                log.info("pikpak 开启离线下载：{}".format(data["magnet"], ))
                task = self.client.offline_download(
                    data["magnet"],
                    path_id,
                )
                await asyncio.wait_for(task, timeout=10000)

                log.info("pikpak 保存成功：{} 保存路径：{}".format(data["title"], parent_path))
                data['save_pikpak'] = parent_path
            except Exception as e:
                log.error("pikpak 离线下载失败 error:{}\ndata:{}".format(e, data))
                # datas.remove(data)
                datas.pop(index)
                await asyncio.sleep(60)


if __name__ == "__main__":
    pikpak = PikPak()
    asyncio.run(pikpak.downloads([{
        'magnet': 'magnet:?xt=urn:btih:CBA071E8CCADC4C33263878A599AE000E26AA693'
    }], 36))
