# Result Predictor
## Environment
`python -m venv venv`

`venv\Scripts\activate `

`pip install -r requirements.txt`
##    Steps

### Fetch data from understat
separate into match data and current standings

### process data
 - loop through all leagues and seasons
 - for every single game, find the teams xG and xGA performance in prior n-amount of games.
 - Log the results of said game

 - graph results
 - produce a model that estimates result odds based on last n games

### predict future games
use results to guess odds of upcoming games

### simulate rest of season

