from django.contrib import admin

# Register your models here.


# モデルをインポート
from . models import CityData, UserInput

# 管理ツールに登録
admin.site.register(CityData)
admin.site.register(UserInput)