[app]
title = Eldritch Portals
package.name = eldritchportals
package.domain = org.rpg

icon.filename = %(source.dir)s/icon.png

source.dir = .
source.include_exts = py,png,jpg,jpeg,webp,kv,atlas,ttf,otf,json
source.include_patterns = weapons.json

version = 0.4.5

requirements = python3,kivy==2.3.0,pillow,android,pyjnius,pychromecast,zeroconf,ifaddr,protobuf,cython<3.0

android.api = 34
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.enable_androidx = True

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,CHANGE_WIFI_MULTICAST_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES,READ_MEDIA_AUDIO,READ_MEDIA_VIDEO

orientation = portrait
fullscreen = 1

android.accept_sdk_license = True
android.private_storage = True

p4a.bootstrap = sdl2
p4a.branch = v2024.01.21

log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
