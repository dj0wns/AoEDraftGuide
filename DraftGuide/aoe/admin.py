from django.contrib import admin
import aoe.models

# Register your models here.

admin.site.register(aoe.models.Player)
admin.site.register(aoe.models.Map)
admin.site.register(aoe.models.Civilization)
admin.site.register(aoe.models.PlayerCivilization)
admin.site.register(aoe.models.MapCivilization)
admin.site.register(aoe.models.Strategy)
admin.site.register(aoe.models.CivStrategy)
admin.site.register(aoe.models.StrategyGroup)
admin.site.register(aoe.models.MapStrategyGroup)
admin.site.register(aoe.models.Tournament)
