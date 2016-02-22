This uses [you-get](https://you-get.org/).

I [originally wrote this in PowerShell](https://github.com/VertigoRay/Download-EcuaVisa/blob/7123b6c918a6e44d28c6709f3a79d23d73c68d2c/Download-EcuaVisa.ps1), but opted to re-write it in Python and put it on my [Plex](http://plex.tv) server to auto-download the latest episodes and put them where [Plex](http://plex.tv) will find them, keeping only the latest episodes since it's just the news.

Cheers!! :beers:

# Usage

Currently running on Debian 8 (Jessie) with Python 3.4.2 (default, Oct  8 2014, 10:45:20).

This is the `crontab` entry on the `plex` user account; which is the account that my Plex server services run as.

```crontab
0 * * * * $(which python3) /mnt/plex/EcuaVista-Downloader/ecuavista-downloader.py
```
