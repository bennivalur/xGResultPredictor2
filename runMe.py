import json
import urllib.request
from datetime import date,datetime, timedelta
from understatapi import UnderstatClient
from plotData import plotGraphs


leagues = ['EPL','La_Liga','Bundesliga','Serie_A','Ligue_1']#,'RFPL']
#leagues = ['EPL']
#seasons = ['2024']
gamesBackToCheck = 5
#WHen win rate per xg difference is calculated, 
# only include differences that have at least this many games to avoid skewing the data with small sample sizes
minimumGamesToInclude = 200
seasons = ['2014','2015','2016','2017','2018','2019','2020','2021','2022','2023','2024','2025']
xGExtraDigits = 1

def getUnderstatResults(league,year):
    print("Getting Understat results for",league,year)
    with UnderstatClient() as understat:
        data = understat.league(league=league).get_match_data(season=year)
        games = {"dates":data}
        with open('data/'+ league +'/' + year+'.json','w') as f:
            f.write(json.dumps(games))

def getLastGamesXGs(team:any,nGames:int,results,date=None):
    games = [g for g in results if g['h']['id'] == team or g['a']['id'] == team][:nGames]
    
    if(len(games) < nGames):
        return 'not enough games'
    
    xG = 0
    xGA = 0
    for g in games:
        if(g['h']['id'] == team):
            #print(g['xG']['h'])
            xG += float(g['xG']['h'])
            xGA += float(g['xG']['a'])
        if(g['a']['id'] == team):
            xG += float(g['xG']['a'])
            xGA += float(g['xG']['h'])
    return [xG/len(games),xGA/len(games)]

def calcWinOdds(xGSum,m,b):
    odds = (xGSum  * m) + b
    if odds <= 0:
        return 0
    return round(odds,2)

def getData(leagues,seasons):
    #Get Understat data for all leagues and seasons
    print("Getting data for leagues:",leagues,"and seasons:",seasons)
    for league in leagues:
        for season in seasons:
            getUnderstatResults(league,season)

def processPastGames():
    processedGames = []
    for league in leagues:  
        for season in seasons:
            with open('data/'+ league +'/' + season+'.json','r') as f:
                data = json.loads(f.read())
                results = [g for g in data['dates'] if g['isResult'] == True]
                #sort results by date
                results = sorted(results, key=lambda x: datetime.strptime(x['datetime'], '%Y-%m-%d %H:%M:%S'))
                for index,g in enumerate(results):
                    homeTeam = g['h']
                    awayTeam = g['a']
                    
    
                    #filter results so we only get games with earlier dates than the current game, 
                    # so we only get games that happened before the current game
                    priorResults = results[:index]

                    xGHome = getLastGamesXGs(homeTeam['id'],gamesBackToCheck,priorResults)
                    xGAway = getLastGamesXGs(awayTeam['id'],gamesBackToCheck,priorResults)
                    if(xGHome != 'not enough games' and xGAway != 'not enough games'):
                        HxGDiff = round((xGHome[0] - xGHome[1]) - (xGAway[0] - xGAway[1]), xGExtraDigits)
                        AxGDiff = round((xGAway[0] - xGAway[1]) - (xGHome[0] - xGHome[1]), xGExtraDigits)
                        #odds = calcWinOdds(xGDiff)
                        print(league,season,g['id'],homeTeam['title'],awayTeam['title'],HxGDiff,AxGDiff,g['goals']['h'],g['goals']['a'])
                        if g['goals']['h'] > g['goals']['a']:
                            result = 'home win'
                        elif g['goals']['h'] < g['goals']['a']:
                            result = 'away win'
                        else:
                            result = 'draw'
                        processedGames.append({
                            'league': league,
                            'season': season,
                            'gameId': g['id'],
                            'homeTeam': homeTeam['title'],
                            'awayTeam': awayTeam['title'],
                            'homeXGDiff': HxGDiff,
                            'awayXGDiff': AxGDiff,
                            'homeGoals': g['goals']['h'],
                            'awayGoals': g['goals']['a'],
                            'result': result
                        })
    with open('data/processedGames.json','w') as f:
        f.write(json.dumps(processedGames))

