from django.db import models
from django.template.defaultfilters import slugify

class Player(models.Model):
  name = models.CharField(max_length=50)
  class Meta:
    ordering=["id"]
  def __str__(self):
    return self.name

class Map(models.Model):
  name = models.CharField(max_length=50)
  strategy_groups = models.ManyToManyField("StrategyGroup", through="MapStrategyGroup")
  class Meta:
    ordering=["name"]
  def __str__(self):
    return self.name

class Civilization(models.Model):
  name = models.CharField(max_length=50)
  class Meta:
    ordering=["name"]
  def __str__(self):
    return self.name

class PlayerCivilization(models.Model):
  player = models.ForeignKey(Player, on_delete=models.CASCADE)
  civilization = models.ForeignKey(Civilization, on_delete=models.CASCADE)
  weight = models.IntegerField()
  class Meta:
    unique_together = ["player", "civilization"]
    ordering = ["player", "-weight"]
  def __str__(self):
    return self.player.name + " " + self.civilization.name + " " + str(self.weight)

class MapCivilization(models.Model):
  map = models.ForeignKey(Map, on_delete=models.CASCADE)
  civilization = models.ForeignKey(Civilization, on_delete=models.CASCADE)
  weight = models.IntegerField()
  class Meta:
    unique_together = ["map", "civilization"]
    ordering = ["map", "-weight"]
  def __str__(self):
    return self.map.name + " " + self.civilization.name + " " + str(self.weight)

class Strategy(models.Model):
  name = models.CharField(max_length=50)
  description = models.TextField()
  civilizations = models.ManyToManyField(Civilization, through="CivStrategy")
  class Meta:
    verbose_name_plural = "strategies"
    ordering=["name"]
  def __str__(self):
    return self.name

class CivStrategy(models.Model):
  civilization = models.ForeignKey(Civilization, on_delete=models.CASCADE)
  strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
  weight = models.IntegerField()
  class Meta:
    unique_together = ["civilization", "strategy"]
    ordering = ["civilization", "-weight", "strategy"]
    verbose_name_plural = "civ strategies"
  def __str__(self):
    return self.civilization.name + " " + self.strategy.name + " " + str(self.weight)

class StrategyGroup(models.Model):
  team_size = models.IntegerField()
  strategies = models.ManyToManyField(Strategy)
  class Meta:
    ordering=["id"]
  def __str__(self):
    ret_string = ""
    for strategy in self.strategies.all():
      ret_string += strategy.name
      ret_string += " | "
    return ret_string[:-3]

class MapStrategyGroup(models.Model):
  weight = models.IntegerField()
  map = models.ForeignKey(Map, on_delete=models.CASCADE)
  strategy_group = models.ForeignKey(StrategyGroup, on_delete=models.CASCADE)
  class Meta:
    unique_together = ["map", "strategy_group"]
    ordering=["-weight"]
  def __str__(self):
    ret_string = str(self.map) + " " + str(self.strategy_group) + " - " + str(self.weight)
    return ret_string

class Tournament(models.Model):
  name = models.CharField(max_length=50)
  slug_name = models.SlugField(blank=True)
  team_size = models.IntegerField()
  max_map_picks = models.IntegerField()
  maps = models.ManyToManyField(Map)
  class Meta:
    ordering=["id"]
  def __str__(self):
    return self.name
  def save(self, *args, **kwargs):
    self.slug_name = slugify(self.name)
    super(Tournament, self).save(*args, **kwargs)

