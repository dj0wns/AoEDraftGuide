from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.template.defaultfilters import slugify
from aoe.models import Tournament, Civilization, Player, Map, CivStrategy, PlayerCivilization, MapCivilization

# Create your views here.
def index(request, tourny_name=None):
  player = list(map(int, request.GET.get('player', "-1").split(",")))
  maps = list(map(int, request.GET.get('maps', "-1").split(",")))
  lower_limit = int(request.GET.get('lower_limit', "0").split(",")[0])
  tournaments = Tournament.objects.all()
  players = Player.objects.all()
  selected_tournament = Tournament.objects.filter(slug_name=tourny_name).first()
  if selected_tournament:
    tourny_maps = selected_tournament.maps.all()
    max_map_picks = selected_tournament.max_map_picks
    team_size = selected_tournament.team_size
  else:
    tourny_maps = None
    maps = None
    max_map_picks = 0
    team_size = 0
  civ_ratings = GetCivRatings(selected_tournament, player, maps, lower_limit)
  map_strategies = GetMapStrategies(maps, lower_limit, max_map_picks)
  template = loader.get_template('aoe/index.html')
  context = {   "tournaments" : tournaments,
                "selected_tournament" : selected_tournament,
                "team_size" : range(team_size),
                "players" : players,
                "tourny_maps" : tourny_maps,
                "max_map_picks" : range(max_map_picks),
                "player_list" : player,
                "map_list" : maps,
                "map_strategies" : map_strategies,
                "civ_ratings" : civ_ratings,
                "lower_limit" : lower_limit,
                "lower_limit_range" : range(0,11),
  }
  return HttpResponse(template.render(context, request))

def GetMapStrategies(maps, lower_limit, max_map_picks):
  if maps is None:
    return {}
  map_strategies = [""] * (max_map_picks + 1)
  index = 0
  for map in maps:
    if not map:
      continue
    map_object = Map.objects.filter(id=map).first()
    if not map_object:
      continue
    for map_strategy_group in map_object.mapstrategygroup_set.all():
      if map_strategy_group.weight < lower_limit / 2.:
        #map weightings are only half the total weighting so if its less than half the lower limit skip it
        continue
      strategy_names = ""
      for strategy in map_strategy_group.strategy_group.strategies.all():
        if strategy_names:
          strategy_names += ", "
        strategy_names += strategy.name
      if map_strategies[index]:
        map_strategies[index].append((map_strategy_group.weight, strategy_names))
      else:
        map_strategies[index] = [(map_strategy_group.weight, strategy_names)]
    index += 1
    #sort each map by weight descending
    map_strategies[index] = sorted(map_strategies[index], key=lambda item: -item[0])
  return map_strategies

def GetCivRatings(tournament, player, maps, lower_limit):
  if tournament is None or maps is None:
    return {}
  civ_ratings = {}
  #get the largest per map weight for each civ
  for map in maps:
    civ_map_ratings = {}
    max_weight = -1 #to normalize all weightings to 10 for the map
    if not map:
      continue
    map_object = Map.objects.filter(id=map).first()
    if not map_object:
      continue
    for map_strategy_group in map_object.mapstrategygroup_set.all():
      if map_strategy_group.weight < lower_limit / 2.:
        #map weightings are only half the total weighting so if its less than half the lower limit skip it
        continue
      for strategy in map_strategy_group.strategy_group.strategies.all():
        for civ in strategy.civilizations.all():
          map_weight = MapCivilization.objects.filter(civilization=civ.id, map=map_object.id).first()
          if map_weight is None:
            #if there is no civ specifiv weight fall back to the strategy weighting
            weight = CivStrategy.objects.filter(civilization=civ.id, strategy=strategy.id).first().weight + map_strategy_group.weight
          else:
            #give max weight + rating/5 and then later normalize all the data
            weight = 10 + map_weight.weight / 5.
          if weight > max_weight:
            max_weight = weight
          if weight < lower_limit:
            #dont add ratings below the limit
            continue
          if civ.name in civ_map_ratings:
            if weight > civ_map_ratings[civ.name][0]:
              civ_map_ratings[civ.name] = (weight, map_object.name, strategy.name) 
          else:
            civ_map_ratings[civ.name] = (weight, map_object.name, strategy.name)
    #normaliz civ ratings to 10
    normalize_factor = (10./max_weight)
    for k, v in civ_map_ratings.items():
      civ_map_ratings[k] = (v[0] * normalize_factor, v[1], v[2])
    # make sure each civ has a rating to keep the board nice
    for civ in Civilization.objects.all():
      if civ.name not in civ_map_ratings:
        civ_map_ratings[civ.name] = (0, "", "")
    #now sum the map and pool ratings
    for k, v in civ_map_ratings.items():
      if k in civ_ratings.keys():
        # ugly structure but need to keep track of all historical weights so we can keep reasonings alive
        civ_ratings[k] = (v[0] + civ_ratings[k][0], civ_ratings[k][1] + [(v[0], v[1], v[2])] )
      else:
        civ_ratings[k] = (v[0], [(v[0], v[1], v[2]),])
  #now multiply by players ability
  player_civ_ratings = {}
  for p in player:
    if not p:
      continue
    for player_civ_object in PlayerCivilization.objects.filter(player=p).all():
      #get the best weight out of every player for each civ
      if player_civ_object.civilization.name in player_civ_ratings:
        if player_civ_object.weight > player_civ_ratings[player_civ_object.civilization.name]:
          player_civ_ratings[player_civ_object.civilization.name] = player_civ_object.weight
      else:
        player_civ_ratings[player_civ_object.civilization.name] = player_civ_object.weight

  #now sum the player and pool ratings
  for k,v in player_civ_ratings.items():
    if k in civ_ratings:
      civ_ratings[k] = (v * civ_ratings[k][0], civ_ratings[k][1])
    else:
      civ_ratings[k] = (v, [("", "", "")])

  return dict(sorted(civ_ratings.items(), key=lambda item: -item[1][0]))

def submit(request):
  if request.method =='POST':
    data = request.POST
    if "tournament" in data:
      tournament = data['tournament']
    else:
      redirect('/aoe')
    redir = '/aoe/{tourny}'.format(tourny=tournament)
    query_count = 0
    for k, v in data.lists():
      if k == "tournament" or k == "csrfmiddlewaretoken":
        continue
      if query_count:
        redir += "&"
      else:
        redir += "?"
      redir +=  k + "="
      for value in v:
        redir += str(value)
        redir += ','
      redir = redir[:-1]
      query_count += 1
  return redirect(redir)