def analyzeData():
    with open('data/processedGames.json','r') as f:
        data = json.load(f)

        entries = []
        homeEntries = []
        awayEntries = []

        for g in data:
            homeXG = next((e for e in entries if e[0] == g['homeXGDiff']), None)
            awayXG = next((e for e in entries if e[0] == g['awayXGDiff']), None)

            if not homeXG:
                homeXG = [g['homeXGDiff'],[]]
                entries.append(homeXG)
                homeEntries.append(homeXG)
            if not awayXG:
                awayXG = [g['awayXGDiff'],[]]
                entries.append(awayXG)
                awayEntries.append(awayXG)
            
            if homeXG:
                if g['result'] == 'home win':
                    homeXG[1].append(1)
                else:
                    homeXG[1].append(0)
            
            if awayXG:
                if g['result'] == 'away win':
                    awayXG[1].append(1)
                else:
                    awayXG[1].append(0)
            
        #sort entries by xg difference
        entries = sorted(entries, key=lambda x: x[0])
        entries = [[e[0],e[1],len(e[1])] for e in entries if len(e[1]) >= minimumGamesToInclude]
        homeEntries = sorted(homeEntries, key=lambda x: x[0])
        homeEntries = [[e[0],e[1],len(e[1])] for e in homeEntries if len(e[1]) >= minimumGamesToInclude/2]
        awayEntries = sorted(awayEntries, key=lambda x: x[0])   
        awayEntries = [[e[0],e[1],len(e[1])] for e in awayEntries if len(e[1]) >= minimumGamesToInclude/2]

        for e in entries:
            winRate = sum(e[1])/len(e[1]) if len(e[1]) > 0 else 0
            games = len(e[1])
            e[1] = winRate
            e[2] = games
            #print("xG Diff:",e[0],"Win Rate:",round(winRate,2),"Games:",games)

        for e in homeEntries:
            winRate = sum(e[1])/len(e[1]) if len(e[1]) > 0 else 0
            games = len(e[1])
            e[1] = winRate
            e[2] = games
            #print("Home xG Diff:",e[0],"Win Rate:",round(winRate,2),"Games:",games)
        for e in awayEntries:
            winRate = sum(e[1])/len(e[1]) if len(e[1]) > 0 else 0
            games = len(e[1])   
            e[1] = winRate
            e[2] = games
            #print("Away xG Diff:",e[0],"Win Rate:",round(winRate,2),"Games:",games)
        
        totalGames = sum(e[2] for e in entries)
        print("Total games included in analysis:",totalGames)
        
    with open('data/xgDiffWinRates.json','w') as f:
        f.write(json.dumps(entries))

    with open('data/homeXgDiffWinRates.json','w') as f:
        f.write(json.dumps(homeEntries))

    with open('data/awayXgDiffWinRates.json','w') as f:
        f.write(json.dumps(awayEntries))
    return totalGames


def main():
    with open('settings.json','r') as f:
        settings = json.load(f)
    #Get data for all leagues and seasons
    today = date.today().strftime("%d/%m/%Y")
    if settings['understatLastFetch'] != today:
        getData(leagues=leagues,seasons=seasons)
        settings['understatLastFetch'] = today
        with open('settings.json','w') as f:
            f.write(json.dumps(settings))

    #For all leagues and games, 
    # calculate xg difference for the last n games for each team, 
    # log the difference and the result of the game
    processPastGames()

    #loop through the processed games and log the win rate for home wins, away wins and draws for different xg difference ranges
    numberOfGamesInSet = analyzeData()
    plotGraphs(numberOfGamesInSet)
        

    

            
if __name__ == "__main__":
    main()