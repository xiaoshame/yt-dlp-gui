## 背景

- 老婆经常需要下载B站和好看视频的内容，日常都是我帮助下载。马上就是老婆的生日，就像下个下载器送给老婆作为生日礼物

## 项目简介

- 整体基于开源项目[youtube-dl-gui](https://github.com/MrS0m30n3/youtube-dl-gui)
  - 从python2调整为python3，修复相关bug
  - 下载器从youtube-dl调整为yt-dlp
  - 支持B站和youtube视频下载，youtube视频下载需要设置代理
  - yt-dlp如果想用新版本，可以自行在[yt-dlp](https://github.com/yt-dlp/yt-dlp/releases)下载，然后覆盖/data/exe中的yt-dlp.exe即可
- 新增好看视频下载，基于开源项目[crawler](https://github.com/litaolemo/crawler)中好看视频信息获取代码
  - 网络请求从requests 调整为urllib.request，规避打包成exe后运行报openssl相关错误
  - 最初通过使用官方_ssl.pyd替换conda中的_ssl.pyd文件可以解决openssl报错，但是导致B站视频下载失败，最终更换网络请求库解决
- 增加打包相关信息，直接下载dist目录中__main__文件夹即可使用

## todo

- 只测试了主要流程，部分参数设置功能未测试，待完善
