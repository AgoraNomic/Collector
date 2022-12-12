from sys import argv
from csv import reader
from datetime import datetime, timezone

isReport = "-r" in argv

# Determine timestamp
now = datetime.now(timezone.utc)

stamp_counts = {}

def countStamps(stype, snum):
    if stype in stamp_counts:
        stamp_counts[stype]+= snum
    else:
        stamp_counts[stype] = snum

players = {}

class Player:
    def __init__(self):
        self.stamp_balances = {}
        
    def modifyBalance(self, stype, snum):
        if stype in self.stamp_balances:
            self.stamp_balances[stype]+= snum
        else:
            self.stamp_balances[stype] = snum
            
        if self.stamp_balances[stype] == 0:
            self.stamp_balances.pop(stype)
            
    def totalStamps(self):
        return sum(self.stamp_balances.values())

# Load and process existing state
score_file = 'current.csv'
with open(score_file, 'r') as infile:
    current_stamps_f = reader(infile, delimiter=',', quotechar="\"")
    
    for row in current_stamps_f:
        players[row[0]] = Player()
        sets = list(map(lambda a, b: [a, int(b)], row[1::2], row[2::2]))

        for s in sets:
            players[row[0]].modifyBalance(s[0],s[1])
            countStamps(s[0], s[1])

# Load and process new events
recent_file = 'recent_events.csv'
historical = ""
with open(recent_file, 'r') as infile:
    recent_in = reader(infile, delimiter=',', quotechar="\"")
    next(recent_in)
    
    for row in recent_in: 
        event, player, s_type, source, number, reason, date = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
        
        if number != "":
            number = int(number)
        
        if player not in players:
            players[player] = Player()
        
        pl = players[player]
        
        if event == "NEW":
            historical+= f"{date}: {player} granted {number} {s_type} stamp{'s' if number != 1 else ''} by {source} ({reason}).\n"
            pl.modifyBalance(player, number)
            countStamps(s_type, number)
        
        elif event == "DREAM":
            number = max(0, 2 - (stamp_counts[player] // 8))
            historical+= f"{date}: {player} granted {number} {player} stamp{'s' if number != 1 else ''} via Wealth Dream.\n"
            pl.modifyBalance(player, number)
            countStamps(player, number)
        
        elif event == "TRA":
            historical+= f"{date}: {player} given (transferred) {number} {s_type} stamp{'s' if number != 1 else ''} by {source} ({reason }).\n"
            players[source].modifyBalance(s_type, 0-number)
            pl.modifyBalance(player, number)
            if players[source].totalStamps() == 0:
                players.pop(source)
            
        elif event == "DEL": # expects a negative number
            historical+= f"{date}: {player} destroyed {number} {s_type} stamp{'s' if number != 1 else ''} in eir possession ({reason}).\n"
            countStamps(s_type, number)
            pl.modifyBalance(player, number)
            if players[player].totalStamps() == 0:
                players.pop(player)
            
        elif event == "DRG":
            historical+= f"{date}: {player} deregistered.\n"
            for key in players[player].stamp_balances.keys():
                players["L&FD"].modifyBalance(key, players[player].stamp_balances[key])
            players.pop(player)
        
        # If it's a report, put all of this in the history file now that we're done with it
        if isReport:
            historic_file = 'history.csv'
            with open(historic_file, 'a') as outfile:
                outfile.write(','.join(row)+"\n")
                
# get ready to format current output
current_holdings_str = ""
current_holdings_csv = ""

# sort owners
owners = sorted(players.keys(), key = lambda s: s.lower())
if 'L&FD' in owners:
    owners.remove('L&FD')
    owners = ['L&FD'] + owners

for owner in owners:
    line = f"{owner} ({players[owner].totalStamps()}):\n"
    current_holdings_csv+= owner + ","

    # sort stamps
    stamp_types = sorted(players[owner].stamp_balances.keys(), key = lambda s: s.lower())

    for stamp_type in stamp_types:
        stamp_count = players[owner].stamp_balances[stamp_type]
        line += f"- {stamp_count} {stamp_type} stamp{'s'if stamp_count != 1 else ''}\n"
        current_holdings_csv+= f"{stamp_type},{stamp_count},"
    current_holdings_csv = current_holdings_csv[:-1] + "\n"
    current_holdings_str += line + "\n"

current_holdings_str = current_holdings_str[:-2]

# Apply map and output report
with open('report.template', 'r') as infile:
    template = infile.read()

stamp_totals_string = ""
for key in sorted(stamp_counts.keys(), key=lambda x: x.lower()):
    stamp_totals_string+= f"{key}: {stamp_counts[key]}\n"

report_mapping = {'date': now.strftime('%d %b %Y'), 'stamps': current_holdings_str, 'historical': historical, 'totals': stamp_totals_string}

report = template.format_map(report_mapping)

if not isReport:
    print(report)
else:
    report_name = now.strftime('%Y-%m-%d')

    # Write the report to the report.txt and its own file
    with open('reports/' + report_name + '.txt', 'w') as ofile:
        ofile.write(report)

    with open('report.txt', 'w') as ofile:
        ofile.write(report)

    # Updates current.csv
    with open('current.csv', 'w') as ofile:
        ofile.write(current_holdings_csv)

    # Update history.csv
    with open ('history.csv', 'a') as ofile:
        ofile.write(historical)
        
    # Empty recent_events.csv
    with open('recent_events.csv', 'w') as ofile:
        ofile.write("EVENT,PLAYER,TYPE,SOURCE,NUMBER,REASON,DATE")
