import matplotlib.pyplot as plt
import json

import numpy as np

def updateXGFormulaVariables(m,b,hm,hb,am,ab):
    with(open('settings.json','r') as f):
        settings = json.load(f)
    
    settings['xGFormulaVariables']['m'] = m
    settings['xGFormulaVariables']['b'] = b
    settings['xGFormulaVariablesHome']['m'] = hm
    settings['xGFormulaVariablesHome']['b'] = hb
    settings['xGFormulaVariablesAway']['m'] = am
    settings['xGFormulaVariablesAway']['b'] = ab
    with(open('settings.json','w') as f):
        f.write(json.dumps(settings))



def plotGraphs(numberOfGamesInSet):
    
    
    with open('data/xgDiffWinRates.json','r') as f:
        games = json.load(f)

    with open('data/homeXgDiffWinRates.json','r') as f:
        homeGames = json.load(f)
    with open('data/awayXgDiffWinRates.json','r') as f:
        awayGames = json.load(f)

    #add homeGames and awayGames data to plot with different colors
    home_xg_differences = [game[0] for game in homeGames]
    home_results = [game[1] for game in homeGames]
    away_xg_differences = [game[0] for game in awayGames]
    away_results = [game[1] for game in awayGames]

    xg_differences = [game[0] for game in games]
    results = [game[1] for game in games]
    
    plt.scatter(home_xg_differences, home_results, color='red', label='Home Games')
    plt.scatter(away_xg_differences, away_results, color='blue', label='Away Games')

    #plt.scatter(xg_differences, results, color='black', label='All Games', alpha=0.5)
    #make y scale go from 0 to 1
    plt.ylim(0,1)

    #add trendline
    z = np.polyfit(xg_differences, results, 1)      
    p = np.poly1d(z)
    #plt.plot(xg_differences,p(xg_differences),"r--")

    z2 = np.polyfit(home_xg_differences, home_results, 1)      
    p2 = np.poly1d(z2)
    plt.plot(home_xg_differences,p2(home_xg_differences),"r-")

    z3 = np.polyfit(away_xg_differences, away_results, 1)
    p3 = np.poly1d(z3)
    plt.plot(away_xg_differences,p3(away_xg_differences),"b-")

    updateXGFormulaVariables(z[0],z[1],z2[0],z2[1],z3[0],z3[1])

    #add confidence intervals to the graph
    #calculate standard error of the estimate
    y_pred = p(xg_differences)
    residuals = np.array(results) - y_pred

    se = np.sqrt(np.sum(residuals**2) / (len(results) - 2))

    #calculate confidence intervals
    ci = 1.96 * se
    #plt.fill_between(xg_differences, p(xg_differences) - ci
    #                    , p(xg_differences) + ci, color='r', alpha=0.2)
    
    #add trendline equation to graph
    #plt.text(min(xg_differences), max(results), f'y={z[0]:.6f}x+{z[1]:.6f}', fontsize=12)
    plt.text(-2.0, 0.95, f'Home: y={z2[0]:.6f}x+{z2[1]:.6f}', fontsize=12, color='red')
    plt.text(-2.0, 0.90, f'Away: y={z3[0]:.6f}x+{z3[1]:.6f}', fontsize=12, color='blue')

    

    # Generate x values
    x = np.linspace(-4.5, 4.5, 200)

    # Best fit function according to chatGPT:------------------------
    def f(x):
        return 0.05 + (0.70 / (1 + np.exp(-.76 * (x-0.03))))
    y = f(x)

    # Plot
    #plt.scatter(x, y)
    #----------------------------------------------------------------

    plt.xlabel('xG Difference')
    plt.ylabel('Win Rate')
    plt.title('xG Difference vs Win Rate: ' + str(numberOfGamesInSet) + ' Games')
    #add in bottom right corner the total number of games included in the analysis
    #plt.text(0.95, -0.10, f'Total Games: {numberOfGamesInSet}', fontsize=10, ha='right', va='bottom', transform=plt.gca().transAxes)
    plt.legend()

    #plot y≈0.05+1+e−1.8x0.70​ 



    # add under that the source of the data: understat.com
    plt.text(0.95, -0.10, 'Graph by: Benni Valur | Data Source: understat.com', fontsize=8, ha='right', va='bottom', transform=plt.gca().transAxes)
    plt.show()