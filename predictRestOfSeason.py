import json
import random as rd
from re import match
from runMe import leagues, calcWinOdds,getLastGamesXGs
import copy
from plotRestOfSeasonSimulations import graphResultsOfSimulation

def predictRestOfSeason(league, season):
    with open(f'data/{league}/{season}.json', 'r') as f:
        games = json.load(f)
        #order results by date
        games = sorted(games['dates'], key=lambda x: x['datetime'])
        #only keep results where isResult is true
        results = [i for i in games if i['isResult'] == True][::-1]     
        remainingGames = [i for i in games if i['isResult'] == False]

    with open(f'settings.json', 'r') as f:
        settings = json.load(f)
    
    homeM = settings['xGFormulaVariablesHome']['m']
    homeB = settings['xGFormulaVariablesHome']['b']
    awayM = settings['xGFormulaVariablesAway']['m']
    awayB = settings['xGFormulaVariablesAway']['b']

    teams = settings['teams'][league]

    #get last 5 games xG for each team
    for team in teams:
        #print(f"Calculating last 5 games xG for {team['title']}")
        team['lastXGs'] = getLastGamesXGs(team['id'], 5, results)
        
        team['lastXGs'] = team['lastXGs'][0] - team['lastXGs'][1]
        
        team['pts'] = 0



    #predict remaining games
    for match in remainingGames:
        homeTeam = next(t for t in teams if t['id'] == match['h']['id'])
        awayTeam = next(t for t in teams if t['id'] == match['a']['id'])
        homeOdds = calcWinOdds(homeTeam['lastXGs']-awayTeam['lastXGs'], homeM,homeB)
        awayOdds = calcWinOdds(awayTeam['lastXGs']-homeTeam['lastXGs'], awayM,awayB)
        drawOdds = 1 - homeOdds - awayOdds
        #print(f"Predicting match: {homeTeam['title']} vs {awayTeam['title']} on {match['datetime']}")
        #print(f"Predicted odds: {homeTeam['title']} win: {homeOdds:.2f}, Draw: {drawOdds:.2f}, {awayTeam['title']} win: {awayOdds:.2f}")
        match['homeOdds'] = homeOdds
        match['awayOdds'] = awayOdds
        match['drawOdds'] = drawOdds

    #save remaining games with predictions
    with open(f'data/{league}/predictedRemainingGames.json', 'w') as f:
        f.write(json.dumps(remainingGames))

    #generate league table
    for match in results:
        homeTeam = next(t for t in teams if t['id'] == match['h']['id'])
        awayTeam = next(t for t in teams if t['id'] == match['a']['id'])
        if match['goals']['h'] > match['goals']['a']:
            homeTeam['pts'] += 3
        elif match['goals']['h'] < match['goals']['a']:
            awayTeam['pts'] += 3
        else:
            homeTeam['pts'] += 1
            awayTeam['pts'] += 1
    
    
    #sort and save league table
    teams = sorted(teams, key=lambda x: x['pts'], reverse=True)

    #save league table
    with open(f'data/{league}/leagueTable.json', 'w') as f:
        f.write(json.dumps(teams))

def simulateRestOfSeason(remainingGames, teams):

    for match in remainingGames:
        homeOdds = match['homeOdds']
        awayOdds = match['awayOdds']
        drawOdds = match['drawOdds']
        #find home and away team
        homeTeam = next(t for t in teams if t['id'] == match['h']['id'])
        awayTeam = next(t for t in teams if t['id'] == match['a']['id'])
    
        outcome = rd.choices(['home', 'draw', 'away'], weights=[homeOdds, drawOdds, awayOdds])[0]
        
        if outcome == 'home':
            homeTeam['pts'] += 3
        elif outcome == 'away':
            awayTeam['pts'] += 3
        else:
            homeTeam['pts'] += 1
            awayTeam['pts'] += 1

    
    #return teams ordered by points
    teams = sorted(teams, key=lambda x: x['pts'], reverse=True)

    return teams

if __name__ == "__main__":
    season = '2025'  
    for league in leagues:
            print(f"Predicting rest of season for {league} {season}")
            predictRestOfSeason(league, season)
    
            with open(f'data/{league}/predictedRemainingGames.json', 'r') as f:
                remainingGames = json.load(f)

            #get league table
            with open(f'data/{league}/leagueTable.json', 'r') as f:
                teams = json.load(f)
            numberOfSimulations = 1000000
            teamPositionsAtEndOfSeason = {t['short_title']: {} for t in teams}
            for t in teams:
                teamPositionsAtEndOfSeason[t['short_title']] = {i: 0 for i in range(1, len(teams)+1)}
            
            for i in range(numberOfSimulations):
                res = simulateRestOfSeason(remainingGames, copy.deepcopy(teams))
            
                for index, team in enumerate(res, start=1):
                    #print(f"Simulation {i+1}: {team['title']} finished in position {index} with {team['pts']} points")
                    teamPositionsAtEndOfSeason[team['short_title']][index] += 1


            
            #save teamPositionsAtEndOfSeason
            with open(f'data/{league}/teamPositionsAtEndOfSeason.json', 'w') as f:
                f.write(json.dumps(teamPositionsAtEndOfSeason))

            graphResultsOfSimulation(league,numberOfSimulations)