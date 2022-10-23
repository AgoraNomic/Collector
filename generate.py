from sys import argv
from csv import reader, writer
from datetime import datetime, timezone

isReport = "-r" in argv

# Determine timestamp
now = datetime.now(timezone.utc)

# Load state of last report
current_stamps = {}

score_file = 'current.csv'
with open(score_file, 'r') as infile:
    current_stamps_f = reader(infile, delimiter=',', quotechar="\"")
    
    for row in current_stamps_f:
        pl_holdings = {}
        sets = list(map(lambda a, b: [a, b], row[1::2], row[2::2]))
        for s in sets:
            if s[0] != '':
                pl_holdings[s[0]] = int(s[1])
        current_stamps[row[0]] = pl_holdings
print(current_stamps)

# Load and process events since last report
recent_file = 'recent_events.csv'
historical = ""
with open(recent_file, 'r') as infile:
    recent_in = reader(infile, delimiter=',', quotechar="\"")
    next(recent_in)
    
    for row in recent_in: 
        event, player, s_type, source, number, reason, date = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
        
        if player not in current_stamps:
            current_stamps[player] = {}
        print(row)
        
        stamp_str = "stamp"
        if int(number) > 1:
            stamp_str+= "s"
        
        if event == "NEW":
            historical+= date + ": " + player + " granted " + number + " " + s_type + " " + stamp_str + " by " + source + " (" + reason + ").\n"
            if s_type not in current_stamps[player]:
                current_stamps[player][s_type] = int(number)
            else:
                current_stamps[player][s_type]+= int(number)
        if event == "TRA":
            historical+= date + ": " + player + " given (transferred) " + number + " " + s_type + " " + stamp_str + " by " + source + " (" + reason + ").\n"
            if s_type not in current_stamps[player]:
                current_stamps[player][s_type] = int(number)
            else:
                current_stamps[player][s_type]+= int(number)
            current_stamps[source][s_type]-= int(number)
            if current_stamps[source][s_type] == 0:
                current_stamps[source].pop(s_type)
        
        # If it's a report, put all of this in the history file now that we're done with it
        if isReport:
            historic_file = 'history.csv'
            with open(historic_file, 'a') as outfile:
                outfile.write(','.join(row)+"\n")

for key in current_stamps:
    print(key + ":")
    for item in current_stamps[key]:
        stamp_str = "stamp"
        if int(current_stamps[key][item]) > 1:
            stamp_str+= "s"
        print("- " + str(current_stamps[key][item]) + " " + item + " " + stamp_str)
    print()

print(historical)


# Sort everything and prepare for outputs
#TODO: Finish the file output, none of it is done
sorted_keys = sorted(current_stamps.keys())

file_output = ""

for key in current_stamps:
    if not current_stamps[key]:
        sorted_keys.pop(key)

if isReport:
    with open(recent_file, 'w') as outfile:
        outfile.write("Name,Change,Reason,Date\n")

# Grab all the player names, then sort them by score
pl_keys = list(players.keys())
pl_keys.sort(key=lambda x:players[x].score, reverse=True) #sort by new score, desc

# define the ordinal numbers
ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

place = 1
ties = -1 # starts at -1 because the first loop will iterate it
previous_score = players[pl_keys[0]].score
out = ""

report_scores = ""
html_scores = ""

def report_formatter(place, pl):
    out = ""
    out+= ordinal(place) + " " * 4
    out+= pl.short_name + " " * 6
    out+= pl.scorestr() + " " * 4
    out+= pl.changestr()
    out+= "\n"
    return(out)

def html_formatter(place, pl):
    out = "<tr>"
    out+= "<td>" + ordinal(place) + "</td>"
    out+= "<td>" + pl.short_name + "</td>"
    out+= "<td>" + pl.scorestr() + "</td>"
    out+= "<td>" + pl.changestr() + "</td>"
    out+= "</tr>"
    return(out)

for player in pl_keys:
    pl = players[player]

    if pl.score == previous_score:
        ties+=1
    else:
        place+=ties+1
        ties=0
    previous_score = pl.score
    report_scores += report_formatter(place, pl)
    html_scores += html_formatter(place, pl)

pl_keys.sort(key=lambda x : players[x].name, reverse=False) #sort by name

# Generate key
key_list = ""
for player in pl_keys:
    key_list+= players[player].name + " = " + players[player].short_name + "; "

key_list = key_list[:-2]

history=""

for i in changes:
    history += i[4] + ": "
    if i[0] == "ADJ":
        if int(i[2]) >= 0:
            history += i[1] + " gains " + i[2] + " (" + i[3] + ")"
        else:
            history += i[1] + " loses " + i[2] + " (" + i[3] + ")"
    elif i[0] == "SET":
        history += i[1] + " score set to " + i[2] + " (" + i[3] + ")"
    elif i[0] == "QRT":
        history += "All players' scores halved for new quarter."
    elif i[0] == "REG":
        history += i[1] + " registers."
    elif i[0] == "DRG":
        history += i[1] + " is deregistered."
    elif i[0] == "WIN":
        history += i[1] + " wins via High Score. Eir score is set to 0. Other scores are halved."
    history+= "\n"

# Apply map and output report
with open('report.template', 'r') as infile:
    template = infile.read()

report_mapping = {'date': now.strftime('%d %b %Y'), 'history': history, 'scores': report_scores, 'key': key_list}

report = template.format_map(report_mapping)

# Apply map and output html
with open('report.html.template', 'r') as infile:
    template = infile.read()

html_mapping = {'date': now.strftime('%d %b %Y'), 'history': history, 'scores': html_scores, 'key': key_list}

html = template.format_map(html_mapping)

if not isReport:
    print(report)
    print(html)
else:
    report_name = now.strftime('%Y-%m-%d')

    with open(score_file, 'w') as outfile:
        outfile.write("Name,Short,Score\n")
        for player in pl_keys:
            outfile.write(players[player].name+","+players[player].short_name+","+str(players[player].score)+"\n")

    with open("report.html", "w") as ofile:
        ofile.write(html)

    with open('reports/' + report_name + '.txt', 'w') as ofile:
        ofile.write(report)

    with open('report.txt', 'w') as ofile:
        ofile.write(report)
